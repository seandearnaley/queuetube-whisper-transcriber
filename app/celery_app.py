"""Celery application instance."""

from celery import Celery

from app.config import get_settings

settings = get_settings()

celery_app = Celery(
    "qtube",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.download_processor",
        "app.transcription_processor",
    ],
)

celery_app.conf.update(
    task_routes={
        "app.download_processor.*": {"queue": "download_queue"},
        "app.transcription_processor.*": {"queue": "transcription_queue"},
    }
)

celery_app.autodiscover_tasks(["app"])
