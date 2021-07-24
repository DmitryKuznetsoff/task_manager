import hashlib
from datetime import datetime, timezone


def get_password_hash(raw_password: str) -> str:
    return hashlib.sha256(raw_password.encode()).hexdigest()


DATETIME_FORMAT = '%Y-%m-%d %H:%M'


def local_to_utc(dt: datetime) -> datetime:
    local_tz = datetime.utcnow().astimezone().tzinfo
    local_dt = dt.replace(tzinfo=local_tz)
    utc_dt = local_dt.astimezone(timezone.utc)
    return utc_dt


def utc_to_local(dt: datetime) -> str:
    local_tz = datetime.utcnow().astimezone().tzinfo
    utc_dt = dt.replace(tzinfo=timezone.utc)
    local_dt = utc_dt.astimezone(local_tz).strftime(DATETIME_FORMAT)
    return local_dt
