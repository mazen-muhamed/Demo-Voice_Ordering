"""STT backend — Groq whisper-large-v3 (API) with local faster-whisper fallback.

One interface, two backends, switched by STT_BACKEND:
  groq  (default, demo stage) -> Groq API whisper-large-v3, needs GROQ_API_KEY
  local                       -> faster-whisper small int8 on CPU (cached model)
  fake                        -> FakeSTT in the pipeline (offline plumbing tests)

The pipeline never knows which is active: transcribe(pcm16_bytes_16k) -> str.
Whisper needs NO database — audio in, text out; the transcript flows into
the router/matcher. Spec §2: both backends must exist; Groq is on stage,
local is the automatic fallback when the API fails.
"""
import io
import os
import time
import wave

import httpx

GROQ_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
GROQ_MODEL = "whisper-large-v3"


def pcm16_to_wav(pcm16: bytes, sample_rate: int = 16000) -> bytes:
    """Wrap raw PCM16 mono bytes in a WAV container (Groq wants a file)."""
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm16)
    return buf.getvalue()


class GroqSTT:
    def __init__(self) -> None:
        self._key = os.getenv("GROQ_API_KEY", "")
        if not self._key:
            raise RuntimeError("GROQ_API_KEY not set")
        self._http = httpx.AsyncClient(timeout=30.0)

    async def transcribe(self, pcm16: bytes, sample_rate: int = 16000) -> str:
        t0 = time.perf_counter()
        files = {"file": ("audio.wav", pcm16_to_wav(pcm16, sample_rate), "audio/wav")}
        data = {"model": GROQ_MODEL, "language": "ar", "response_format": "text"}
        resp = await self._http.post(
            GROQ_URL, files=files, data=data,
            headers={"Authorization": f"Bearer {self._key}"},
        )
        resp.raise_for_status()
        text = resp.text.strip()
        print(f"[stt] groq {time.perf_counter() - t0:.0f}ms -> {text[:40]}")
        return text


class LocalSTT:
    """faster-whisper small int8 on CPU — model already in the HF cache."""

    def __init__(self) -> None:
        from faster_whisper import WhisperModel  # lazy: heavy import

        self._model = WhisperModel("small", device="cpu", compute_type="int8")

    async def transcribe(self, pcm16: bytes, sample_rate: int = 16000) -> str:
        t0 = time.perf_counter()
        import numpy as np

        audio = np.frombuffer(pcm16, dtype=np.int16).astype(np.float32) / 32768.0
        if sample_rate != 16000:
            # linear resample (pipeline audio is always 16k; this is a safety net)
            n_out = int(len(audio) * 16000 / sample_rate)
            audio = np.interp(
                np.linspace(0.0, len(audio) - 1, n_out), np.arange(len(audio)), audio
            ).astype(np.float32)
        segments, _ = self._model.transcribe(
            audio, language="ar", vad_filter=False, beam_size=1
        )
        text = " ".join(seg.text for seg in segments).strip()
        print(f"[stt] local {time.perf_counter() - t0:.0f}ms -> {text[:40]}")
        return text


_active = None


def get_stt():
    """STT_BACKEND=groq|local (default groq, auto-falls-back to local on error).
    Raises only for 'fake' handling in the pipeline (FakeSTT used directly)."""
    global _active
    if _active is not None:
        return _active

    backend = os.getenv("STT_BACKEND", "groq")
    if backend == "local":
        _active = LocalSTT()
    else:
        try:
            _active = GroqSTT()
        except Exception as e:  # noqa: BLE001 - no key -> straight to local
            print(f"[stt] groq unavailable ({e}); using local faster-whisper")
            _active = LocalSTT()
    return _active
