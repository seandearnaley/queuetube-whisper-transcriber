""" FastAPI server for downloading YouTube channels """
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.download_processor import get_youtube_url
from app.transcription_processor import process_untranscribed_videos

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logging.basicConfig(filename="thread_output.log", level=logging.INFO)

# TODO: change this
DL_PATH = "downloads"


class YouTubeURL(BaseModel):
    """Channel URL model."""

    url: str


@app.post("/download_url")
async def download_url(url: YouTubeURL):
    """Download all videos from a given YouTube URL."""
    print("hello")
    get_youtube_url.delay(url.url)

    return {"message": "Channel download started"}


@app.post("/process_untranscribed_videos")
async def process_videos():
    """Process untranscribed videos in the specified directory."""
    process_untranscribed_videos.delay(DL_PATH)
    return {"message": "Processing untranscribed videos started"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
