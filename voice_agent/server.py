"""FastAPI WebSocket endpoint that FreeSWITCH connects to.

Run:  uvicorn server:app --host 0.0.0.0 --port 8765
FreeSWITCH should open a websocket to ws://<host>:8765/ws
NOTE: written against a recent pipecat-ai release; some class/param names
(VAD location, interruption params) differ between versions, so pin your version.
"""
from fastapi import FastAPI, WebSocket
from pipecat.audio.vad.silero import SileroVADAnalyzer
from pipecat.audio.vad.vad_analyzer import VADParams
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.transports.network.fastapi_websocket import (
    FastAPIWebsocketParams,
    FastAPIWebsocketTransport,
)

from dev_services import FakeSTT, FakeTTS  # TODO: swap for real STT / TTS
from processors import IntentRouter, Matcher, ReplyGenerator
from serializer import FreeSwitchFrameSerializer

app = FastAPI()


@app.websocket("/ws")
async def freeswitch_ws(websocket: WebSocket):
    await websocket.accept()

    transport = FastAPIWebsocketTransport(
        websocket=websocket,
        params=FastAPIWebsocketParams(
            audio_in_enabled=True,
            audio_out_enabled=True,
            add_wav_header=False,
            # Stage 1: VAD
            vad_analyzer=SileroVADAnalyzer(params=VADParams(stop_secs=0.6)),
            serializer=FreeSwitchFrameSerializer(),
        ),
    )

    # VAD -> STT -> Router -> Matcher -> Reply -> TTS
    pipeline = Pipeline(
        [
            transport.input(),   # audio in + VAD
            FakeSTT(),           # STT
            IntentRouter(),      # Router
            Matcher(),           # Matcher
            ReplyGenerator(),    # Reply
            FakeTTS(),           # TTS
            transport.output(),  # audio out
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            allow_interruptions=True,  # barge-in
            audio_in_sample_rate=16000,
            audio_out_sample_rate=8000,
        ),
    )

    @transport.event_handler("on_client_disconnected")
    async def on_disconnected(transport, client):
        await task.cancel()

    await PipelineRunner(handle_sigint=False).run(task)
