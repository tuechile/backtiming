import os
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime

from app.models import Event, EventIn, Task, TaskIn

DB_PATH = os.environ.get("BACKTIMING_DB", "backtiming.db")

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    start TEXT NOT NULL,
    horizon_days INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    minutes INTEGER NOT NULL,
    due_days_before INTEGER NOT NULL
);
"""


@contextmanager
def connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init():
    with connection() as conn:
        conn.executescript(SCHEMA)


def to_event(row) -> Event:
    return Event(id=row["id"], title=row["title"], start=datetime.fromisoformat(row["start"]), horizon_days=row["horizon_days"])


def list_events() -> list[Event]:
    with connection() as conn:
        return [to_event(r) for r in conn.execute("SELECT * FROM events ORDER BY start")]


def get_event(event_id: int) -> Event | None:
    with connection() as conn:
        row = conn.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    return to_event(row) if row else None


def create_event(data: EventIn) -> Event:
    start = data.start.astimezone(UTC).isoformat()
    with connection() as conn:
        cur = conn.execute("INSERT INTO events (title, start, horizon_days) VALUES (?, ?, ?)", (data.title, start, data.horizon_days))
    return Event(id=cur.lastrowid, **data.model_dump())


def delete_event(event_id: int):
    with connection() as conn:
        conn.execute("DELETE FROM events WHERE id = ?", (event_id,))


def list_tasks(event_id: int) -> list[Task]:
    with connection() as conn:
        rows = conn.execute("SELECT * FROM tasks WHERE event_id = ? ORDER BY due_days_before DESC, id", (event_id,))
        return [Task(**dict(r)) for r in rows]


def create_task(event_id: int, data: TaskIn) -> Task:
    with connection() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (event_id, title, minutes, due_days_before) VALUES (?, ?, ?, ?)",
            (event_id, data.title, data.minutes, data.due_days_before),
        )
    return Task(id=cur.lastrowid, event_id=event_id, **data.model_dump())


def delete_task(task_id: int):
    with connection() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
