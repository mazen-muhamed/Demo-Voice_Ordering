
""" Run:  uvicorn server:app --host 0.0.0.0 --port 8765
FreeSWITCH should open a websocket to ws://<host>:8765/ws
NOTE: written against a recent pipecat-ai release; some class/param names
(VAD location, interruption params) differ between versions, so pin your version.
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.audio.vad_processor import VADProcessor
from pipecat.transports.websocket.fastapi import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)
import os

try:
    from dotenv import load_dotenv

    load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
except ImportError:
    pass

from processors import IntentRouter, Matcher, ReplyGenerator, TimingLogger
from real_stt import build_stt
from serializer import FreeSwitchFrameSerializer

app = FastAPI()


def build_tts():
    """TTS_BACKEND=edge -> Egyptian Arabic via edge-tts; default = beep."""
    if os.getenv("TTS_BACKEND", "fake").lower() == "edge":
        from edge_tts_tts import EdgeTTS

        return EdgeTTS()
    from dev_services import FakeTTS

    return FakeTTS()


@app.websocket("/ws")
async def freeswitch_ws(websocket: WebSocket):
    await websocket.accept()

    # The ESL listener passes FreeSWITCH's call UUID here.  It lets the
    # pipeline attach to the session the listener already created, so voice
    # orders and DTMF presses share one basket.
    call_uuid = websocket.query_params.get("call_uuid")

    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            # mod_audio_stream turns every websocket audio message into a
            # separate temp file + playback event.  Use 500 ms chunks (rather
            # than the 40 ms default) so a sentence is a handful of files, not
            # dozens of tiny fragments with gaps between them.
            audio_out_10ms_chunks=50,
            # Keep the transport from padding idle time with silence; the TTS
            # stage flushes the final partial chunk with TTSStoppedFrame.
            audio_out_auto_silence=False,
            serializer=FreeSwitchFrameSerializer(),
        ),
    )

    # VAD -> STT -> Router -> Matcher -> Reply -> TTS
    pipeline = Pipeline(
        [
            transport.input(),   # audio in
            VADProcessor(        # Stage 1: VAD (pipecat 1.16 moved this out of transport params)
                vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.6))
            ),
            build_stt(),         # STT: Groq whisper-large-v3 / local faster-whisper (STT_BACKEND)
            IntentRouter(),      # Router
            Matcher(call_uuid=call_uuid),  # Matcher (+ session push)
            ReplyGenerator(),    # Reply
            TimingLogger(),      # one timing line per turn -> pitch slide
            build_tts(),         # TTS (TTS_BACKEND=edge|fake)
            transport.output(),  # audio out
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            # Interruptions are enabled by default in pipecat 1.16; barge-in
            # is driven by the VAD/interruption frames, not a PipelineParams flag.
            # mod_audio_stream streams L16 mono at 8 kHz (telephony rate).
            # Interpreting it at 16 kHz double-speeds every utterance and
            # Whisper only produces hallucinations ("اشتركوا في القناة").
            audio_in_sample_rate=8000,
            audio_out_sample_rate=8000,
        ),
    )

    @transport.event_handler("on_client_disconnected")
    async def on_disconnected(transport, client):
        await task.cancel()

    await PipelineRunner(handle_sigint=False).run(task)
