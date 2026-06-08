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
from datetime import datetime, timezone

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


def controlled_builtin_script_hash() -> str:
    script = REPO_ROOT / "scripts/builtins/vs001_echo_markdown.py"
    return "sha256:" + sha256_file(script)


def fixture_preflight_lineage(
    attempt_id: str,
    work_order_id: str,
) -> tuple[dict[str, str], str, str]:
    payload = {
        "attempt_id": attempt_id,
        "work_order_id": work_order_id,
        "tenant_id": "ten_local",
        "workspace_id": "wsp_personal",
        "script_path": str(
            REPO_ROOT / "scripts/builtins/vs001_echo_markdown.py"
        ),
        "script_sha256": controlled_builtin_script_hash(),
        "scratch_root": "/fixture/attempt",
        "allowed_temp_root": "/fixture",
        "input_ref": "scratch://input",
        "output_ref": "scratch://output",
    }
    payload_hash = "sha256:" + hashlib.sha256(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    return (
        payload,
        payload_hash,
        f"preflight://{attempt_id}/{payload_hash}",
    )


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


@contextmanager
def phase2a_authority_database():
    from app.services.foundation_bootstrap import bootstrap_local_foundation

    harness = load_f0_env()
    before = harness.build_source_manifest(OPERATIONAL_DB)
    with sqlite3.connect(
        f"{OPERATIONAL_DB.as_uri()}?mode=ro&immutable=1",
        uri=True,
    ) as connection:
        if connection.execute(
            "SELECT COUNT(*) FROM sqlite_master"
            " WHERE type='table' AND name='alembic_version'"
        ).fetchone()[0]:
            raise RuntimeError("operational_database_already_stamped")

    try:
        with operational_copy_at_0003() as copied:
            engine, session = make_sqlite_session(copied)
            try:
                bootstrap_local_foundation(session)
                work_order_id = session.execute(
                    __import__("sqlalchemy").text(
                        "SELECT work_order_id FROM work_orders"
                        " ORDER BY work_order_id LIMIT 1"
                    )
                ).scalar_one()
                session.execute(
                    __import__("sqlalchemy").text(
                        "UPDATE work_orders SET tenant_id=:tenant_id,"
                        " workspace_id=:workspace_id, canonical_state='draft',"
                        " row_version=1, parallel_attempts_allowed=0,"
                        " max_attempts=3, canonicalized_at=:canonicalized_at"
                        " WHERE work_order_id=:work_order_id"
                    ),
                    {
                        "tenant_id": "ten_local",
                        "workspace_id": "wsp_personal",
                        "canonicalized_at": datetime.now(timezone.utc),
                        "work_order_id": work_order_id,
                    },
                )
                script_hash = controlled_builtin_script_hash()
                session.execute(
                    __import__("sqlalchemy").text(
                        "INSERT INTO runtime_registry"
                        " (runtime_id, runtime_type, display_name, adapter_module,"
                        " config_json, enabled) VALUES"
                        " (:runtime_id, :runtime_type, :display_name,"
                        " :adapter_module, :config_json, 1)"
                    ),
                    {
                        "runtime_id": "builtin.vs001_echo_markdown",
                        "runtime_type": "controlled_builtin",
                        "display_name": "VS-001 Controlled Builtin",
                        "adapter_module": (
                            "app.services.controlled_builtin_executor"
                        ),
                        "config_json": json.dumps(
                            {
                                "executor": "controlled_builtin",
                                "script_sha256": script_hash,
                                "scratch_only": True,
                            },
                            sort_keys=True,
                            separators=(",", ":"),
                        ),
                    },
                )
                session.commit()
            finally:
                session.close()
                engine.dispose()
            yield copied, work_order_id
    finally:
        if before != harness.build_source_manifest(OPERATIONAL_DB):
            raise RuntimeError("operational_database_changed")
        with sqlite3.connect(
            f"{OPERATIONAL_DB.as_uri()}?mode=ro&immutable=1",
            uri=True,
        ) as connection:
            if connection.execute(
                "SELECT COUNT(*) FROM sqlite_master"
                " WHERE type='table' AND name='alembic_version'"
            ).fetchone()[0]:
                raise RuntimeError("operational_database_was_stamped")
