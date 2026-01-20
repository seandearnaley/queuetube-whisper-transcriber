"""FastAPI server for QueueTube Whisper Transcriber."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional

import mimetypes

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from pydantic import BaseModel
from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session
from yt_dlp import YoutubeDL

from app.config import get_settings
from app.db import get_session, init_db
from app.download_processor import _base_ydl_params, enqueue_url
from app.transcription_processor import process_untranscribed_videos
from app.models import Batch, Job, JobEvent, JobStatus
from app.schemas import (
    BatchCreateResponse,
    BatchDetailResponse,
    BatchResponse,
    DeleteJobResponse,
    DownloadFormatOption,
    JobCreateRequest,
    JobEventResponse,
    JobListResponse,
    JobResponse,
    PreviewRequest,
    PreviewResponse,
    SettingsResponse,
)
from app.services.jobs import create_batch, update_batch_status

settings = get_settings()


class YouTubeURL(BaseModel):
    """Legacy request model."""

    url: str


def _resolve_download_path(path_value: str) -> Path:
    candidate = Path(path_value).expanduser().resolve()
    downloads_root = Path(settings.downloads_dir).expanduser().resolve()
    if downloads_root not in candidate.parents and candidate != downloads_root:
        raise HTTPException(status_code=400, detail="File path is outside downloads directory")
    return candidate


def _fetch_preview_info(url: str) -> Dict[str, Any]:
    ydl = YoutubeDL({**_base_ydl_params(), "skip_download": True, "noplaylist": True})
    info = ydl.extract_info(url, download=False)
    if not isinstance(info, dict):
        raise ValueError("Unable to fetch preview metadata")
    return info


def _format_resolution(fmt: Dict[str, Any]) -> Optional[str]:
    if fmt.get("resolution"):
        return fmt.get("resolution")
    width = fmt.get("width")
    height = fmt.get("height")
    if width and height:
        return f"{width}x{height}"
    return None


def _build_format_options(info: Dict[str, Any]) -> List[DownloadFormatOption]:
    formats = info.get("formats") or []
    options: List[DownloadFormatOption] = []
    for fmt in formats:
        if not isinstance(fmt, dict):
            continue
        format_id = fmt.get("format_id")
        if not format_id:
            continue
        vcodec = fmt.get("vcodec")
        acodec = fmt.get("acodec")
        has_video = bool(vcodec and vcodec != "none")
        has_audio = bool(acodec and acodec != "none")
        options.append(
            DownloadFormatOption(
                format_id=str(format_id),
                ext=fmt.get("ext"),
                resolution=_format_resolution(fmt),
                width=fmt.get("width"),
                height=fmt.get("height"),
                fps=fmt.get("fps"),
                filesize=fmt.get("filesize"),
                filesize_approx=fmt.get("filesize_approx"),
                vcodec=vcodec,
                acodec=acodec,
                format_note=fmt.get("format_note"),
                tbr=fmt.get("tbr"),
                audio_channels=fmt.get("audio_channels"),
                has_audio=has_audio,
                has_video=has_video,
            )
        )
    return options


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="QueueTube Whisper Transcriber", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/settings", response_model=SettingsResponse)
    def read_settings() -> SettingsResponse:
        cookies_path = settings.ytdlp_cookies_file
        cookies_configured = bool(cookies_path and Path(cookies_path).exists())
        return SettingsResponse(
            cookies_configured=cookies_configured,
            cookies_path=cookies_path,
        )

    @app.post("/preview", response_model=PreviewResponse)
    def preview_formats(payload: PreviewRequest) -> PreviewResponse:
        try:
            info = _fetch_preview_info(payload.url)
        except Exception as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

        if info.get("entries"):
            raise HTTPException(
                status_code=400,
                detail="Format preview is only supported for single video URLs.",
            )

        formats = _build_format_options(info)
        return PreviewResponse(
            title=info.get("title"),
            uploader=info.get("uploader"),
            duration=info.get("duration"),
            webpage_url=info.get("webpage_url"),
            thumbnail=info.get("thumbnail"),
            formats=formats,
        )

    @app.post("/jobs", response_model=BatchCreateResponse, status_code=202)
    def create_jobs(request: JobCreateRequest, session: Session = Depends(get_session)) -> BatchCreateResponse:
        batch = create_batch(session, request.url)
        session.commit()
        enqueue_url.delay(batch.id, request.url, request.format_id)
        return BatchCreateResponse(batch_id=batch.id, message="Queued for processing")

    @app.post("/download_url", response_model=BatchCreateResponse, status_code=202)
    def legacy_download_url(payload: YouTubeURL, session: Session = Depends(get_session)) -> BatchCreateResponse:
        batch = create_batch(session, payload.url)
        session.commit()
        enqueue_url.delay(batch.id, payload.url, None)
        return BatchCreateResponse(batch_id=batch.id, message="Channel download started")

    @app.post("/process_untranscribed_videos", status_code=202)
    def legacy_process_untranscribed() -> dict:
        process_untranscribed_videos.delay(settings.downloads_dir)
        return {"message": "Processing untranscribed videos started"}

    @app.get("/jobs", response_model=JobListResponse)
    def list_jobs(
        status: Optional[JobStatus] = Query(default=None),
        batch_id: Optional[str] = Query(default=None),
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        session: Session = Depends(get_session),
    ) -> JobListResponse:
        stmt = select(Job)
        count_stmt = select(func.count()).select_from(Job)
        if status:
            stmt = stmt.where(Job.status == status)
            count_stmt = count_stmt.where(Job.status == status)
        if batch_id:
            stmt = stmt.where(Job.batch_id == batch_id)
            count_stmt = count_stmt.where(Job.batch_id == batch_id)

        total = session.scalar(count_stmt) or 0
        jobs = session.scalars(stmt.order_by(Job.created_at.desc()).limit(limit).offset(offset)).all()
        return JobListResponse(jobs=jobs, total=total)

    @app.get("/jobs/{job_id}", response_model=JobResponse)
    def get_job(job_id: str, session: Session = Depends(get_session)) -> JobResponse:
        job = session.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job

    @app.delete("/jobs/{job_id}", response_model=DeleteJobResponse)
    def delete_job(
        job_id: str,
        purge_files: bool = Query(default=False),
        session: Session = Depends(get_session),
    ) -> DeleteJobResponse:
        job = session.get(Job, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        if job.status in {JobStatus.downloading, JobStatus.transcribing}:
            raise HTTPException(status_code=409, detail="Cannot delete an active job")

        if purge_files:
            for path_value in (job.download_path, job.transcript_path):
                if not path_value:
                    continue
                candidate = _resolve_download_path(path_value)
                if candidate.exists():
                    candidate.unlink()

        batch_id = job.batch_id
        session.execute(delete(JobEvent).where(JobEvent.job_id == job_id))
        session.delete(job)
        session.flush()
        if batch_id:
            update_batch_status(session, batch_id)
        session.commit()
        return DeleteJobResponse(job_id=job_id, message="Job removed")

    @app.get("/jobs/{job_id}/events", response_model=List[JobEventResponse])
    def get_job_events(job_id: str, session: Session = Depends(get_session)) -> List[JobEventResponse]:
        events = session.scalars(
            select(JobEvent).where(JobEvent.job_id == job_id).order_by(JobEvent.created_at.asc())
        ).all()
        return events

    @app.get("/jobs/{job_id}/media")
    def get_job_media(job_id: str, session: Session = Depends(get_session)) -> FileResponse:
        job = session.get(Job, job_id)
        if not job or not job.download_path:
            raise HTTPException(status_code=404, detail="Media file not found")

        media_path = _resolve_download_path(job.download_path)
        if not media_path.exists():
            raise HTTPException(status_code=404, detail="Media file not found")

        media_type, _ = mimetypes.guess_type(media_path.name)
        return FileResponse(
            media_path,
            media_type=media_type or "application/octet-stream",
            filename=media_path.name,
        )

    @app.get("/jobs/{job_id}/transcript")
    def get_job_transcript(job_id: str, session: Session = Depends(get_session)) -> PlainTextResponse:
        job = session.get(Job, job_id)
        if not job or not job.transcript_path:
            raise HTTPException(status_code=404, detail="Transcript not found")

        transcript_path = _resolve_download_path(job.transcript_path)
        if not transcript_path.exists():
            raise HTTPException(status_code=404, detail="Transcript not found")

        transcript_text = transcript_path.read_text(encoding="utf-8", errors="ignore")
        return PlainTextResponse(transcript_text)

    @app.get("/batches", response_model=List[BatchResponse])
    def list_batches(
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        session: Session = Depends(get_session),
    ) -> List[BatchResponse]:
        batches = session.scalars(
            select(Batch).order_by(Batch.created_at.desc()).limit(limit).offset(offset)
        ).all()
        return batches

    @app.get("/batches/{batch_id}", response_model=BatchDetailResponse)
    def get_batch(batch_id: str, session: Session = Depends(get_session)) -> BatchDetailResponse:
        batch = session.get(Batch, batch_id)
        if not batch:
            raise HTTPException(status_code=404, detail="Batch not found")
        jobs = session.scalars(select(Job).where(Job.batch_id == batch_id)).all()
        return BatchDetailResponse(batch=batch, jobs=jobs, total=len(jobs))

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
