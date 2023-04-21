"""Download all videos from a given channel"""
from typing import List

from pytube import Channel, YouTube

CHANNEL_URL = "https://www.youtube.com/c/SabineHossenfelder"
DL_PATH = "downloads"
downloaded_videos: List[str] = []


def download_video(url: str, path: str) -> None:
    """Download a video from a given url to a given path"""
    print(f"Downloading video from {url} to {path}")
    youtube = YouTube(url)
    video = youtube.streams.filter(progressive=True, file_extension="mp4").first()
    if video is None:
        return
    video.download(output_path=path)
    downloaded_videos.append(url)


def get_channel_videos(yt_url: str) -> None:
    """Get all videos from a given channel url"""
    channel = Channel(yt_url)
    print(f"Found {len(channel.video_urls)} videos")
    for url in channel.video_urls:
        download_video(url, DL_PATH)


if __name__ == "__main__":
    get_channel_videos(CHANNEL_URL)
