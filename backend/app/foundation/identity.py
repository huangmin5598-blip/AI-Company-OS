"""Opaque canonical identifier helpers."""

from __future__ import annotations

import re
import secrets


_PREFIX_PATTERN = re.compile(r"^[a-z][a-z0-9_]{1,15}$")


def new_id(prefix: str) -> str:
    """Return an opaque prefixed identifier with 128 bits of randomness."""
    if not _PREFIX_PATTERN.fullmatch(prefix):
        raise ValueError(f"Invalid canonical ID prefix: {prefix!r}")
    return f"{prefix}_{secrets.token_hex(16)}"
