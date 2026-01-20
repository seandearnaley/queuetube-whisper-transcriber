export type JobStatus =
  | "queued"
  | "downloading"
  | "downloaded"
  | "transcribing"
  | "completed"
  | "failed"
  | "canceled";

export interface Job {
  id: string;
  batch_id: string | null;
  source_url: string;
  video_url: string | null;
  video_id: string | null;
  title: string | null;
  uploader: string | null;
  requested_format: string | null;
  status: JobStatus;
  progress: number;
  download_path: string | null;
  transcript_path: string | null;
  error: string | null;
  created_at: string;
  updated_at: string;
  started_at: string | null;
  finished_at: string | null;
}

export interface JobEvent {
  id: number;
  job_id: string;
  event_type: string;
  message: string;
  progress: number | null;
  created_at: string;
}

export interface JobListResponse {
  jobs: Job[];
  total: number;
}

export interface SettingsResponse {
  cookies_configured: boolean;
  cookies_path: string | null;
}

export interface DownloadFormatOption {
  format_id: string;
  ext: string | null;
  resolution: string | null;
  width: number | null;
  height: number | null;
  fps: number | null;
  filesize: number | null;
  filesize_approx: number | null;
  vcodec: string | null;
  acodec: string | null;
  format_note: string | null;
  tbr: number | null;
  audio_channels: number | null;
  has_audio: boolean;
  has_video: boolean;
}

export interface PreviewResponse {
  title: string | null;
  uploader: string | null;
  duration: number | null;
  webpage_url: string | null;
  thumbnail: string | null;
  formats: DownloadFormatOption[];
}
