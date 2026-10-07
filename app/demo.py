from datetime import datetime, timedelta

from app.models import Block


def busy(start: datetime, end: datetime) -> list[Block]:
    local = datetime.now().astimezone().tzinfo
    day = start.astimezone(local).replace(hour=0, minute=0, second=0, microsecond=0)
    blocks = []
    while day < end:
        if day.weekday() < 5:
            blocks.append(Block(start=day.replace(hour=9), end=day.replace(hour=17)))
        blocks.append(Block(start=day.replace(hour=19), end=day.replace(hour=20)))
        day += timedelta(days=1)
    return blocks
