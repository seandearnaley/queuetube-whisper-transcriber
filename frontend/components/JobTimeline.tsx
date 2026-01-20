import type { JobEvent } from "@/lib/types";

interface JobTimelineProps {
  events: JobEvent[];
}

export function JobTimeline({ events }: JobTimelineProps) {
  if (!events.length) {
    return (
      <div className="timeline-empty">
        <p>No events yet. Once a job starts, updates appear here.</p>
      </div>
    );
  }

  return (
    <div className="timeline">
      {events.map((event) => (
        <div key={event.id} className="timeline-item">
          <div className="timeline-dot" />
          <div className="timeline-content">
            <div className="timeline-row">
              <span className="timeline-type">{event.event_type}</span>
              <span className="timeline-time">
                {new Date(event.created_at).toLocaleString()}
              </span>
            </div>
            <p className="timeline-message">{event.message}</p>
            {event.progress !== null && (
              <span className="timeline-progress">{Math.round(event.progress)}%</span>
            )}
          </div>
        </div>
      ))}
    </div>
  );
}
