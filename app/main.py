from contextlib import asynccontextmanager
from datetime import UTC, datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app import db, demo, gcal, scheduler
from app.models import Event, EventCreate, Plan, SaveTemplate, Settings, Task, TaskIn, Template, TemplateIn

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


def find_template(template_id: int) -> Template:
    template = db.get_template(template_id)
    if not template:
        raise HTTPException(404, "Template not found")
    return template


def apply_template(event: Event, template: Template) -> list[Task]:
    return [db.create_task(event.id, task) for task in template.tasks]


def make_plan(event: Event) -> Plan:
    now = datetime.now(UTC)
    source = gcal if gcal.available() else demo
    busy = source.busy(now, event.start) if event.start > now else []
    settings = db.get_settings()
    blocked = scheduler.sleep_blocks(now, event.start, settings.sleep_start, settings.sleep_end) if settings.sleep_enabled else []
    allocations, unplaced = scheduler.allocate(event, db.list_tasks(event.id), busy, now, blocked)
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
def create_event(data: EventCreate) -> Event:
    template = find_template(data.template_id) if data.template_id else None
    event = db.create_event(data)
    if template:
        apply_template(event, template)
    return event


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


@app.post("/api/events/{event_id}/apply-template/{template_id}")
def apply(event_id: int, template_id: int) -> list[Task]:
    return apply_template(find_event(event_id), find_template(template_id))


@app.post("/api/events/{event_id}/save-template")
def save_as_template(event_id: int, data: SaveTemplate) -> Template:
    event = find_event(event_id)
    tasks = [TaskIn(**t.model_dump()) for t in db.list_tasks(event.id)]
    return db.save_template(TemplateIn(name=data.name, horizon_days=event.horizon_days, tasks=tasks))


@app.get("/api/templates")
def list_templates() -> list[Template]:
    return db.list_templates()


@app.post("/api/templates")
def create_template(data: TemplateIn) -> Template:
    return db.save_template(data)


@app.delete("/api/templates/{template_id}")
def delete_template(template_id: int):
    db.delete_template(template_id)
    return {"ok": True}


@app.get("/api/settings")
def get_settings() -> Settings:
    return db.get_settings()


@app.put("/api/settings")
def save_settings(data: Settings) -> Settings:
    return db.save_settings(data)
