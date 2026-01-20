import type { Job } from "@/lib/types";

interface JobCardProps {
  job: Job;
  isActive: boolean;
  onSelect: (jobId: string) => void;
  onRemove?: (jobId: string) => void;
}

function formatTitle(job: Job) {
  if (job.title) return job.title;
  if (job.video_id) return `Video ${job.video_id}`;
  return job.source_url;
}

function formatSubtitle(job: Job) {
  if (job.uploader) return job.uploader;
  if (job.video_url) return job.video_url;
  return job.source_url;
}

export function JobCard({ job, isActive, onSelect, onRemove }: JobCardProps) {
  const canRemove = Boolean(onRemove && job.status === "failed");

  return (
    <div
      role="button"
      tabIndex={0}
      className={`job-card ${isActive ? "active" : ""}`}
      onClick={() => onSelect(job.id)}
      onKeyDown={(event) => {
        if (event.key === "Enter" || event.key === " ") {
          event.preventDefault();
          onSelect(job.id);
        }
      }}
    >
      <div className="job-card__header">
        <span className={`status-pill status-${job.status}`}>{job.status}</span>
        <div className="job-card__actions">
          <span className="job-meta">{new Date(job.created_at).toLocaleString()}</span>
          {canRemove && (
            <button
              type="button"
              className="job-remove"
              onClick={(event) => {
                event.stopPropagation();
                onRemove?.(job.id);
              }}
            >
              Remove
            </button>
          )}
        </div>
      </div>
      <div className="job-title">{formatTitle(job)}</div>
      <div className="job-subtitle">{formatSubtitle(job)}</div>
      <div className="job-progress">
        <div className="job-progress__bar" style={{ width: `${job.progress}%` }} />
      </div>
      <div className="job-progress__meta">
        <span>{Math.round(job.progress)}%</span>
        <span>{job.batch_id ? `Batch ${job.batch_id.slice(0, 8)}` : "Single"}</span>
      </div>
    </div>
  );
}
