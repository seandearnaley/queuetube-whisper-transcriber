"""Job service helpers."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Batch, BatchStatus, Job, JobEvent, JobStatus


def create_batch(session: Session, source_url: str) -> Batch:
    batch = Batch(source_url=source_url, status=BatchStatus.queued)
    session.add(batch)
    session.flush()
    return batch


def create_job(
    session: Session,
    source_url: str,
    batch_id: Optional[str] = None,
    video_url: Optional[str] = None,
    video_id: Optional[str] = None,
    title: Optional[str] = None,
    uploader: Optional[str] = None,
    requested_format: Optional[str] = None,
) -> Job:
    job = Job(
        batch_id=batch_id,
        source_url=source_url,
        video_url=video_url,
        video_id=video_id,
        title=title,
        uploader=uploader,
        requested_format=requested_format,
        status=JobStatus.queued,
        progress=0.0,
    )
    session.add(job)
    session.flush()
    return job


def add_job_event(
    session: Session,
    job_id: str,
    event_type: str,
    message: str,
    progress: Optional[float] = None,
) -> JobEvent:
    event = JobEvent(
        job_id=job_id,
        event_type=event_type,
        message=message,
        progress=progress,
    )
    session.add(event)
    return event


def update_job_status(
    session: Session,
    job: Job,
    status: JobStatus,
    progress: Optional[float] = None,
    error: Optional[str] = None,
    download_path: Optional[str] = None,
    transcript_path: Optional[str] = None,
) -> Job:
    job.status = status
    job.updated_at = datetime.utcnow()
    if progress is not None:
        job.progress = progress
    if error is not None:
        job.error = error
    if download_path is not None:
        job.download_path = download_path
    if transcript_path is not None:
        job.transcript_path = transcript_path
    if status in {JobStatus.downloading, JobStatus.transcribing} and job.started_at is None:
        job.started_at = datetime.utcnow()
    if status in {JobStatus.completed, JobStatus.failed, JobStatus.canceled}:
        job.finished_at = datetime.utcnow()
    session.add(job)
    return job


def set_batch_status(session: Session, batch_id: str, status: BatchStatus) -> None:
    batch = session.get(Batch, batch_id)
    if not batch:
        return
    batch.status = status
    batch.updated_at = datetime.utcnow()
    session.add(batch)


def update_batch_status(session: Session, batch_id: str) -> None:
    batch = session.get(Batch, batch_id)
    if not batch:
        return

    jobs = session.scalars(select(Job).where(Job.batch_id == batch_id)).all()
    if not jobs:
        batch.status = BatchStatus.completed
        session.add(batch)
        return

    statuses = {job.status for job in jobs}
    if JobStatus.failed in statuses:
        batch.status = BatchStatus.failed
    elif all(status == JobStatus.completed for status in statuses):
        batch.status = BatchStatus.completed
    else:
        batch.status = BatchStatus.processing
    batch.updated_at = datetime.utcnow()
    session.add(batch)
