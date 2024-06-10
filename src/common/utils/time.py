from datetime import datetime, timezone


def utc_with_zone() -> datetime:
    zone = timezone.utc
    return datetime.now(tz=zone)
