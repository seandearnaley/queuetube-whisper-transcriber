"""Download all videos from a given YouTube channel."""
from __future__ import annotations

import json
from pathlib import Path

from celery import Celery
from celery.signals import worker_process_init
from yt_dlp import YoutubeDL

app = Celery(
    "download_queue",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    task_routes={"app.download_processor.*": {"queue": "download_queue"}},
)


# note /videos is not /shorts and the channel can return page entries with links to both

VOL_DL_PATH = "downloads"


@worker_process_init.connect
def init_worker_processes(**kwargs):
    print("init download processor")
    init_download_video()
    init_get_yt_info()


def init_download_video():
    task = download_video

    download_options = {
        "outtmpl": "downloads/%(title)s.%(ext)s",
        "format": "mp4/best",
        "noplaylist": True,
    }

    task.ydl = YoutubeDL(download_options)


def init_get_yt_info():
    task = get_yt_info
    task.ydl = YoutubeDL()


@app.task(bind=True)
def download_video(self, url: str, path: str) -> None:
    """Download a video from a given url to a given path."""
    print(f"Downloading video from {url} to {path}")
    self.ydl.download([url])


def extract_yt_info(ydl: YoutubeDL, yt_url: str) -> dict[str, str]:
    """Get channel info from a given channel url."""
    print('Getting info for channel "%s"' % yt_url)
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
    folder = Path(f"{VOL_DL_PATH}/{name}")
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
            print(f"Error {err} occurred while downloading video {vid_id}, skipping.")


@app.task
def get_youtube_url(url: str) -> None:
    print(f"Downloading channel from {url}")
    yt_info = extract_yt_info(
        get_yt_info.ydl, url
    )  # Call the new function with the ydl instance
    print('Got info for channel "%s"' % yt_info["uploader"])
    dl_path = create_folder(yt_info["uploader"])

    save_yt_info_to_file(yt_info, dl_path, filename=yt_info["id"])
    video_ids = get_video_ids(yt_info)
    download_videos(video_ids, dl_path)


if __name__ == "__main__":
    get_youtube_url("https://www.youtube.com/@sigriduk3072/videos")
