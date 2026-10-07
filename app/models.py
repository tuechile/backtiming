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
