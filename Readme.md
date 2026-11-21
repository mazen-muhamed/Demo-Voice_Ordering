# Demo for AI Voice Ordering System

Egyptian-dialect voice ordering demo:
**FreeSWITCH (media gateway) → Pipecat pipeline (VAD → STT → Router → Matcher →
Session → TTS) → live order state on a monitor WS.**

- **LLM**: none in the demo pipeline (rules + e5-small only; LLM deferred)
- **TTS**: `edge-tts` (`ar-EG-SalmaNeural`) → 8 kHz PCM16; `TTS_BACKEND=fake` gives a beep
- **VAD**: Silero, ~0.6 s endpoint silence, barge-in enabled
- **STT**: Groq `whisper-large-v3` free tier with local `faster-whisper` fallback
  (swap point: `FakeSTT` — both behind the same signature)
- **Telephony**: FreeSWITCH 1.10.12 + `mod_audio_stream` (community edition)

## The parts (and how they connect)

```
Zoiper/MicroSIP  ──SIP/RTP──►  FreeSWITCH (Docker, host network)
                                   │  mod_audio_stream (L16 8 kHz)
                                   ▼
voice_agent/       FastAPI WS :8765 — ws://…/ws?call_uuid=<uuid>  (Pipecat)
   │   VAD → STT → IntentRouter (rules) → Matcher (e5 + NumPy + RapidFuzz, menu.sql)
   │                                        │ POST /api/v1/sessions/{sid}/items
   ▼                                        ▼
voice_ordering/    FastAPI :8001 — session FSM, confirmation gate, DTMF floor
   │
   └── WS /ws/live — every state change broadcast (monitor page subscribes here)

listener.py        ESL bridge :8021 — CHANNEL_ANSWER / DTMF / mod_audio_stream::play
menu.sql + menu_matcher.py   ONE menu: Postgres (aliases TEXT[], variants JSONB)
run_12_turns.py              offline replay of the 12-turn script + asserts (470 EGP)
```

## Run with Docker (recommended)

Prerequisites: Docker + Compose, a softphone (Zoiper or MicroSIP), and a free
LAN IP on the demo machine.

```bash
cp .env.example .env          # fill GROQ_API_KEY if STT_BACKEND=groq
docker compose build          # first FreeSWITCH build: ~25–40 min, then cached
docker compose up -d
docker compose ps
```

Host ports (FreeSWITCH and the listener use `network_mode: host`):

| Port | Purpose |
|---|---|
| 5060/udp + tcp | SIP signalling |
| 16384–16484/udp | RTP (must match `switch.conf.xml`) |
| 8021/tcp | ESL, bound to 127.0.0.1 |
| 8001/tcp | session service + `/ws/live` |
| 8765/tcp | Pipecat audio websocket |
| 5433/tcp | Postgres (host port; override with `POSTGRES_HOST_PORT`) |

### Softphone setup

- Username `1000`, password `1234`
- Domain / SIP server: the host's LAN IP, e.g. `192.168.1.10`
- Dial **5000** for the voice-ordering demo, **9196** for an echo test

### What happens on a call

1. FreeSWITCH answers; `listener.py` creates a session keyed by the call UUID
   and starts `uuid_audio_stream … ws://127.0.0.1:8765/ws?call_uuid=<uuid> mono 8000`.
2. Caller audio (L16 8 kHz) → Pipecat (VAD → STT → router → matcher).
3. Replies → edge-tts → 8 kHz PCM16 → WAV → `{"type":"streamAudio"}` JSON →
   `mod_audio_stream` temp file → `mod_audio_stream::play` event → the listener
   plays it with `uuid_broadcast`.
4. DTMF → `CHANNEL_DTMF` → `POST /api/v1/sessions/{sid}/dtmf`; every press is
   saved in `dtmf_history` and broadcast on `/ws/live`.
5. Barge-in → the pipeline sends `{"type":"clear"}` → listener runs `uuid_break`.

### Logs and smoke test

```bash
docker compose logs -f freeswitch listener voice_agent voice_ordering
docker exec -it vo-freeswitch fs_cli
./scripts/smoke_test.sh          # session service, confirmation gate, DTMF floor
```

## Run without Docker (host development)

```bash
# 1) Menu in Postgres (once)
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f menu.sql
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f voice_ordering/schema_events.sql

# 2) Session service (FSM + DTMF + /ws/live) — boots even without DB
cd voice_ordering && pip install -r requirements.txt
DATABASE_URL="postgresql://postgres:password@localhost:5433/restaurant_demo" \
  uvicorn app.main:app --port 8001

# 3) Voice pipeline — boots without FreeSWITCH too (FakeSTT/FakeTTS for testing)
cd voice_agent && pip install -r requirements.txt
TTS_BACKEND=edge uvicorn server:app --host 0.0.0.0 --port 8765

# 4) Offline script replay (needs DB + e5 model on first run)
python run_12_turns.py   # ends with asserts: total == 470, 4 order lines
```

Env: `DATABASE_URL` (menu + matcher DSN) · `SESSION_API_URL`
(default `http://127.0.0.1:8001/api/v1`) · `STT_BACKEND` · `GROQ_API_KEY` ·
`TTS_BACKEND` (`edge`|`fake`) · `EDGE_TTS_VOICE` · `FS_ESL_PASSWORD`.

## Failure isolation (demo rules)

- Postgres down → `voice_ordering` falls back to an in-memory seed menu; service still boots
- Matcher/model down → pipeline logs it and **the DTMF floor takes over** (keys 1/0,
  confirm/edit via `<index>*<qty>#` — every press saved in `dtmf_history`)
- No FreeSWITCH connected → pipeline runs standalone against the Fake STT/TTS
- edge-tts offline → the TTS stage falls back to the beep, the call stays up
- ESL listener down → audio still streams, but TTS playback and DTMF stop
  (the community module only *announces* playback files; the listener plays them)

## Status / known gaps (2026-11-19)

- Real telephony path is wired: FreeSWITCH + `mod_audio_stream` + ESL listener
- STT/TTS swap points are in place; `TTS_BACKEND=edge` is the demo voice
- `mod_audio_stream` Community Edition is AGPL-3.0-only with a FreeSWITCH
  linking exception — fine for the demo, review before shipping
- The community module accepts **JSON + base64 WAV** for playback, not raw
  binary; `voice_agent/serializer.py` wraps each utterance in a WAV accordingly
- No monitor HTML page yet (the `/ws/live` bus is ready for it)
- `pipecat-ai` pinned to 1.16.0 (the 0.0.66 pin predates the FastAPI websocket
  transport this code uses); onnxruntime needs Python 3.11/3.12 (not 3.14)
