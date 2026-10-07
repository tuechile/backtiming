from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app import db, gcal
from app.main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", str(tmp_path / "test.db"))
    monkeypatch.setattr(gcal, "available", lambda: False)
    with TestClient(app) as c:
        yield c


def test_demo_flow(client):
    start = (datetime.now(UTC) + timedelta(days=5)).isoformat()
    event = client.post("/api/events", json={"title": "Move", "start": start, "horizon_days": 7}).json()
    client.post(f"/api/events/{event['id']}/tasks", json={"title": "Pack", "minutes": 120, "due_days_before": 1})
    client.post(f"/api/events/{event['id']}/tasks", json={"title": "Clean", "minutes": 90})

    plan = client.get(f"/api/events/{event['id']}/plan").json()

    assert plan["source"] == "demo"
    assert {a["title"] for a in plan["allocations"]} == {"Pack", "Clean"}
    assert plan["unplaced"] == []


def test_push_requires_google(client):
    start = (datetime.now(UTC) + timedelta(days=5)).isoformat()
    event = client.post("/api/events", json={"title": "Move", "start": start}).json()
    assert client.post(f"/api/events/{event['id']}/push").status_code == 400


def future(days=20):
    return (datetime.now(UTC) + timedelta(days=days)).isoformat()


def test_starter_templates_are_seeded(client):
    names = {t["name"] for t in client.get("/api/templates").json()}
    assert {"Wedding (guest)", "Moving house", "Exam"} <= names


def test_create_event_from_template_copies_tasks(client):
    template = client.get("/api/templates").json()[0]
    event = client.post("/api/events", json={"title": "Big day", "start": future(), "template_id": template["id"]}).json()
    tasks = client.get(f"/api/events/{event['id']}/tasks").json()
    assert sorted(t["title"] for t in tasks) == sorted(t["title"] for t in template["tasks"])


def test_save_event_as_template_replaces_same_name(client):
    event = client.post("/api/events", json={"title": "Recital", "start": future(), "horizon_days": 9}).json()
    client.post(f"/api/events/{event['id']}/tasks", json={"title": "Practice", "minutes": 60})
    client.post(f"/api/events/{event['id']}/save-template", json={"name": "Recital"})
    client.post(f"/api/events/{event['id']}/tasks", json={"title": "Tune", "minutes": 30})
    client.post(f"/api/events/{event['id']}/save-template", json={"name": "Recital"})

    recitals = [t for t in client.get("/api/templates").json() if t["name"] == "Recital"]
    assert len(recitals) == 1
    assert recitals[0]["horizon_days"] == 9
    assert {t["title"] for t in recitals[0]["tasks"]} == {"Practice", "Tune"}


def test_delete_template_stays_deleted_after_restart(client):
    template = client.get("/api/templates").json()[0]
    client.delete(f"/api/templates/{template['id']}")
    db.init()
    assert template["name"] not in {t["name"] for t in client.get("/api/templates").json()}


def test_unknown_template_is_404(client):
    assert client.post("/api/events", json={"title": "X", "start": future(), "template_id": 999}).status_code == 404


def test_settings_default_and_save(client):
    assert client.get("/api/settings").json() == {"sleep_enabled": True, "sleep_start": "02:00:00", "sleep_end": "09:00:00"}
    client.put("/api/settings", json={"sleep_enabled": True, "sleep_start": "23:30", "sleep_end": "07:00"})
    assert client.get("/api/settings").json()["sleep_start"] == "23:30:00"
