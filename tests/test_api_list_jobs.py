from __future__ import annotations

from app.services.jobs import create_batch, create_job


def test_list_jobs_returns_total(client, db_session):
    batch = create_batch(db_session, "https://example.com/channel")
    create_job(db_session, source_url=batch.source_url, batch_id=batch.id, video_url="https://x")
    create_job(db_session, source_url=batch.source_url, batch_id=batch.id, video_url="https://y")
    db_session.commit()

    response = client.get("/jobs")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 2
    assert len(payload["jobs"]) == 2
