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
