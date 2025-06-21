"""OpenAI Whisper transcriber module"""

import time
from pathlib import Path

import whisper

from app.audio_tools import NdArray


class WhisperTranscriber:
    """OpenAI Whisper transcriber"""

    def __init__(self, model: str = "tiny.en") -> None:
        """Initialize the transcriber"""
        # Force CPU usage for compatibility
        self.device = "cpu"

        # Load the model with CPU device
        print(f"Loading Whisper model '{model}' on {self.device}")
        self.model = whisper.load_model(model, device=self.device)
        print(f"Model loaded successfully on {self.device}")

    def _extract_text_from_result(self, result: dict) -> str:
        """Extract text from whisper result, handling both string and list cases"""
        text = result["text"]

        # Handle case where text might be a list (though this shouldn't happen with current whisper)
        if isinstance(text, list):
            return " ".join(str(item) for item in text).strip()

        # Handle normal string case
        if isinstance(text, str):
            return text.strip()

        # Fallback for any other type
        return str(text).strip()

    def transcribe_audio(self, audio_file: Path) -> str:
        """Transcribe audio from a file"""
        start_time = time.time()

        # Transcribe using OpenAI Whisper
        result = self.model.transcribe(str(audio_file))

        # Extract text from result with proper type handling
        transcription_text = self._extract_text_from_result(result)

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Transcription completed in {elapsed_time:.2f} seconds")

        return transcription_text

    def transcribe_ndarray(self, audio_data: NdArray) -> str:
        """Transcribe audio from numpy array"""
        start_time = time.time()

        # Convert numpy array to torch tensor and transcribe
        result = self.model.transcribe(audio_data)

        # Extract text from result with proper type handling
        transcription_text = self._extract_text_from_result(result)

        end_time = time.time()
        elapsed_time = end_time - start_time
        print(f"Transcription completed in {elapsed_time:.2f} seconds")

        return transcription_text
