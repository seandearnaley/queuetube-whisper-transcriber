"""Download all videos from a given channel"""
import os
import tempfile
from typing import List

from pytube import Channel, YouTube, helpers
from tenacity import retry, stop_after_attempt, wait_fixed

CHANNEL_URL = "https://www.youtube.com/c/SabineHossenfelder"
DL_PATH = "downloads"
TEMP_EXTENSION = ".temp"
downloaded_videos: List[str] = []


@retry(wait=wait_fixed(60), stop=stop_after_attempt(3))
def download_video(url: str, path: str) -> None:
    """Download a video from a given url to a given path"""
    print(f"Downloading video from {url} to {path}")
    youtube = YouTube(url)
    video = youtube.streams.filter(progressive=True, file_extension="mp4").first()
    if video is None:
        return

    # Download to a temp file
    with tempfile.NamedTemporaryFile(
        dir=path, suffix=TEMP_EXTENSION, delete=False
    ) as temp_file:
        temp_path = temp_file.name
        video.download(output_path=path, filename=temp_file.name)

    # Rename the temp file back to its original filename
    final_filename = video.default_filename
    final_path = os.path.join(path, final_filename)
    os.rename(temp_path, final_path)
    downloaded_videos.append(url)


def get_channel_videos(yt_url: str) -> helpers.DeferredGeneratorList:
    """Get all videos from a given channel url"""
    channel = Channel(yt_url)
    print(f"Found {len(channel.video_urls)} videos")

    return channel.video_urls


def main() -> None:
    """Main function"""
    channel_video_urls = get_channel_videos(CHANNEL_URL)
    for url in channel_video_urls:
        download_video(url, DL_PATH)


if __name__ == "__main__":
    main()
