"""Download all videos from a given YouTube channel."""
from __future__ import annotations

import json
from pathlib import Path

from yt_dlp import YoutubeDL

# note /videos is not /shorts and the channel can return page entries with links to both

VOL_DL_PATH = "downloads"


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


def get_yt_info(yt_url: str) -> dict[str, str]:
    """Get channel info from a given channel url."""
    with YoutubeDL() as ydl:
        yt_info = ydl.extract_info(yt_url, download=False, process=True)

        if not isinstance(yt_info, dict):
            raise ValueError("Unknown type of yt_info")

        return yt_info


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
            download_video(f"https://www.youtube.com/watch?v={vid_id}", path)
        except ValueError as err:
            print(f"Error {err} occurred while downloading video {vid_id}, skipping.")


def get_youtube_url(url: str) -> None:
    yt_info = get_yt_info(url)
    dl_path = create_folder(yt_info["uploader"])

    save_yt_info_to_file(yt_info, dl_path, filename=yt_info["id"])
    video_ids = get_video_ids(yt_info)
    download_videos(video_ids, dl_path)


def main() -> None:
    """Main function."""
    get_youtube_url("https://www.youtube.com/@sigriduk3072/videos")


if __name__ == "__main__":
    main()
