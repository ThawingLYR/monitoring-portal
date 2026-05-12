from datetime import datetime, timezone


def make_utc(time: datetime):
    if time is None:
        return time

    if time.tzinfo is None:
        time = time.replace(tzinfo=timezone.utc)
    return time
