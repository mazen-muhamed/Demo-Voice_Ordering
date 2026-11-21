"""FreeSWITCH ESL bridge for the voice-ordering demo.

Responsibilities (the "Youssef-Sayed" box in the architecture):

  CHANNEL_ANSWER          create the voice_ordering session, then start
                          mod_audio_stream -> Pipecat
                          ws://<agent>/ws?call_uuid=<uuid>
  CHANNEL_DTMF            POST the digit to the session FSM (DTMF floor)
  mod_audio_stream::play  play the temp WAV the module produced from the
                          pipeline's TTS audio (uuid_broadcast)
  mod_audio_stream::json  {"type":"clear"} from the pipeline -> uuid_break
  CHANNEL_HANGUP_COMPLETE forget the call

The listener does NOT write to /ws/live directly.  It drives the session
service; the session service broadcasts every state change on /ws/live, which
is the monitor page's event bus.

No third-party dependencies: asyncio + urllib from the standard library.
"""

from __future__ import annotations

import asyncio
import json
import os
import signal
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

FS_ESL_HOST = os.getenv("FS_ESL_HOST", "127.0.0.1")
FS_ESL_PORT = int(os.getenv("FS_ESL_PORT", "8021"))
FS_ESL_PASSWORD = os.getenv("FS_ESL_PASSWORD", "ClueCon")
SESSION_API = os.getenv("SESSION_API_URL", "http://127.0.0.1:8001/api/v1").rstrip("/")
WS_URL = os.getenv("VOICE_AGENT_WS_URL", "ws://127.0.0.1:8765/ws")
SESSION_TTL = int(os.getenv("SESSION_TTL_SECONDS", "300"))
FS_TEMP_DIR = os.getenv("FS_TEMP_DIR", "/tmp").rstrip("/") + "/"


EVENT_SUBSCRIPTION = (
    "CHANNEL_ANSWER CHANNEL_DTMF CHANNEL_HANGUP_COMPLETE "
    "CUSTOM mod_audio_stream::play mod_audio_stream::json"
)


def log(message: str) -> None:
    stamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"{stamp} {message}", flush=True)


def _http_json(method: str, url: str, payload=None, timeout: float = 5.0):
    data = None
    headers = {}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"

    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read()
            return response.status, (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            body = json.loads(raw) if raw else None
        except ValueError:
            body = raw.decode("utf-8", "replace")
        return exc.code, body


async def http_json(method: str, url: str, payload=None, timeout: float = 5.0):
    return await asyncio.to_thread(_http_json, method, url, payload, timeout)


def with_query(url: str, key: str, value: str) -> str:
    separator = "&" if urllib.parse.urlparse(url).query else "?"
    return f"{url}{separator}{key}={urllib.parse.quote(value, safe='')}"


class ESLClient:
    def __init__(self) -> None:
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self._api_replies: asyncio.Queue[str] = asyncio.Queue()
        self._api_lock = asyncio.Lock()

    async def connect(self) -> None:
        self.reader, self.writer = await asyncio.open_connection(FS_ESL_HOST, FS_ESL_PORT)

        headers, _ = await self._read_message()
        if headers.get("content-type") != "auth/request":
            raise RuntimeError(f"unexpected ESL greeting: {headers}")

        await self._send(f"auth {FS_ESL_PASSWORD}")
        headers, body = await self._read_message()
        if not (headers.get("reply-text") or body).startswith("+OK"):
            raise RuntimeError(f"ESL auth failed: {headers.get('reply-text') or body!r}")

        await self._send(f"event plain {EVENT_SUBSCRIPTION}")
        headers, body = await self._read_message()
        if not (headers.get("reply-text") or body).startswith("+OK"):
            raise RuntimeError(f"ESL subscribe failed: {headers.get('reply-text') or body!r}")

        log(f"[esl] connected to {FS_ESL_HOST}:{FS_ESL_PORT}")

    async def _send(self, line: str) -> None:
        assert self.writer is not None
        self.writer.write((line + "\n\n").encode("utf-8"))
        await self.writer.drain()

    async def _read_message(self) -> tuple[dict[str, str], str]:
        assert self.reader is not None
        headers: dict[str, str] = {}
        while True:
            line = await self.reader.readline()
            if not line:
                raise ConnectionError("ESL closed the connection")
            text = line.decode("utf-8", "replace").rstrip("\r\n")
            if text == "":
                break
            if ":" in text:
                key, value = text.split(":", 1)
                headers[key.strip().lower()] = value.strip()

        length = int(headers.get("content-length") or 0)
        body = await self.reader.readexactly(length) if length else b""
        return headers, body.decode("utf-8", "replace")

    async def api(self, command: str, timeout: float = 10.0) -> str | None:
        async with self._api_lock:
            await self._send(f"api {command}")
            try:
                return await asyncio.wait_for(self._api_replies.get(), timeout)
            except asyncio.TimeoutError:
                log(f"[esl] api timeout: {command[:80]}")
                return None

    async def serve(self, on_event) -> None:
        while True:
            headers, body = await self._read_message()
            content_type = headers.get("content-type", "")

            if content_type == "api/response":
                self._api_replies.put_nowait(body)
            elif content_type == "text/event-plain":
                event = parse_plain_event(body)
                asyncio.create_task(_dispatch(on_event, event))
            elif content_type == "text/disconnect-notice":
                raise ConnectionError("ESL disconnect notice")
            # command/reply and log/data messages are ignored here

    async def close(self) -> None:
        if self.writer is not None:
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except Exception:  # noqa: BLE001 - best effort
                pass


def parse_plain_event(raw: str) -> dict[str, str]:
    """Parse a text/event-plain body into headers + `_body`.

    ESL URL-encodes header values; JSON bodies keep their structure.
    """
    raw = raw.replace("\r\n", "\n")
    head, _, body = raw.partition("\n\n")
    event: dict[str, str] = {}
    for line in head.split("\n"):
        if ":" in line:
            key, value = line.split(":", 1)
            event[key.strip()] = urllib.parse.unquote(value.strip())
    # FreeSWITCH's text/event-plain body is URL-encoded, including JSON
    # payloads from mod_audio_stream.  Decode it before json.loads().
    event["_body"] = urllib.parse.unquote(body)
    return event


async def _dispatch(handler, event: dict[str, str]) -> None:
    try:
        await handler(event)
    except Exception as exc:  # noqa: BLE001 - one bad event must not kill ESL
        log(f"[handler] {type(exc).__name__}: {exc}")


class Bridge:
    def __init__(self, esl: ESLClient) -> None:
        self.esl = esl
        self.sessions: dict[str, str] = {}

    async def on_event(self, event: dict[str, str]) -> None:
        name = event.get("Event-Name", "")
        # FreeSWITCH custom events arrive as Event-Name: CUSTOM with the
        # actual name in Event-Subclass (e.g. mod_audio_stream::play).
        if name == "CUSTOM":
            name = event.get("Event-Subclass", "")
        uuid = event.get("Unique-ID") or event.get("Channel-Call-UUID") or ""
        if not uuid:
            return

        if name == "CHANNEL_ANSWER":
            await self.on_answer(uuid)
        elif name == "CHANNEL_DTMF":
            await self.on_dtmf(uuid, event.get("DTMF-Digit", ""))
        elif name == "CHANNEL_HANGUP_COMPLETE":
            self.sessions.pop(uuid, None)
            log(f"[call] {uuid} hung up")
        elif name == "mod_audio_stream::play":
            await self.on_play(uuid, event.get("_body", ""))
        elif name == "mod_audio_stream::json":
            await self.on_pipeline_message(uuid, event.get("_body", ""))

    async def on_answer(self, uuid: str) -> None:
        if uuid in self.sessions:
            return

        session_id = await self.create_session(uuid)
        if session_id:
            self.sessions[uuid] = session_id
            log(f"[call] {uuid} -> session {session_id}")
        else:
            log(f"[call] {uuid}: session service unavailable; DTMF will retry lookup")

        await self.esl.api(f"uuid_setvar {uuid} STREAM_SUPPRESS_LOG true")
        url = with_query(WS_URL, "call_uuid", uuid)
        result = await self.esl.api(f"uuid_audio_stream {uuid} start {url} mono 8000")
        log(f"[stream] start {uuid}: {result!r}")

    async def create_session(self, uuid: str) -> str | None:
        for attempt in range(1, 6):
            try:
                status, data = await http_json(
                    "POST",
                    f"{SESSION_API}/sessions",
                    {"caller_number": uuid, "ttl_seconds": SESSION_TTL},
                )
                if status in (200, 201) and isinstance(data, dict) and data.get("id"):
                    return data["id"]
                log(f"[session] create -> HTTP {status}: {data}")
            except Exception as exc:  # noqa: BLE001
                log(f"[session] create failed ({exc}); retry {attempt}/5")
            await asyncio.sleep(0.3)
        return None

    async def lookup_session(self, uuid: str) -> str | None:
        try:
            status, data = await http_json(
                "GET",
                f"{SESSION_API}/sessions/by-caller/{urllib.parse.quote(uuid, safe='')}",
            )
            if status == 200 and isinstance(data, dict):
                return data.get("id")
            log(f"[session] lookup {uuid} -> HTTP {status}")
        except Exception as exc:  # noqa: BLE001
            log(f"[session] lookup failed: {exc}")
        return None

    # -- DTMF floor --------------------------------------------------------
    async def on_dtmf(self, uuid: str, digit: str) -> None:
        if not digit:
            return

        session_id = self.sessions.get(uuid)
        if not session_id:
            session_id = await self.lookup_session(uuid)
            if session_id:
                self.sessions[uuid] = session_id

        if not session_id:
            log(f"[dtmf] {uuid}: no session yet, dropping {digit!r}")
            return

        status, data = await http_json(
            "POST", f"{SESSION_API}/sessions/{session_id}/dtmf", {"digit": digit}
        )
        action = None
        if isinstance(data, dict):
            history = data.get("dtmf_history") or []
            if history:
                action = history[-1].get("action")
        log(f"[dtmf] {uuid} {digit!r} -> HTTP {status} action={action}")

    # -- audio coming back from the pipeline -------------------------------
    async def on_play(self, uuid: str, body: str) -> None:
        """mod_audio_stream writes the base64 payload to a temp file and fires
        this event; we are the component that actually plays it."""
        try:
            payload = json.loads(body)
        except ValueError:
            log(f"[play] non-JSON payload: {body[:80]!r}")
            return

        path = payload.get("file")
        if not path or not path.startswith("/"):
            log(f"[play] missing/invalid file: {payload}")
            return
        # Only accept files the module wrote into the FreeSWITCH temp dir.
        if not path.startswith(FS_TEMP_DIR):
            log(f"[play] refusing path outside {FS_TEMP_DIR}: {path}")
            return

        result = await self.esl.api(f"uuid_broadcast {uuid} {path} aleg")
        log(f"[play] {uuid} {os.path.basename(path)} -> {result!r}")

    async def on_pipeline_message(self, uuid: str, body: str) -> None:
        try:
            payload = json.loads(body)
        except ValueError:
            return
        if payload.get("type") == "clear":
            result = await self.esl.api(f"uuid_break {uuid} all")
            log(f"[barge-in] {uuid} clear -> {result!r}")


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------
async def main() -> None:
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:  # pragma: no cover - non-POSIX
            pass

    while not stop.is_set():
        client = ESLClient()
        try:
            await client.connect()
            await client.serve(Bridge(client).on_event)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - reconnect forever
            log(f"[esl] {type(exc).__name__}: {exc}; reconnecting in 3s")
        finally:
            await client.close()

        try:
            await asyncio.wait_for(stop.wait(), timeout=3)
        except asyncio.TimeoutError:
            pass

    log("[esl] stopped")


if __name__ == "__main__":
    asyncio.run(main())
