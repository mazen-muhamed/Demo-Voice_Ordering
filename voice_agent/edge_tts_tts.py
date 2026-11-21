"""Egyptian-Arabic TTS stage: edge-tts -> 8 kHz mono PCM16.

edge-tts returns MP3; ffmpeg decodes it to the exact format the FreeSWITCH
serializer expects.  One utterance becomes ONE OutputAudioRawFrame because
mod_audio_stream turns each websocket message into one temp file + one
playback event — chunking a sentence into 20 ms frames would produce dozens
of files and stuttering playback.

If edge-tts is offline or the voice fails, the stage falls back to the beep
so the demo never goes silent.
"""
import asyncio
import os

import edge_tts
from pipecat.frames.frames import Frame, OutputAudioRawFrame, TextFrame, TTSStoppedFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor

from dev_services import beep_pcm

DEFAULT_VOICE = os.getenv("EDGE_TTS_VOICE", "ar-EG-SalmaNeural")
RATE = 8000


class EdgeTTS(FrameProcessor):
    def __init__(self, voice: str | None = None) -> None:
        super().__init__()
        self._voice = voice or DEFAULT_VOICE
        self._ffmpeg_lock = asyncio.Lock()

    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)

        if not isinstance(frame, TextFrame):
            await self.push_frame(frame, direction)
            return

        try:
            pcm = await self._synthesize(frame.text)
        except Exception as exc:  # noqa: BLE001 - demo must keep talking
            print(f"[tts] edge-tts failed ({exc}); falling back to beep")
            pcm = beep_pcm(RATE)

        if pcm:
            await self.push_frame(
                OutputAudioRawFrame(audio=pcm, sample_rate=RATE, num_channels=1)
            )
            # Flush the transport's buffered audio now, so the whole utterance
            # becomes one streamAudio message (one temp file, one broadcast).
            await self.push_frame(TTSStoppedFrame(), direction)

    async def _synthesize(self, text: str) -> bytes:
        communicate = edge_tts.Communicate(text, self._voice)
        mp3 = bytearray()
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio" and chunk.get("data"):
                mp3.extend(chunk["data"])
        if not mp3:
            raise RuntimeError("edge-tts returned no audio")
        return await self._mp3_to_pcm(bytes(mp3))

    async def _mp3_to_pcm(self, mp3: bytes) -> bytes:
        async with self._ffmpeg_lock:
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-i", "pipe:0",
                "-f", "s16le", "-acodec", "pcm_s16le",
                "-ac", "1", "-ar", str(RATE),
                "pipe:1",
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            out, err = await process.communicate(mp3)

        if process.returncode != 0:
            raise RuntimeError(err.decode("utf-8", "replace")[-300:])
        return out
