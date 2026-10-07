from datetime import UTC, datetime, timedelta

from app.models import Block, Event, Task
from app.scheduler import allocate

NOW = datetime(2026, 10, 1, 8, 0, tzinfo=UTC)
EVENT = Event(id=1, title="Wedding", start=datetime(2026, 10, 10, 12, 0, tzinfo=UTC), horizon_days=14)


def task(id, minutes, due_days_before=0):
    return Task(id=id, event_id=1, title=f"t{id}", minutes=minutes, due_days_before=due_days_before)


def at(day, hour, minute=0):
    return datetime(2026, 10, day, hour, minute, tzinfo=UTC)


def spans(allocations):
    return [(a.start, a.end) for a in allocations]


def test_places_as_late_as_possible_with_buffer():
    allocations, unplaced = allocate(EVENT, [task(1, 60)], [], NOW)
    assert spans(allocations) == [(at(10, 10, 45), at(10, 11, 45))]
    assert unplaced == []


def test_busy_block_pushes_task_earlier():
    busy = [Block(start=at(10, 10), end=at(10, 11, 45))]
    allocations, _ = allocate(EVENT, [task(1, 60)], busy, NOW)
    assert spans(allocations) == [(at(10, 8, 45), at(10, 9, 45))]


def test_respects_due_days_before():
    allocations, _ = allocate(EVENT, [task(1, 60, due_days_before=2)], [], NOW)
    assert spans(allocations) == [(at(8, 11), at(8, 12))]


def test_tasks_do_not_overlap():
    allocations, _ = allocate(EVENT, [task(1, 60), task(2, 60)], [], NOW)
    assert spans(allocations) == [(at(10, 9, 45), at(10, 10, 45)), (at(10, 10, 45), at(10, 11, 45))]


def test_splits_task_across_gaps():
    busy = [Block(start=at(10, 11), end=at(10, 11, 15)), Block(start=at(10, 9, 30), end=at(10, 10))]
    allocations, _ = allocate(EVENT, [task(1, 60)], busy, NOW)
    assert spans(allocations) == [(at(10, 8, 45), at(10, 9, 15)), (at(10, 10, 15), at(10, 10, 45))]


def test_reports_unplaced_when_no_room():
    tight = Event(id=1, title="Soon", start=NOW + timedelta(hours=1), horizon_days=1)
    allocations, unplaced = allocate(tight, [task(1, 120)], [], NOW)
    assert allocations == []
    assert [t.id for t in unplaced] == [1]


def test_horizon_limits_window():
    short = Event(id=1, title="Exam", start=at(10, 12), horizon_days=1)
    allocations, unplaced = allocate(short, [task(1, 60, due_days_before=2)], [], NOW)
    assert allocations == []
    assert len(unplaced) == 1
