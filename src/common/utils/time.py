from datetime import datetime, timezone, timedelta


def get_yekaterinburg_dt() -> datetime:
    tz = timezone(offset=timedelta(hours=+5))  # Yekaterinburg Time Zone
    return datetime.now(tz)


def utc_with_zone() -> datetime:
    zone = timezone.utc
    return datetime.now(tz=zone)
