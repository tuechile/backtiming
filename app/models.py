from datetime import time

from pydantic import AwareDatetime, BaseModel, Field


class EventIn(BaseModel):
    title: str
    start: AwareDatetime
    horizon_days: int = Field(default=14, ge=1)


class Event(EventIn):
    id: int


class TaskIn(BaseModel):
    title: str
    minutes: int = Field(gt=0)
    due_days_before: int = Field(default=0, ge=0)


class Task(TaskIn):
    id: int
    event_id: int


class TemplateIn(BaseModel):
    name: str
    horizon_days: int = Field(default=14, ge=1)
    tasks: list[TaskIn] = []


class Template(TemplateIn):
    id: int


class EventCreate(EventIn):
    template_id: int | None = None


class SaveTemplate(BaseModel):
    name: str


class Settings(BaseModel):
    sleep_enabled: bool = True
    sleep_start: time = time(2)
    sleep_end: time = time(9)


class Block(BaseModel):
    start: AwareDatetime
    end: AwareDatetime


class Allocation(Block):
    task_id: int
    title: str


class Plan(BaseModel):
    source: str
    busy: list[Block]
    allocations: list[Allocation]
    unplaced: list[Task]
