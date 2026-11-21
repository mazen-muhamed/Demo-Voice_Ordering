"""Fake STT/TTS so the pipeline can be tested end to end without real models.
Replace with the real Egyptian-Arabic STT and TTS services later."""
import math
import struct

from pipecat.frames.frames import (
    Frame,
    OutputAudioRawFrame,
    TextFrame,
    TranscriptionFrame,
    TTSStoppedFrame,
)
try:  # pipecat 1.16 emits the VAD-specific stop frame; older releases used the turn frame.
    from pipecat.frames.frames import VADUserStoppedSpeakingFrame as _UserStoppedSpeakingFrame
except ImportError:  # pragma: no cover
    from pipecat.frames.frames import UserStoppedSpeakingFrame as _UserStoppedSpeakingFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.utils.time import time_now_iso8601


class FakeSTT(FrameProcessor):
    """When the user stops speaking, emit a fixed transcript."""

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        await self.push_frame(frame, direction)
        if isinstance(frame, _UserStoppedSpeakingFrame):
            await self.push_frame(
                TranscriptionFrame("عايز بيتزا", "caller", time_now_iso8601()), direction
            )


def beep_pcm(rate: int = 8000, seconds: float = 0.5, freq: float = 440.0) -> bytes:
    """0.5 s mono PCM16 beep — used by FakeTTS and as the EdgeTTS fallback."""
    samples = [
        int(8000 * math.sin(2 * math.pi * freq * i / rate))
        for i in range(int(rate * seconds))
    ]
    return struct.pack(f"<{len(samples)}h", *samples)


class FakeTTS(FrameProcessor):
    """Turn reply text into a 0.5 s beep (8 kHz PCM16)."""

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, TextFrame):
            rate = 8000
            await self.push_frame(
                OutputAudioRawFrame(
                    audio=beep_pcm(rate), sample_rate=rate, num_channels=1
                )
            )
            await self.push_frame(TTSStoppedFrame(), direction)
        else:
            await self.push_frame(frame, direction)
