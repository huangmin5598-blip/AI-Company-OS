"""Deterministic JSON serialization and payload hashing."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from typing import Any

from app.foundation.clock import format_utc


def _json_default(value: Any) -> Any:
    if isinstance(value, datetime):
        return format_utc(value)
    raise TypeError(f"Unsupported canonical JSON value: {type(value).__name__}")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        default=_json_default,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def payload_hash(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(value)).hexdigest()
