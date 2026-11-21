"""FreeSWITCH <-> Pipecat frame serializer.

Wire format (mod_audio_stream, community edition):

  FreeSWITCH -> us   raw L16 / PCM16 binary frames at the wire rate (8 kHz)
  us -> FreeSWITCH   JSON {"type":"streamAudio","data":{...}} with base64

The community module does not accept raw binary playback and does not play
audio itself: it writes each message to a temp file and fires
``mod_audio_stream::play``.  The ESL listener (listener.py) plays that file
with ``uuid_broadcast``.  We therefore send a complete WAV per utterance:
WAV is always playable by mod_sndfile, whereas the module's raw ``.r8`` temp
files are not registered with FreeSWITCH's file-format layer.

Barge-in is a separate control message (``{"type":"clear"}``); the listener
turns it into ``uuid_break``.
"""
import base64
import io
import json
import wave

from pipecat.frames.frames import Frame, InputAudioRawFrame, OutputAudioRawFrame
from pipecat.serializers.base_serializer import FrameSerializer

try:  # Pipecat renamed this frame in newer releases
    from pipecat.frames.frames import InterruptionFrame as InterruptionFrameT
except ImportError:  # pragma: no cover
    from pipecat.frames.frames import StartInterruptionFrame as InterruptionFrameT

CLEAR_MESSAGE = json.dumps({"type": "clear"})


def _wav_container(pcm: bytes, sample_rate: int) -> bytes:
    """Wrap mono PCM16 in a RIFF/WAV header (no ffmpeg needed)."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(pcm)
    return buffer.getvalue()


class FreeSwitchFrameSerializer(FrameSerializer):
    def __init__(self, phone_rate: int = 8000):
        super().__init__(
            FrameSerializer.InputParams(
                audio_in_sample_rate=phone_rate,
                audio_out_sample_rate=phone_rate,
            )
        )
        # Remember the wire rate explicitly: FrameSerializer._sample_rate is
        # the pipeline's *input* rate (16 kHz), not the rate we send on.
        self._phone_rate = phone_rate

    async def serialize(self, frame: Frame) -> str | bytes | None:
        # Barge-in: ask the ESL listener to stop whatever is playing.
        if isinstance(frame, InterruptionFrameT):
            await self._reset_audio_out()
            return CLEAR_MESSAGE

        # Bot audio -> 8 kHz PCM16 -> WAV -> base64 -> mod_audio_stream.
        if isinstance(frame, OutputAudioRawFrame):
            pcm = await self._resample_audio_out(frame)
            if not pcm:
                return None
            payload = {
                "type": "streamAudio",
                "data": {
                    "audioDataType": "wav",
                    "sampleRate": self._phone_rate,
                    "audioData": base64.b64encode(
                        _wav_container(pcm, self._phone_rate)
                    ).decode("ascii"),
                },
            }
            return json.dumps(payload)
        return None

    async def deserialize(self, data: str | bytes) -> Frame | None:
        # Text = control/metadata from FreeSWITCH. Ignored for now.
        if isinstance(data, str):
            return None

        # Caller audio: 8 kHz PCM16 -> pipeline input rate.
        audio = await self._resample_audio_in(data)
        return InputAudioRawFrame(
            audio=audio, sample_rate=self._sample_rate, num_channels=1
        )
