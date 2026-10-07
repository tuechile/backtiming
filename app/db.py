import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

from app.models import Event, EventIn, Settings, Task, TaskIn, Template, TemplateIn

DB_PATH = os.environ.get("BACKTIMING_DB", "backtiming.db")
STARTER_TEMPLATES = Path(__file__).parent / "starter_templates.json"

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
CREATE TABLE IF NOT EXISTS settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    data TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS templates (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    horizon_days INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS template_tasks (
    id INTEGER PRIMARY KEY,
    template_id INTEGER NOT NULL REFERENCES templates(id) ON DELETE CASCADE,
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
        seeded = conn.execute("PRAGMA user_version").fetchone()[0] >= 1
    if not seeded:
        for data in json.loads(STARTER_TEMPLATES.read_text()):
            save_template(TemplateIn(**data))
        with connection() as conn:
            conn.execute("PRAGMA user_version = 1")


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


def list_templates() -> list[Template]:
    with connection() as conn:
        templates = conn.execute("SELECT * FROM templates ORDER BY name").fetchall()
        tasks = conn.execute("SELECT * FROM template_tasks ORDER BY due_days_before DESC, id").fetchall()
    return [
        Template(
            id=t["id"],
            name=t["name"],
            horizon_days=t["horizon_days"],
            tasks=[TaskIn(title=r["title"], minutes=r["minutes"], due_days_before=r["due_days_before"]) for r in tasks if r["template_id"] == t["id"]],
        )
        for t in templates
    ]


def get_template(template_id: int) -> Template | None:
    return next((t for t in list_templates() if t.id == template_id), None)


def save_template(data: TemplateIn) -> Template:
    with connection() as conn:
        conn.execute("DELETE FROM templates WHERE name = ?", (data.name,))
        cur = conn.execute("INSERT INTO templates (name, horizon_days) VALUES (?, ?)", (data.name, data.horizon_days))
        conn.executemany(
            "INSERT INTO template_tasks (template_id, title, minutes, due_days_before) VALUES (?, ?, ?, ?)",
            [(cur.lastrowid, t.title, t.minutes, t.due_days_before) for t in data.tasks],
        )
    return Template(id=cur.lastrowid, **data.model_dump())


def delete_template(template_id: int):
    with connection() as conn:
        conn.execute("DELETE FROM templates WHERE id = ?", (template_id,))


def get_settings() -> Settings:
    with connection() as conn:
        row = conn.execute("SELECT data FROM settings WHERE id = 1").fetchone()
    return Settings.model_validate_json(row["data"]) if row else Settings()


def save_settings(data: Settings) -> Settings:
    with connection() as conn:
        conn.execute("INSERT OR REPLACE INTO settings (id, data) VALUES (1, ?)", (data.model_dump_json(),))
    return data
