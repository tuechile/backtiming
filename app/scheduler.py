from datetime import UTC, datetime, timedelta

from app.models import Allocation, Block, Event, Task

GRID_SECONDS = 15 * 60


def floor_grid(t: datetime) -> datetime:
    return datetime.fromtimestamp(t.timestamp() // GRID_SECONDS * GRID_SECONDS, UTC)


def ceil_grid(t: datetime) -> datetime:
    return datetime.fromtimestamp(-(-t.timestamp() // GRID_SECONDS) * GRID_SECONDS, UTC)


def free_gaps(start: datetime, end: datetime, busy: list[Block], buffer: timedelta) -> list[tuple[datetime, datetime]]:
    gaps = []
    cursor = start
    for block in sorted(busy, key=lambda b: b.start):
        if block.start - buffer > cursor:
            gaps.append((cursor, min(block.start - buffer, end)))
        cursor = max(cursor, block.end + buffer)
        if cursor >= end:
            break
    if cursor < end:
        gaps.append((cursor, end))
    gaps = [(ceil_grid(s), floor_grid(e)) for s, e in gaps]
    return [(s, e) for s, e in gaps if s < e]


def subtract(gaps: list[tuple[datetime, datetime]], start: datetime, end: datetime) -> list[tuple[datetime, datetime]]:
    result = []
    for gap_start, gap_end in gaps:
        if gap_end <= start or gap_start >= end:
            result.append((gap_start, gap_end))
            continue
        if gap_start < start:
            result.append((gap_start, start))
        if end < gap_end:
            result.append((end, gap_end))
    return result


def place(task: Task, deadline: datetime, gaps: list[tuple[datetime, datetime]], min_chunk: timedelta) -> list[tuple[datetime, datetime]] | None:
    remaining = timedelta(minutes=task.minutes)
    chosen = []
    for gap_start, gap_end in reversed(gaps):
        gap_end = min(gap_end, deadline)
        if gap_end <= gap_start:
            continue
        size = min(remaining, gap_end - gap_start)
        if size < remaining and size < min_chunk:
            continue
        chosen.append((gap_end - size, gap_end))
        remaining -= size
        if not remaining:
            return chosen
    return None


def allocate(
    event: Event,
    tasks: list[Task],
    busy: list[Block],
    now: datetime,
    buffer: timedelta = timedelta(minutes=15),
    min_chunk: timedelta = timedelta(minutes=30),
) -> tuple[list[Allocation], list[Task]]:
    window_start = max(now, event.start - timedelta(days=event.horizon_days))
    gaps = free_gaps(window_start, event.start - buffer, busy, buffer)
    allocations, unplaced = [], []
    for task in sorted(tasks, key=lambda t: t.due_days_before):
        deadline = event.start - timedelta(days=task.due_days_before)
        chunks = place(task, deadline, gaps, min_chunk)
        if chunks is None:
            unplaced.append(task)
            continue
        for start, end in chunks:
            gaps = subtract(gaps, start, end)
            allocations.append(Allocation(task_id=task.id, title=task.title, start=start, end=end))
    return sorted(allocations, key=lambda a: a.start), unplaced
