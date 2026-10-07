from datetime import datetime, timedelta

from app.models import Block


def local(day: datetime, hour: int) -> datetime:
    return day.replace(hour=hour).astimezone()


def busy(start: datetime, end: datetime) -> list[Block]:
    day = start.astimezone().replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    blocks = []
    while day.astimezone() < end:
        if day.weekday() < 5:
            blocks.append(Block(start=local(day, 9), end=local(day, 17)))
        blocks.append(Block(start=local(day, 19), end=local(day, 20)))
        day += timedelta(days=1)
    return blocks
