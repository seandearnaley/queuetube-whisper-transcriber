"""Pydantic schemas for API."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models import BatchStatus, JobStatus


class JobCreateRequest(BaseModel):
    url: str = Field(..., min_length=3)
    format_id: Optional[str] = Field(default=None, max_length=64)


class BatchCreateResponse(BaseModel):
    batch_id: str
    message: str


class BatchResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_url: str
    status: BatchStatus
    created_at: datetime
    updated_at: datetime


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    batch_id: Optional[str]
    source_url: str
    video_url: Optional[str]
    video_id: Optional[str]
    title: Optional[str]
    uploader: Optional[str]
    requested_format: Optional[str]
    status: JobStatus
    progress: float
    download_path: Optional[str]
    transcript_path: Optional[str]
    error: Optional[str]
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]


class JobEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_id: str
    event_type: str
    message: str
    progress: Optional[float]
    created_at: datetime


class JobListResponse(BaseModel):
    jobs: List[JobResponse]
    total: int


class BatchDetailResponse(BaseModel):
    batch: BatchResponse
    jobs: List[JobResponse]
    total: int


class SettingsResponse(BaseModel):
    cookies_configured: bool
    cookies_path: Optional[str]


class PreviewRequest(BaseModel):
    url: str = Field(..., min_length=3)


class DownloadFormatOption(BaseModel):
    format_id: str
    ext: Optional[str]
    resolution: Optional[str]
    width: Optional[int]
    height: Optional[int]
    fps: Optional[float]
    filesize: Optional[int]
    filesize_approx: Optional[int]
    vcodec: Optional[str]
    acodec: Optional[str]
    format_note: Optional[str]
    tbr: Optional[float]
    audio_channels: Optional[int]
    has_audio: bool
    has_video: bool


class PreviewResponse(BaseModel):
    title: Optional[str]
    uploader: Optional[str]
    duration: Optional[float]
    webpage_url: Optional[str]
    thumbnail: Optional[str]
    formats: List[DownloadFormatOption]


class DeleteJobResponse(BaseModel):
    job_id: str
    message: str
