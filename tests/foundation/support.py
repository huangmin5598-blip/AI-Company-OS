"""Disposable database and protected-state helpers for RT1 tests."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import tempfile
from types import ModuleType
from contextlib import contextmanager

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session

from path_bootstrap import ensure_backend_path


ensure_backend_path()

REPO_ROOT = Path(__file__).resolve().parents[2]
OPERATIONAL_DB = (REPO_ROOT / "backend/data/ai_company_os.db").resolve()


def load_f0_env() -> ModuleType:
    module_path = REPO_ROOT / "alembic/env.py"
    spec = importlib.util.spec_from_file_location("rt1_f0_env", module_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load F0-C0 environment")
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
        return {"present": False, "entries": []}
    entries = []
    for path in sorted(root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_file():
            stat_result = path.stat()
            entries.append(
                {
                    "path": path.relative_to(root).as_posix(),
                    "size": stat_result.st_size,
                    "mtime_ns": stat_result.st_mtime_ns,
                    "sha256": sha256_file(path),
                }
            )
    return {"present": True, "entries": entries}


def protected_snapshot() -> dict[str, object]:
    f0_env = load_f0_env()
    with sqlite3.connect(
        f"{OPERATIONAL_DB.as_uri()}?mode=ro&immutable=1",
        uri=True,
    ) as connection:
        runtime_rows = connection.execute(
            "SELECT * FROM runtime_registry ORDER BY runtime_id"
        ).fetchall()
        work_order_rows = connection.execute(
            "SELECT work_order_id, status FROM work_orders ORDER BY work_order_id"
        ).fetchall()
    return {
        "operational": f0_env.build_source_manifest(OPERATIONAL_DB),
        "backend_data": tree_manifest(REPO_ROOT / "backend/data"),
        "private": tree_manifest(REPO_ROOT / "private"),
        "runtime_digest": hashlib.sha256(
            json.dumps(runtime_rows, default=str).encode("utf-8")
        ).hexdigest(),
        "work_order_digest": hashlib.sha256(
            json.dumps(work_order_rows, default=str).encode("utf-8")
        ).hexdigest(),
        "git_status": subprocess.run(
            ["git", "status", "--porcelain=v1", "-z"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
        ).stdout,
    }


def make_sqlite_session(database_path: Path) -> tuple[object, Session]:
    engine = create_engine(f"sqlite:///{database_path}")

    @event.listens_for(engine, "connect")
    def _enable_foreign_keys(dbapi_connection, _connection_record):
        dbapi_connection.execute("PRAGMA foreign_keys=ON")

    return engine, Session(engine)


def create_foundation_schema(engine) -> None:
    from app.models.foundation_audit import AuditEvent  # noqa: F401
    from app.models.foundation_execution import WorkAttempt  # noqa: F401
    from app.models.foundation_identity import Tenant  # noqa: F401
    from app.models.foundation_base import FoundationBase

    FoundationBase.metadata.create_all(engine)


@contextmanager
def operational_copy_at_0003():
    harness = load_f0_env()
    manifest = harness.build_source_manifest(OPERATIONAL_DB)
    components = {
        component["role"]: component
        for component in manifest["source_database"]["components"]
    }
    if components["wal"]["present"] or components["shm"]["present"]:
        raise RuntimeError("operational_database_sidecar_present")

    with tempfile.TemporaryDirectory() as temporary_directory:
        copied = Path(temporary_directory) / "operational-copy.db"
        shutil.copy2(OPERATIONAL_DB, copied)
        configuration = Config(str(REPO_ROOT / "alembic.ini"))
        configuration.set_main_option("sqlalchemy.url", f"sqlite:///{copied}")
        command.stamp(configuration, "0001_baseline")
        command.upgrade(configuration, "0003_promotion_execution_persistence")
        yield copied
