"""Canonical UTC timestamp helpers."""

from __future__ import annotations

from datetime import datetime, timezone


UTC_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def format_utc(value: datetime) -> str:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Canonical timestamps must be timezone-aware")
    return value.astimezone(timezone.utc).strftime(UTC_FORMAT)


def parse_utc(value: str) -> datetime:
    parsed = datetime.strptime(value, UTC_FORMAT)
    return parsed.replace(tzinfo=timezone.utc)
