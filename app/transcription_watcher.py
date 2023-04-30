from pathlib import Path
from typing import List

from celery import Celery

from app.whispercc import WhisperTranscriber

app = Celery("transcription_watcher", broker="redis://redis:6379/0")
transcriber = WhisperTranscriber("small.en")


def find_untranscribed_videos(directory: Path) -> List[Path]:
    """
    Find all mp4 files in the given directory that don't have a corresponding txt file.

    Args:
        directory: The directory to search for untranscribed videos.

    Returns:
        A list of untranscribed video file paths.
    """
    untranscribed_videos = []
    for video_path in directory.glob("**/*.mp4"):
        print(f"Checking {video_path}")
        txt_path = video_path.with_name(video_path.name + ".txt")
        print(f"Checking txtpath: {txt_path}")
        if not txt_path.exists():
            untranscribed_videos.append(video_path)
    return untranscribed_videos


@app.task
def transcribe_video(video_path: str) -> None:
    """
    Transcribe the given video file and save the transcription to a txt file.

    Args:
        video_path: The path of the video file to transcribe.
    """
    transcription = transcriber.transcribe_audio(Path(video_path))
    with open(video_path + ".txt", "w") as f:
        f.write(transcription)


def process_untranscribed_videos(directory: str) -> None:
    """
    Find untranscribed videos in the given directory and add them to the Celery queue.

    Args:
        directory: The directory to search for untranscribed videos.
    """
    untranscribed_videos = find_untranscribed_videos(Path(directory))
    print(f"Found {len(untranscribed_videos)} untranscribed videos")
    for video_path in untranscribed_videos:
        transcribe_video.delay(str(video_path))


if __name__ == "__main__":
    process_untranscribed_videos("downloads")
