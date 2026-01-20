from __future__ import annotations

from app.services.jobs import add_job_event, create_job


def test_job_events_empty(client, db_session):
    job = create_job(db_session, source_url="https://example.com")
    db_session.commit()

    response = client.get(f"/jobs/{job.id}/events")
    assert response.status_code == 200
    assert response.json() == []


def test_job_events_returns_records(client, db_session):
    job = create_job(db_session, source_url="https://example.com")
    add_job_event(db_session, job.id, "queued", "Queued", 0.0)
    db_session.commit()

    response = client.get(f"/jobs/{job.id}/events")
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["event_type"] == "queued"
