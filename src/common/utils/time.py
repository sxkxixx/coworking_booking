from datetime import datetime, timezone, timedelta


def current_ural_time() -> datetime:
    zone = timezone(timedelta(hours=5))
    return datetime.now(tz=zone)


def utc_with_zone() -> datetime:
    zone = timezone.utc
    return datetime.now(tz=zone)
