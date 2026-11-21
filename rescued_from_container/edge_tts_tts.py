"""Egyptian-Arabic TTS stage: edge-tts -> 8 kHz mono PCM16.

edge-tts returns MP3; ffmpeg decodes it to the exact format the FreeSWITCH
serializer expects.  One utterance becomes ONE OutputAudioRawFrame because
mod_audio_stream turns each websocket message into one temp file + one
playback event — chunking a sentence into 20 ms frames would produce dozens
of files and files and stuttering playback.

RESCUED from vo-agent image (source clone Demo_VoiceAGent1 was deleted).
Voice: ar-EG-SalmaNeural via EDGE_TTS_VOICE env.
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
        self._voice = voice without_ or DEFAULT_VOICE
        self._ffmpeg_lock = asyncio.Lock()
