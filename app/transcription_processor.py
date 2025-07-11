from pathlib import Path
from typing import List

from celery import Celery
from celery.signals import worker_process_init
from celery.utils.log import get_task_logger

from app.whisper_transcriber import WhisperTranscriber

logger = get_task_logger(__name__)

app = Celery(
    "transcription_queue",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
    task_routes={"app.transcription_processor.*": {"queue": "transcription_queue"}},
)


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
        txt_path = video_path.with_name(video_path.name + ".txt")
        if not txt_path.exists():
            untranscribed_videos.append(video_path)
    return untranscribed_videos


@worker_process_init.connect
def init_transcriber(**kwargs):
    transcribe_video.transcriber = WhisperTranscriber("tiny.en")


@app.task(bind=True)
def transcribe_video(self, video_path: str) -> None:
    """
    Transcribe the given video file and save the transcription to a txt file.

    bind=True allows the transcribe_video task to access its own attributes and methods.
    This is useful because it enables you to store the transcriber instance as an
    attribute of the transcribe_video task, instead of using a global variable.

    Args:
        video_path: The path of the video file to transcribe.
    """
    logger.info(f"Transcribing {video_path}")
    transcription = self.transcriber.transcribe_audio(Path(video_path))
    file_path = video_path + ".txt"
    with open(file_path, "w") as f:
        f.write(transcription)
        logger.info(f"Saved transcription to {file_path}")


@app.task
def process_untranscribed_videos(directory: str) -> None:
    """
    Find untranscribed videos in the given directory and add them to the Celery queue.

    Args:
        directory: The directory to search for untranscribed videos.
    """
    untranscribed_videos = find_untranscribed_videos(Path(directory))
    logger.info(f"Found {len(untranscribed_videos)} untranscribed videos")
    for video_path in untranscribed_videos:
        # Explicitly route to the transcription_queue
        transcribe_video.apply_async(
            args=[str(video_path)], queue="transcription_queue"
        )
        logger.info(f"Queued transcription for {video_path}")


if __name__ == "__main__":
    process_untranscribed_videos("downloads")
