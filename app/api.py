""" FastAPI server for downloading YouTube channels """
import logging
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from app.transcription_watcher import process_untranscribed_videos
from app.yt_channel_dl import (
    download_channel_videos,
    get_channel_info,
    get_channel_video_ids,
)

app = FastAPI()

logging.basicConfig(filename="thread_output.log", level=logging.INFO)

# TODO: change this
DL_PATH = "downloads"


class ChannelURL(BaseModel):
    """Channel URL model."""

    url: str


@app.post("/download_channel")
async def download_channel(channel_url: ChannelURL):
    """Download all videos from a given YouTube channel."""
    channel_info = get_channel_info(channel_url.url)
    channel_video_ids = get_channel_video_ids(channel_info)
    download_channel_videos(channel_video_ids, Path(DL_PATH + "/" + channel_info["id"]))

    return {"message": "Channel download started"}


@app.post("/process_untranscribed_videos")
async def process_videos():
    """Process untranscribed videos in the specified directory."""
    process_untranscribed_videos(DL_PATH)
    return {"message": "Processing untranscribed videos started"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
