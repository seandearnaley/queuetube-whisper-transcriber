"""Transcription worker tasks."""

from __future__ import annotations

from pathlib import Path

from celery.signals import worker_process_init
from celery.utils.log import get_task_logger

from app.celery_app import celery_app
from app.config import get_settings
from app import db
from app.models import Job, JobStatus
from sqlalchemy import select

from app.services.jobs import add_job_event, create_job, update_batch_status, update_job_status
from app.whisper_transcriber import WhisperTranscriber

logger = get_task_logger(__name__)
settings = get_settings()


@worker_process_init.connect
def init_transcriber(**kwargs):
    transcribe_video.transcriber = WhisperTranscriber()


@celery_app.task(bind=True, name="app.transcription_processor.transcribe_video")
def transcribe_video(self, job_id: str) -> None:
    """Transcribe the downloaded video for a job."""
    with db.SessionLocal() as session:
        job = session.get(Job, job_id)
        if not job:
            logger.error("Job %s not found", job_id)
            return

        if not job.download_path:
            update_job_status(session, job, JobStatus.failed, error="Missing download path")
            add_job_event(session, job.id, "failed", "Missing download path")
            session.commit()
            return

        update_job_status(session, job, JobStatus.transcribing, progress=60.0)
        add_job_event(session, job.id, "transcribing", "Transcription started", 60.0)
        session.commit()

        try:
            transcription = self.transcriber.transcribe_audio(Path(job.download_path))
            transcript_path = f"{job.download_path}.txt"
            with open(transcript_path, "w") as handle:
                handle.write(transcription)

            update_job_status(
                session, job, JobStatus.completed, progress=100.0, transcript_path=transcript_path
            )
            add_job_event(session, job.id, "completed", "Transcription completed", 100.0)
            session.commit()
            if job.batch_id:
                update_batch_status(session, job.batch_id)
                session.commit()
        except Exception as exc:
            logger.error("Transcription failed for %s: %s", job_id, exc)
            update_job_status(session, job, JobStatus.failed, error=str(exc))
            add_job_event(session, job.id, "failed", f"Transcription failed: {exc}")
            session.commit()
            if job.batch_id:
                update_batch_status(session, job.batch_id)
                session.commit()


def find_untranscribed_videos(directory: Path) -> list[Path]:
    """Find mp4 files with no matching txt transcript."""
    untranscribed = []
    for video_path in directory.glob("**/*.mp4"):
        txt_path = video_path.with_name(video_path.name + ".txt")
        if not txt_path.exists():
            untranscribed.append(video_path)
    return untranscribed


@celery_app.task(name="app.transcription_processor.process_untranscribed_videos")
def process_untranscribed_videos(directory: str | None = None) -> None:
    """Queue transcription jobs for any downloaded videos missing transcripts."""
    target_dir = Path(directory or settings.downloads_dir)
    untranscribed = find_untranscribed_videos(target_dir)
    logger.info("Found %s untranscribed videos", len(untranscribed))

    with db.SessionLocal() as session:
        for video_path in untranscribed:
            existing = session.scalar(
                select(Job).where(Job.download_path == str(video_path))
            )
            if existing:
                continue
            job = create_job(session, source_url="local", video_url=None)
            update_job_status(session, job, JobStatus.downloaded, progress=50.0, download_path=str(video_path))
            add_job_event(session, job.id, "downloaded", "Imported local download", 50.0)
            session.commit()
            transcribe_video.apply_async(args=[job.id], queue="transcription_queue")
