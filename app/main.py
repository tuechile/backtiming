from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app import db, demo, gcal, scheduler
from app.models import Event, EventIn, Plan, Task, TaskIn

STATIC = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_):
    db.init()
    yield


app = FastAPI(lifespan=lifespan)


def find_event(event_id: int) -> Event:
    event = db.get_event(event_id)
    if not event:
        raise HTTPException(404, "Event not found")
    return event


def make_plan(event: Event) -> Plan:
    now = datetime.now(UTC)
    source = gcal if gcal.available() else demo
    busy = source.busy(now, event.start) if event.start > now else []
    allocations, unplaced = scheduler.allocate(event, db.list_tasks(event.id), busy, now)
    return Plan(source="google" if source is gcal else "demo", busy=busy, allocations=allocations, unplaced=unplaced)


@app.get("/")
def index():
    return FileResponse(STATIC / "index.html")


@app.get("/api/status")
def status():
    return {"google": gcal.available()}


@app.get("/api/events")
def list_events() -> list[Event]:
    return db.list_events()


@app.post("/api/events")
def create_event(data: EventIn) -> Event:
    return db.create_event(data)


@app.delete("/api/events/{event_id}")
def delete_event(event_id: int):
    db.delete_event(event_id)
    return {"ok": True}


@app.get("/api/events/{event_id}/tasks")
def list_tasks(event_id: int) -> list[Task]:
    return db.list_tasks(find_event(event_id).id)


@app.post("/api/events/{event_id}/tasks")
def create_task(event_id: int, data: TaskIn) -> Task:
    return db.create_task(find_event(event_id).id, data)


@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: int):
    db.delete_task(task_id)
    return {"ok": True}


@app.get("/api/events/{event_id}/plan")
def plan(event_id: int) -> Plan:
    return make_plan(find_event(event_id))


@app.post("/api/events/{event_id}/push")
def push(event_id: int):
    if not gcal.available():
        raise HTTPException(400, "Google Calendar is not connected. Add credentials.json to enable pushing.")
    event = find_event(event_id)
    return {"written": gcal.push(event, make_plan(event).allocations)}
