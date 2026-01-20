"""Whisper transcription using faster-whisper."""

from __future__ import annotations

import time
from pathlib import Path

from faster_whisper import WhisperModel

from app.config import get_settings

settings = get_settings()


class WhisperTranscriber:
    """faster-whisper transcriber."""

    def __init__(self, model: str | None = None) -> None:
        model_name = model or settings.whisper_model
        self.device = settings.transcription_device
        self.compute_type = settings.transcription_compute_type

        print(f"Loading faster-whisper model '{model_name}' on {self.device}")
        self.model = WhisperModel(
            model_name,
            device=self.device,
            compute_type=self.compute_type,
        )
        print(f"Model loaded successfully on {self.device}")

    def transcribe_audio(self, audio_file: Path) -> str:
        """Transcribe audio from a file."""
        start_time = time.time()
        segments, _info = self.model.transcribe(str(audio_file))
        transcription_text = "".join(segment.text for segment in segments).strip()
        elapsed_time = time.time() - start_time
        print(f"Transcription completed in {elapsed_time:.2f} seconds")
        return transcription_text
