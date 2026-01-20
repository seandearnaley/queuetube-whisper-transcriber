from __future__ import annotations

from app.models import Batch


def test_create_jobs_enqueues_batch(client, db_session, monkeypatch):
    calls = []

    def fake_delay_with_format(batch_id, url, format_id):
        calls.append((batch_id, url, format_id))

    monkeypatch.setattr("app.api.enqueue_url.delay", fake_delay_with_format)

    response = client.post("/jobs", json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"})
    assert response.status_code == 202

    payload = response.json()
    assert "batch_id" in payload
    assert payload["message"]

    batch = db_session.get(Batch, payload["batch_id"])
    assert batch is not None
    assert batch.source_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

    assert calls
    assert calls[0][0] == payload["batch_id"]
    assert calls[0][1] == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    assert calls[0][2] is None


def test_get_job_not_found(client):
    response = client.get("/jobs/does-not-exist")
    assert response.status_code == 404


def test_delete_job_removes_failed_job(client, db_session):
    from app.models import Job, JobStatus

    job = Job(source_url="https://example.com", status=JobStatus.failed, progress=0.0)
    db_session.add(job)
    db_session.commit()
    job_id = job.id

    response = client.delete(f"/jobs/{job_id}")
    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == job_id

    db_session.expire_all()
    assert db_session.get(Job, job_id) is None


def test_delete_job_active_conflict(client, db_session):
    from app.models import Job, JobStatus

    job = Job(source_url="https://example.com", status=JobStatus.downloading, progress=10.0)
    db_session.add(job)
    db_session.commit()

    response = client.delete(f"/jobs/{job.id}")
    assert response.status_code == 409


def test_preview_formats_returns_payload(client, monkeypatch):
    def fake_preview(url):
        assert url == "https://example.com/video"
        return {
            "title": "Test",
            "uploader": "Uploader",
            "duration": 120,
            "webpage_url": url,
            "thumbnail": "https://example.com/thumb.jpg",
            "formats": [
                {
                    "format_id": "18",
                    "ext": "mp4",
                    "resolution": "640x360",
                    "width": 640,
                    "height": 360,
                    "vcodec": "avc1",
                    "acodec": "mp4a",
                    "filesize": 1234,
                }
            ],
        }

    monkeypatch.setattr("app.api._fetch_preview_info", fake_preview)

    response = client.post("/preview", json={"url": "https://example.com/video"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Test"
    assert payload["formats"][0]["format_id"] == "18"


def test_settings_reports_cookies_status(client):
    response = client.get("/settings")
    assert response.status_code == 200
    payload = response.json()
    assert "cookies_configured" in payload
