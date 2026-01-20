"""Database models for jobs and batches."""

from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class BatchStatus(str, enum.Enum):
    queued = "queued"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class JobStatus(str, enum.Enum):
    queued = "queued"
    downloading = "downloading"
    downloaded = "downloaded"
    transcribing = "transcribing"
    completed = "completed"
    failed = "failed"
    canceled = "canceled"


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, name="batch_status"), default=BatchStatus.queued
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )

    jobs: Mapped[list["Job"]] = relationship("Job", back_populates="batch")


class Job(Base):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    batch_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("batches.id"), nullable=True
    )
    source_url: Mapped[str] = mapped_column(Text, nullable=False)
    video_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    video_id: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    uploader: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requested_format: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="job_status"), default=JobStatus.queued
    )
    progress: Mapped[float] = mapped_column(Float, default=0.0)
    download_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    transcript_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    batch: Mapped[Optional[Batch]] = relationship("Batch", back_populates="jobs")
    events: Mapped[list["JobEvent"]] = relationship("JobEvent", back_populates="job")


class JobEvent(Base):
    __tablename__ = "job_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    job_id: Mapped[str] = mapped_column(String(36), ForeignKey("jobs.id"), nullable=False)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    progress: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    job: Mapped[Job] = relationship("Job", back_populates="events")
