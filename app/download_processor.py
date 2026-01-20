"""Download and enqueue YouTube videos."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from celery.signals import worker_process_init
from celery.utils.log import get_task_logger
from yt_dlp import YoutubeDL

from app.celery_app import celery_app
from app.config import get_settings
from app import db
from app.models import BatchStatus, Job, JobStatus
from app.services.jobs import (
    add_job_event,
    create_job,
    set_batch_status,
    update_batch_status,
    update_job_status,
)

logger = get_task_logger(__name__)
settings = get_settings()

INFO_YDL: Optional[YoutubeDL] = None


class DownloadProcessorLogger:
    def debug(self, msg):
        if msg.startswith("[debug] "):
            logger.debug(msg)
        else:
            self.info(msg)

    def info(self, msg):
        logger.info(msg)

    def warning(self, msg):
        logger.warning(msg)

    def error(self, msg):
        logger.error(msg)


def _base_ydl_params() -> Dict[str, Any]:
    params: Dict[str, Any] = {
        "logger": DownloadProcessorLogger(),
        "format": "best",
        "noplaylist": True,
        "js_runtimes": {"deno": {"path": "/usr/local/deno/bin/deno"}},
        "remote_components": ["ejs:github"],
        "extractor_retries": 3,
        "fragment_retries": 3,
        "retries": 3,
        "sleep_interval": 1,
        "max_sleep_interval": 5,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        },
        "socket_timeout": 30,
        "ignoreerrors": False,
        "no_warnings": False,
    }
    if settings.ytdlp_cookies_file:
        params["cookiefile"] = settings.ytdlp_cookies_file
    return params


@worker_process_init.connect
def init_worker_processes(**kwargs) -> None:
    """Initialize shared YoutubeDL instance per worker process."""
    global INFO_YDL
    logger.info("init download processor")
    info_params = {**_base_ydl_params(), "skip_download": True, "noplaylist": False}
    INFO_YDL = YoutubeDL(info_params)


def extract_yt_info(yt_url: str) -> Dict[str, Any]:
    """Get metadata from a YouTube URL."""
    if INFO_YDL is None:
        raise RuntimeError("YoutubeDL is not initialized")

    logger.info('Getting info for URL "%s"', yt_url)
    yt_info = INFO_YDL.extract_info(yt_url, download=False, process=True)
    if not isinstance(yt_info, dict):
        raise ValueError("Unknown type of yt_info")
    return yt_info


def _safe_entries(info: Dict[str, Any]) -> List[Dict[str, Any]]:
    entries = info.get("entries")
    if not entries:
        return []
    return [entry for entry in entries if isinstance(entry, dict)]


def _create_output_dir(uploader: str) -> Path:
    base = Path(settings.downloads_dir)
    target = base / uploader
    target.mkdir(parents=True, exist_ok=True)
    return target


@celery_app.task(name="app.download_processor.enqueue_url")
def enqueue_url(batch_id: str, url: str, requested_format: Optional[str] = None) -> None:
    """Resolve a URL into one or more jobs and enqueue downloads."""
    logger.info("Enqueueing URL %s", url)
    try:
        yt_info = extract_yt_info(url)
    except Exception as exc:
        logger.error("Failed to extract info for %s: %s", url, exc)
        with db.SessionLocal() as session:
            set_batch_status(session, batch_id, status=BatchStatus.failed)
            session.commit()
        raise

    with db.SessionLocal() as session:
        if "entries" in yt_info:
            uploader = yt_info.get("uploader", "Unknown")
            output_dir = _create_output_dir(uploader)
            for entry in _safe_entries(yt_info):
                video_id = entry.get("id")
                title = entry.get("title")
                video_url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None
                job = create_job(
                    session,
                    source_url=url,
                    batch_id=batch_id,
                    video_url=video_url,
                    video_id=video_id,
                    title=title,
                    uploader=uploader,
                    requested_format=requested_format,
                )
                add_job_event(session, job.id, "queued", "Queued for download", 0.0)
                session.commit()
                if video_url:
                    download_video.apply_async(
                        args=[job.id, video_url, str(output_dir)], queue="download_queue"
                    )
        else:
            video_id = yt_info.get("id")
            uploader = yt_info.get("uploader", "Unknown")
            title = yt_info.get("title")
            output_dir = _create_output_dir(uploader)
            job = create_job(
                session,
                source_url=url,
                batch_id=batch_id,
                video_url=url,
                video_id=video_id,
                title=title,
                uploader=uploader,
                requested_format=requested_format,
            )
            add_job_event(session, job.id, "queued", "Queued for download", 0.0)
            session.commit()
            download_video.apply_async(
                args=[job.id, url, str(output_dir)], queue="download_queue"
            )

        update_batch_status(session, batch_id)
        session.commit()


@celery_app.task(bind=True, name="app.download_processor.download_video")
def download_video(self, job_id: str, url: str, output_dir: str) -> None:
    """Download a video and enqueue transcription."""
    logger.info("Downloading %s to %s", url, output_dir)
    with db.SessionLocal() as session:
        job = session.get(Job, job_id)
        if not job:
            logger.error("Job %s not found", job_id)
            return

        update_job_status(session, job, JobStatus.downloading, progress=0.0)
        add_job_event(session, job.id, "downloading", "Download started", 0.0)
        session.commit()

        last_progress = 0.0

        def progress_hook(data: Dict[str, Any]) -> None:
            nonlocal last_progress
            if data.get("status") == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate")
                downloaded = data.get("downloaded_bytes")
                if total and downloaded:
                    pct = (downloaded / total) * 100
                    overall = min(50.0, pct * 0.5)
                    if overall - last_progress >= 1.0:
                        job.progress = overall
                        job.updated_at = datetime.utcnow()
                        session.add(job)
                        session.commit()
                        last_progress = overall
            elif data.get("status") == "finished":
                filename = data.get("filename")
                if filename:
                    update_job_status(
                        session,
                        job,
                        JobStatus.downloaded,
                        progress=50.0,
                        download_path=filename,
                    )
                    add_job_event(session, job.id, "downloaded", "Download finished", 50.0)
                    session.commit()

        format_id = job.requested_format or "best"
        ydl = YoutubeDL(
            {
                **_base_ydl_params(),
                "format": format_id,
                "outtmpl": f"{output_dir}/%(title).200B-%(id)s.%(ext)s",
                "progress_hooks": [progress_hook],
            }
        )

        try:
            ydl.download([url])
        except Exception as exc:
            logger.error("Failed to download %s: %s", url, exc)
            update_job_status(session, job, JobStatus.failed, error=str(exc))
            add_job_event(session, job.id, "failed", f"Download failed: {exc}")
            session.commit()
            if job.batch_id:
                update_batch_status(session, job.batch_id)
                session.commit()
            return

        from app.transcription_processor import transcribe_video

        transcribe_video.apply_async(args=[job.id], queue="transcription_queue")
