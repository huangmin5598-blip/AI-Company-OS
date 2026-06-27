"""Make backend imports deterministic for unittest discovery."""

from pathlib import Path
import sys


def ensure_backend_path() -> None:
    backend = str(Path(__file__).resolve().parents[2] / "backend")
    if backend not in sys.path:
        sys.path.insert(0, backend)
