"""Download all videos from a given YouTube channel."""
from __future__ import annotations

from pathlib import Path
from typing import List

from yt_dlp import YoutubeDL

CHANNEL_URL = "https://www.youtube.com/@tobiasfischer1879"
DL_PATH = "downloads"


def download_video(url: str, path: Path) -> None:
    """Download a video from a given url to a given path."""
    print(f"Downloading video from {url} to {path}")

    ydl_opts = {
        "outtmpl": str(path / "%(title)s.%(ext)s"),
        "format": "mp4/best",
        "noplaylist": True,
    }

    with YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])


def get_channel_info(yt_url: str) -> dict:
    """Get channel info from a given channel url."""
    with YoutubeDL() as ydl:
        channel_info = ydl.extract_info(yt_url, download=False, process=True)

        if not isinstance(channel_info, dict):
            raise ValueError("Unknown type of channel_info")

        return channel_info


def get_channel_video_ids(channel_info: dict) -> List[str]:
    """Extract video ids from channel info."""
    if "entries" not in channel_info:
        raise ValueError("No videos found in the channel")

    return [entry["id"] for entry in channel_info["entries"]]


def download_channel_videos(channel_video_ids: List[str], dl_path: Path) -> None:
    """Download all videos from a list of video ids."""
    dl_path.mkdir(parents=True, exist_ok=True)

    for vid_id in channel_video_ids:
        try:
            download_video(f"https://www.youtube.com/watch?v={vid_id}", dl_path)
        except ValueError as err:
            print(f"Error {err} occurred while downloading video {vid_id}, skipping.")


def main() -> None:
    """Main function."""
    channel_info = get_channel_info(CHANNEL_URL)
    channel_video_ids = get_channel_video_ids(channel_info)
    download_channel_videos(channel_video_ids, Path(DL_PATH + "/" + channel_info["id"]))


if __name__ == "__main__":
    main()
