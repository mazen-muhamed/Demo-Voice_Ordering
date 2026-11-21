FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app

# ffmpeg: edge-tts returns MP3; we decode it to 8 kHz PCM16 for the pipeline.
# curl: compose healthcheck.  libgomp1: torch/onnxruntime runtime.
RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg curl libgomp1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY voice_agent/requirements.txt /app/voice_agent/requirements.txt

# CPU torch first, otherwise sentence-transformers pulls the CUDA wheel.
RUN pip install --upgrade pip \
    && pip install torch --index-url https://download.pytorch.org/whl/cpu \
    && pip install -r /app/voice_agent/requirements.txt

# menu_matcher.py lives at the repo root and is imported as a top-level module.
COPY menu_matcher.py /app/menu_matcher.py
COPY voice_agent /app/voice_agent

WORKDIR /app/voice_agent

EXPOSE 8765

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8765"]
