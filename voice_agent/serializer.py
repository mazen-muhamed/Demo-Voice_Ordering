"""FreeSWITCH <-> Pipecat frame serializer.

ASSUMPTION (check against your FreeSWITCH module, e.g. mod_audio_stream / mod_audio_fork):
  - FreeSWITCH sends raw PCM16 mono audio as BINARY websocket messages at 8 kHz.
  - It may also send TEXT (JSON) metadata messages, which we ignore here.
  - To play audio back we send raw PCM16 8 kHz BINARY messages.
  - To stop playback on barge-in we send a JSON text message {"type": "clear"}.
    Change CLEAR_MESSAGE to whatever your module expects.
"""
import json

from pipecat.audio.utils import create_default_resampler
from pipecat.frames.frames import (
    Frame,
    InputAudioRawFrame,
    OutputAudioRawFrame,
    StartFrame,
)
from pipecat.serializers.base_serializer import FrameSerializer, FrameSerializerType

try:  # Pipecat renamed this frame in newer releases
    from pipecat.frames.frames import StartInterruptionFrame as InterruptionFrameT
except ImportError:  # pragma: no cover
    from pipecat.frames.frames import InterruptionFrame as InterruptionFrameT

CLEAR_MESSAGE = json.dumps({"type": "clear"})


class FreeSwitchFrameSerializer(FrameSerializer):
    def __init__(self, phone_rate: int = 8000, pipeline_rate: int = 16000):
        super().__init__()
        self._phone_rate = phone_rate        # 8 kHz telephony side
        self._pipeline_rate = pipeline_rate  # 16 kHz side (VAD / STT)
        self._resampler = create_default_resampler()

    @property
    def type(self) -> FrameSerializerType:
        return FrameSerializerType.BINARY

    async def setup(self, frame: StartFrame):
        pass

    async def serialize(self, frame: Frame) -> str | bytes | None:
        # Barge-in: tell FreeSWITCH to flush whatever audio it is still playing.
        if isinstance(frame, InterruptionFrameT):
            return CLEAR_MESSAGE

        # Bot audio -> 8 kHz PCM16 back to the caller.
        if isinstance(frame, OutputAudioRawFrame):
            return await self._resampler.resample(
                frame.audio, frame.sample_rate, self._phone_rate
            )
        return None

    async def deserialize(self, data: str | bytes) -> Frame | None:
        # Text = metadata from FreeSWITCH (call uuid, etc). Ignored for now.
        if isinstance(data, str):
            return None

        # Caller audio: 8 kHz PCM16 -> 16 kHz PCM16.
        audio = await self._resampler.resample(
            data, self._phone_rate, self._pipeline_rate
        )
        return InputAudioRawFrame(
            audio=audio, sample_rate=self._pipeline_rate, num_channels=1
        )
