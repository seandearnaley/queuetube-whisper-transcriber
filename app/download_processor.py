"""Download all videos from a given YouTube channel."""
from __future__ import annotations

import json
from pathlib import Path

from celery import Celery
from celery.signals import worker_process_init
from celery.utils.log import get_task_logger
from yt_dlp import YoutubeDL

logger = get_task_logger(__name__)

app = Celery(
    "download_queue",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    task_routes={"app.download_processor.*": {"queue": "download_queue"}},
)


# note /videos is not /shorts and the channel can return page entries with links to both

DOWNLOAD_PATH = "downloads"


class DownloadProcessorLogger:
    def debug(self, msg):
        # For compatibility with youtube-dl, both debug and info are passed into debug
        # You can distinguish them by the prefix '[debug] '
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


@worker_process_init.connect
def init_worker_processes(**kwargs) -> None:
    """
    Initialize the worker processes.
    We do this because we want to initialize the YoutubeDL instance
    only once per worker process.
    """
    logger.info("init download processor")

    ydl = YoutubeDL(
        {
            "logger": DownloadProcessorLogger(),
            "outtmpl": f"{DOWNLOAD_PATH}/%(title)s.%(ext)s",
            "format": "mp4/best",
            "noplaylist": True,
        }
    )
    download_video.ydl = ydl
    get_yt_info.ydl = ydl


@app.task(bind=True)
def download_video(self, url: str, path: str) -> None:
    """Download a video from a given url to a given path."""
    logger.info(f"Downloading video from {url} to {path}")
    self.ydl.download([url])


def extract_yt_info(ydl: YoutubeDL, yt_url: str) -> dict[str, str]:
    """Get channel info from a given channel url."""
    logger.info('Getting info for channel "%s"' % yt_url)
    yt_info = ydl.extract_info(yt_url, download=False, process=True)

    if not isinstance(yt_info, dict):
        raise ValueError("Unknown type of yt_info")

    return yt_info


@app.task(bind=True)
def get_yt_info(self, yt_url: str) -> dict[str, str]:
    """Get channel info from a given channel url."""
    return extract_yt_info(self.ydl, yt_url)


def get_video_ids(info: dict) -> list[str]:
    """Extract video ids from youtube dict info."""
    if "entries" in info:
        return [entry["id"] for entry in info["entries"]]
    elif "id" in info:
        return [info["id"]]
    else:
        raise ValueError("No videos found in the channel")


def create_folder(name: str) -> Path:
    """Create a folder."""
    folder = Path(f"{DOWNLOAD_PATH}/{name}")
    folder.mkdir(parents=True, exist_ok=True)

    return folder


def save_yt_info_to_file(yt_info: dict, path: Path, filename: str) -> None:
    """Save youtube info dict to file."""
    with open(f"{path}/{filename}.info.json", "w") as f:
        json.dump(
            yt_info, f, indent=4
        )  # Beautify the JSON output with 4 spaces indentation.


def download_videos(video_ids: list[str], path: Path) -> None:
    """Download videos from a given list of video ids."""
    for vid_id in video_ids:
        try:
            download_video.delay(f"https://www.youtube.com/watch?v={vid_id}", str(path))
        except ValueError as err:
            logger.info(
                f"Error {err} occurred while downloading video {vid_id}, skipping."
            )


@app.task
def get_youtube_url(url: str) -> None:
    logger.info(f"Downloading channel from {url}")
    yt_info = extract_yt_info(
        get_yt_info.ydl, url
    )  # Call the new function with the ydl instance
    logger.info('Got info for channel "%s"' % yt_info["uploader"])
    dl_path = create_folder(yt_info["uploader"])

    save_yt_info_to_file(yt_info, dl_path, filename=yt_info["id"])
    video_ids = get_video_ids(yt_info)
    download_videos(video_ids, dl_path)


if __name__ == "__main__":
    get_youtube_url("https://www.youtube.com/@sigriduk3072/videos")
