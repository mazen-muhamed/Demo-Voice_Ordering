"""Fake STT/TTS so the pipeline can be tested end to end without real models.
Replace with the real Egyptian-Arabic STT and TTS services later."""
import math
import struct

from pipecat.frames.frames import (
    Frame,
    OutputAudioRawFrame,
    TextFrame,
    TranscriptionFrame,
    UserStoppedSpeakingFrame,
)
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor
from pipecat.utils.time import time_now_iso8601


class FakeSTT(FrameProcessor):
    """When the user stops speaking, emit a fixed transcript."""

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        await self.push_frame(frame, direction)
        if isinstance(frame, UserStoppedSpeakingFrame):
            await self.push_frame(
                TranscriptionFrame("عايز بيتزا", "caller", time_now_iso8601()), direction
            )


class FakeTTS(FrameProcessor):
    """Turn reply text into a 0.5 s beep (8 kHz PCM16)."""

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        if isinstance(frame, TextFrame):
            rate = 8000
            samples = [
                int(8000 * math.sin(2 * math.pi * 440 * i / rate))
                for i in range(rate // 2)
            ]
            audio = struct.pack(f"<{len(samples)}h", *samples)
            await self.push_frame(
                OutputAudioRawFrame(audio=audio, sample_rate=rate, num_channels=1)
            )
        else:
            await self.push_frame(frame, direction)
