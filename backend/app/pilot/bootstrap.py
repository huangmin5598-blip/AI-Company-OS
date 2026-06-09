"""Explicit bootstrap for the isolated VS-001 pilot database."""

from __future__ import annotations

import json
from pathlib import Path
import sqlite3

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from app.pilot.database import (
    PILOT_AUTHORITY,
    PILOT_DB_PATH,
    PILOT_MARKER_ID,
    PilotDatabase,
    assert_fixed_pilot_path,
)
from app.services.canonical_execution_service import (
    BUILTIN_ADAPTER_MODULE,
    BUILTIN_RUNTIME_ID,
    BUILTIN_RUNTIME_TYPE,
)
from app.services.controlled_builtin_executor import BUILTIN_SCRIPT
from app.services.foundation_bootstrap import bootstrap_local_foundation


REPO_ROOT = Path(__file__).resolve().parents[3]


def _script_hash() -> str:
    import hashlib

    return "sha256:" + hashlib.sha256(BUILTIN_SCRIPT.read_bytes()).hexdigest()


def _create_minimal_legacy_tables(connection: sqlite3.Connection) -> None:
    connection.executescript(
        """
        CREATE TABLE IF NOT EXISTS work_orders (
            work_order_id VARCHAR PRIMARY KEY NOT NULL,
            goal_session_id VARCHAR,
            product_line_id VARCHAR,
            skill_id VARCHAR NOT NULL,
            task_type VARCHAR,
            route_reason TEXT,
            risk_level VARCHAR,
            execution_mode VARCHAR,
            assigned_agent VARCHAR,
            runtime_id VARCHAR,
            input_context TEXT,
            expected_output TEXT,
            status VARCHAR,
            approval_required BOOLEAN,
            approval_id VARCHAR,
            attempt_count INTEGER,
            output_path TEXT,
            evidence_path TEXT,
            error TEXT,
            result_summary TEXT,
            artifacts_json TEXT,
            routing_log_json TEXT,
            execution_log_json TEXT,
            created_at DATETIME,
            assigned_at DATETIME,
            completed_at DATETIME,
            openclaw_dispatched_at DATETIME,
            openclaw_claimed_at DATETIME,
            openclaw_timeout_at DATETIME,
            approved_for_dispatch_at DATETIME
        );
        CREATE TABLE IF NOT EXISTS runtime_registry (
            id INTEGER PRIMARY KEY NOT NULL,
            runtime_id VARCHAR NOT NULL UNIQUE,
            runtime_type VARCHAR NOT NULL,
            display_name VARCHAR NOT NULL,
            adapter_module VARCHAR NOT NULL,
            endpoint VARCHAR,
            config_json TEXT,
            enabled INTEGER DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS pilot_marker (
            marker_id VARCHAR PRIMARY KEY NOT NULL,
            authority VARCHAR NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    existing = connection.execute(
        "SELECT marker_id, authority FROM pilot_marker"
    ).fetchall()
    if not existing:
        connection.execute(
            "INSERT INTO pilot_marker (marker_id, authority) VALUES (?, ?)",
            (PILOT_MARKER_ID, PILOT_AUTHORITY),
        )
    elif existing != [(PILOT_MARKER_ID, PILOT_AUTHORITY)]:
        raise RuntimeError("pilot_marker_authority_invalid")
    connection.commit()


def _upgrade_foundation(path: Path) -> None:
    config = Config(str(REPO_ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{path}")
    with sqlite3.connect(path) as connection:
        stamped = connection.execute(
            "SELECT COUNT(*) FROM sqlite_master"
            " WHERE type='table' AND name='alembic_version'"
        ).fetchone()[0]
    if not stamped:
        command.stamp(config, "0001_baseline")
    command.upgrade(config, "0003_promotion_execution_persistence")


def bootstrap_pilot_database(
    database: PilotDatabase | None = None,
) -> PilotDatabase:
    owned = database is None
    pilot = database or PilotDatabase(PILOT_DB_PATH)
    if owned:
        assert_fixed_pilot_path(pilot.path)
    pilot.path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(pilot.path) as connection:
        _create_minimal_legacy_tables(connection)
    _upgrade_foundation(pilot.path)

    with pilot.command_session() as session:
        bootstrap_local_foundation(session)
        if session.execute(
            text(
                "SELECT COUNT(*) FROM runtime_registry"
                " WHERE runtime_id=:runtime_id"
            ),
            {"runtime_id": BUILTIN_RUNTIME_ID},
        ).scalar_one() == 0:
            session.execute(
                text(
                    "INSERT INTO runtime_registry"
                    " (runtime_id, runtime_type, display_name, adapter_module,"
                    " config_json, enabled) VALUES"
                    " (:runtime_id, :runtime_type, :display_name,"
                    " :adapter_module, :config_json, 1)"
                ),
                {
                    "runtime_id": BUILTIN_RUNTIME_ID,
                    "runtime_type": BUILTIN_RUNTIME_TYPE,
                    "display_name": "VS-001 Controlled Builtin",
                    "adapter_module": BUILTIN_ADAPTER_MODULE,
                    "config_json": json.dumps(
                        {
                            "executor": "controlled_builtin",
                            "script_sha256": _script_hash(),
                            "scratch_only": True,
                            "registry_source": "pilot_non_authoritative",
                            "production_registered": False,
                        },
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                },
            )
    return pilot


__all__ = ["bootstrap_pilot_database"]
