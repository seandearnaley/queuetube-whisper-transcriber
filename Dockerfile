# Use Python 3.11 for better performance and compatibility
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Install PyTorch CPU-only version first (much faster with pre-built wheels)
RUN pip install --no-cache-dir torch torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install OpenAI Whisper
RUN pip install --no-cache-dir openai-whisper

# Install other Python dependencies with latest yt-dlp
RUN pip install --no-cache-dir \
    celery==5.3.6 \
    redis==5.0.1 \
    pydantic==2.5.3 \
    yt-dlp \
    loguru==0.7.2 \
    fastapi==0.109.0 \
    uvicorn[standard]==0.26.0 \
    requests==2.31.0 \
    beautifulsoup4==4.12.3 \
    aiofiles==23.2.1 \
    python-multipart==0.0.6 \
    ffmpeg-python==0.2.0

# Copy application code
COPY . /app/

# Start the application
CMD ["uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
