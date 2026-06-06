"""Shared F0-C0 test harness helpers."""

from __future__ import annotations

import contextlib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import socket
import sqlite3
import subprocess
import sys
import threading
from types import ModuleType
from unittest import mock
import urllib.request


REPO_ROOT = Path(__file__).resolve().parents[2]
OPERATIONAL_DB = (REPO_ROOT / "backend/data/ai_company_os.db").resolve()
ALLOWED_PATHS = {
    "alembic.ini",
    "alembic/env.py",
    "alembic/versions/0001_baseline.py",
    "alembic/versions/__init__.py",
    "tests/migration/__init__.py",
    "tests/migration/conftest.py",
    "tests/migration/test_f0_c0_source_manifest.py",
    "tests/migration/test_f0_c0_operational_bind_guard.py",
    "tests/migration/test_f0_c0_no_write.py",
    "tests/migration/test_f0_c0_baseline.py",
}


def load_f0_env() -> ModuleType:
    module_path = REPO_ROOT / "alembic/env.py"
    spec = importlib.util.spec_from_file_location("f0_c0_alembic_env", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load F0-C0 Alembic environment")
    module = importlib.util.module_from_spec(spec)
    previous = os.environ.get("F0_C0_IMPORT_ONLY")
    os.environ["F0_C0_IMPORT_ONLY"] = "1"
    try:
        spec.loader.exec_module(module)
    finally:
        if previous is None:
            os.environ.pop("F0_C0_IMPORT_ONLY", None)
        else:
            os.environ["F0_C0_IMPORT_ONLY"] = previous
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_manifest(root: Path) -> dict[str, object]:
    if not root.exists():
        return {"root": str(root), "present": False, "entries": []}
    entries: list[dict[str, object]] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            entries.append(
                {
                    "path": relative,
                    "type": "symlink",
                    "target": os.readlink(path),
                }
            )
        elif path.is_file():
            stat_result = path.stat()
            entries.append(
                {
                    "path": relative,
                    "type": "file",
                    "size_bytes": int(stat_result.st_size),
                    "mtime_ns": int(stat_result.st_mtime_ns),
                    "sha256": sha256_file(path),
                }
            )
        elif path.is_dir():
            stat_result = path.stat()
            entries.append(
                {
                    "path": relative,
                    "type": "directory",
                    "mtime_ns": int(stat_result.st_mtime_ns),
                }
            )
    return {"root": str(root), "present": True, "entries": entries}


def git_status() -> bytes:
    return subprocess.run(
        ["git", "status", "--porcelain=v1", "-z"],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
    ).stdout


def _immutable_connection() -> sqlite3.Connection:
    uri = f"{OPERATIONAL_DB.as_uri()}?mode=ro&immutable=1"
    return sqlite3.connect(uri, uri=True)


def table_digest(table_name: str) -> str:
    if table_name not in {"runtime_registry", "work_orders"}:
        raise ValueError(f"Unsupported protected table: {table_name}")
    with _immutable_connection() as connection:
        columns = [
            row[1]
            for row in connection.execute(f"PRAGMA table_info({table_name})")
        ]
        rows = connection.execute(f"SELECT * FROM {table_name}").fetchall()
    normalized = {
        "table": table_name,
        "columns": columns,
        "rows": sorted(
            [list(row) for row in rows],
            key=lambda row: json.dumps(row, default=str, sort_keys=True),
        ),
    }
    encoded = json.dumps(
        normalized,
        default=str,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def guarded_state_snapshot() -> dict[str, object]:
    f0_env = load_f0_env()
    return {
        "git_status": git_status(),
        "operational_manifest": f0_env.build_source_manifest(OPERATIONAL_DB),
        "backend_data": tree_manifest(REPO_ROOT / "backend/data"),
        "private": tree_manifest(REPO_ROOT / "private"),
        "runtime_registry_digest": table_digest("runtime_registry"),
        "work_orders_digest": table_digest("work_orders"),
    }


@contextlib.contextmanager
def prohibited_activity_traps():
    attempts: list[str] = []

    def reject(name: str):
        def _rejected(*_args, **_kwargs):
            attempts.append(name)
            raise AssertionError(f"Prohibited F0-C0 activity attempted: {name}")

        return _rejected

    with (
        mock.patch.object(threading.Thread, "start", reject("background_thread")),
        mock.patch.object(subprocess, "Popen", reject("subprocess")),
        mock.patch.object(socket, "socket", reject("network_socket")),
        mock.patch.object(urllib.request, "urlopen", reject("network_urlopen")),
    ):
        yield attempts


def assert_no_backend_startup_imports() -> None:
    forbidden = {
        "app.main",
        "app.database",
        "backend.app.main",
        "backend.app.database",
    }
    imported = forbidden.intersection(sys.modules)
    if imported:
        raise AssertionError(f"Mutation-capable startup modules imported: {imported}")
