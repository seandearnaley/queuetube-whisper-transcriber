import type {
  JobEvent,
  JobListResponse,
  PreviewResponse,
  SettingsResponse
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }
  return (await response.json()) as T;
}

export async function createJobs(
  url: string,
  formatId?: string | null
): Promise<{ batch_id: string; message: string }> {
  const response = await fetch(`${API_BASE}/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, format_id: formatId ?? undefined })
  });
  return handleResponse(response);
}

export async function fetchJobs(): Promise<JobListResponse> {
  const response = await fetch(`${API_BASE}/jobs?limit=100`);
  return handleResponse(response);
}

export async function fetchJobEvents(jobId: string): Promise<JobEvent[]> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}/events`);
  return handleResponse(response);
}

export async function fetchSettings(): Promise<SettingsResponse> {
  const response = await fetch(`${API_BASE}/settings`);
  return handleResponse(response);
}

export async function previewFormats(url: string): Promise<PreviewResponse> {
  const response = await fetch(`${API_BASE}/preview`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
  });
  return handleResponse(response);
}

export async function deleteJob(jobId: string): Promise<{ job_id: string; message: string }> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}`, { method: "DELETE" });
  return handleResponse(response);
}

export async function fetchTranscript(jobId: string): Promise<string> {
  const response = await fetch(`${API_BASE}/jobs/${jobId}/transcript`);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text || `Request failed with ${response.status}`);
  }
  return response.text();
}

export function getMediaUrl(jobId: string): string {
  return `${API_BASE}/jobs/${jobId}/media`;
}

export function getTranscriptUrl(jobId: string): string {
  return `${API_BASE}/jobs/${jobId}/transcript`;
}
