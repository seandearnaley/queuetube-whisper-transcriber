"""Application configuration."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime settings loaded from environment variables."""

    env: str = "development"
    redis_url: str = "redis://redis:6379/0"
    database_url: str = "sqlite:///./data/qtube.db"
    downloads_dir: str = "downloads"
    models_dir: str = "models"
    whisper_model: str = "base.en"
    transcription_device: str = "cpu"
    transcription_compute_type: str = "int8"
    ytdlp_cookies_file: str | None = None
    cors_origins: List[str] = ["*"]

    model_config = SettingsConfigDict(
        env_prefix="QTUBE_",
        env_file=".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
