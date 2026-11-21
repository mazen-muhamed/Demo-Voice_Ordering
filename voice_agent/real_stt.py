"""Real STT pipeline stage — replaces FakeSTT when STT_BACKEND != fake.

Buffers caller audio frames (16 kHz PCM16 after the serializer resample);
when the VAD says the user stopped speaking, transcribes the buffered
utterance via the configured backend (stt.py: Groq API or local
faster-whisper) and pushes a TranscriptionFrame downstream — the exact
frame the IntentRouter already consumes.
"""
import os
import time

from pipecat.frames.frames import (
    Frame,
    InputAudioRawFrame,
    TranscriptionFrame,
)
try:  # pipecat 1.16 emits the VAD-specific stop frame; older releases used the turn frame.
    from pipecat.frames.frames import VADUserStoppedSpeakingFrame as _UserStoppedSpeakingFrame
except ImportError:  # pragma: no cover
    from pipecat.frames.frames import UserStoppedSpeakingFrame as _UserStoppedSpeakingFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.utils.time import time_now_iso8601

from stt import get_stt


class WhisperSTT(FrameProcessor):
    def __init__(self) -> None:
        super().__init__()
        self._buffer = bytearray()
        self._rate: int | None = None  # actual rate of buffered frames
        self._backend = None  # lazy: don't load the model at import time

    def _get_backend(self):
        if self._backend is None:
            self._backend = get_stt()
        return self._backend

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if isinstance(frame, InputAudioRawFrame):
            if self._rate is None:
                self._rate = frame.sample_rate  # trust the transport's label
            self._buffer.extend(frame.audio)
            await self.push_frame(frame, direction)
        elif isinstance(frame, _UserStoppedSpeakingFrame):
            await self.push_frame(frame, direction)  # never swallow the VAD event
            pcm = bytes(self._buffer)
            rate = self._rate or 8000
            self._buffer.clear()
            self._rate = None
            if len(pcm) < rate // 10:  # <100 ms of audio: ASR noise, skip
                return
            t0 = time.perf_counter()
            try:
                text = await self._get_backend().transcribe(pcm, rate)
            except Exception as e:  # noqa: BLE001 - DTMF floor takes over
                print(f"[stt] FAILED ({e}) — DTMF floor takes over")
                return
            ms = (time.perf_counter() - t0) * 1000
            if text:
                await self.push_frame(
                    TranscriptionFrame(text, "caller", time_now_iso8601()), direction
                )
            print(f"stage=stt {ms:.0f}ms | '{text[:50]}'")
        else:
            await self.push_frame(frame, direction)


def build_stt() -> FrameProcessor:
    """FakeSTT for offline plumbing (STT_BACKEND=fake), WhisperSTT otherwise."""
    if os.getenv("STT_BACKEND", "groq") == "fake":
        from dev_services import FakeSTT

        return FakeSTT()
    return WhisperSTT()
