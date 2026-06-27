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
from app.pilot.real_workbench import (
    REAL_WORKBENCH_SCHEMA_COMPONENT,
    REAL_WORKBENCH_SCHEMA_VERSION,
)
from app.services.canonical_execution_service import (
    BUILTIN_ADAPTER_MODULE,
    BUILTIN_RUNTIME_ID,
    BUILTIN_RUNTIME_TYPE,
)
from app.services.controlled_builtin_executor import BUILTIN_SCRIPT
from app.services.foundation_bootstrap import bootstrap_local_foundation


REPO_ROOT = Path(__file__).resolve().parents[3]


def _validate_asset_schema(connection: sqlite3.Connection) -> None:
    expected_columns = {
        "pilot_artifacts": {
            "artifact_id",
            "tenant_id",
            "workspace_id",
            "scope_key",
            "work_order_id",
            "attempt_id",
            "source_ref",
            "storage_ref",
            "content_hash",
            "media_type",
            "size_bytes",
            "sensitivity",
            "validation_status",
            "authority",
            "visibility",
            "source_path",
            "source_authority",
            "provenance_json",
            "content_text",
            "created_by",
            "created_at",
        },
        "pilot_assets": {
            "asset_id",
            "tenant_id",
            "workspace_id",
            "scope_key",
            "title",
            "asset_type",
            "source_work_order_id",
            "source_review_id",
            "version",
            "status",
            "content_ref",
            "public_safe_ref",
            "sensitivity",
            "visibility",
            "authority",
            "source_path",
            "source_authority",
            "owner_id",
            "approval_id",
            "row_version",
            "created_by",
            "created_at",
            "approved_by",
            "approved_at",
        },
        "pilot_asset_artifacts": {
            "asset_id",
            "artifact_id",
            "tenant_id",
            "workspace_id",
            "scope_key",
            "content_hash",
            "created_at",
        },
    }
    for table, expected in expected_columns.items():
        actual = {
            row[1]
            for row in connection.execute(f"PRAGMA table_info({table})")
        }
        if actual != expected:
            raise RuntimeError(f"pilot_asset_schema_columns_invalid:{table}")
    triggers = {
        row[0]
        for row in connection.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'"
            " AND name LIKE 'pilot_%'"
        )
    }
    if not {
        "pilot_artifacts_no_update",
        "pilot_artifacts_no_delete",
        "pilot_asset_artifacts_no_update",
        "pilot_asset_artifacts_no_delete",
    }.issubset(triggers):
        raise RuntimeError("pilot_asset_schema_triggers_invalid")


def _validate_real_workbench_schema(connection: sqlite3.Connection) -> None:
    expected_columns = {
        "pilot_workbench_runs": {
            "run_id",
            "product_line_id",
            "founder_goal",
            "status",
            "authority",
            "mode",
            "source_path",
            "task_plan_hash",
            "created_at",
            "updated_at",
        },
        "pilot_workbench_tasks": {
            "task_id",
            "run_id",
            "step_index",
            "title",
            "executor_slot",
            "status",
            "expected_output",
            "audit_summary",
            "authority",
            "created_at",
            "assigned_slot",
            "assignment_status",
            "assignment_note",
            "assigned_by",
            "assigned_at",
            "updated_at",
        },
    }
    for table, expected in expected_columns.items():
        actual = {
            row[1]
            for row in connection.execute(f"PRAGMA table_info({table})")
        }
        if actual != expected:
            raise RuntimeError(f"pilot_real_workbench_schema_columns_invalid:{table}")


def _upgrade_real_workbench_schema(connection: sqlite3.Connection) -> None:
    actual = {
        row[1]
        for row in connection.execute("PRAGMA table_info(pilot_workbench_tasks)")
    }
    additions = [
        (
            "assigned_slot",
            "ALTER TABLE pilot_workbench_tasks"
            " ADD COLUMN assigned_slot VARCHAR(80)",
        ),
        (
            "assignment_status",
            "ALTER TABLE pilot_workbench_tasks"
            " ADD COLUMN assignment_status VARCHAR(32) NOT NULL"
            " DEFAULT 'unassigned'"
            " CHECK (assignment_status IN ('unassigned', 'assigned', 'revised'))",
        ),
        (
            "assignment_note",
            "ALTER TABLE pilot_workbench_tasks"
            " ADD COLUMN assignment_note TEXT NOT NULL DEFAULT ''",
        ),
        (
            "assigned_by",
            "ALTER TABLE pilot_workbench_tasks"
            " ADD COLUMN assigned_by VARCHAR(64)",
        ),
        (
            "assigned_at",
            "ALTER TABLE pilot_workbench_tasks"
            " ADD COLUMN assigned_at DATETIME",
        ),
        (
            "updated_at",
            "ALTER TABLE pilot_workbench_tasks"
            " ADD COLUMN updated_at DATETIME",
        ),
    ]
    for column, statement in additions:
        if column not in actual:
            connection.execute(statement)
    connection.execute(
        "UPDATE pilot_workbench_tasks"
        " SET updated_at=COALESCE(updated_at, created_at),"
        " assignment_note=COALESCE(assignment_note, ''),"
        " assignment_status=COALESCE(assignment_status, 'unassigned')"
    )


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
        CREATE TABLE IF NOT EXISTS pilot_schema_components (
            component VARCHAR PRIMARY KEY NOT NULL,
            version VARCHAR NOT NULL,
            authority VARCHAR NOT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS pilot_artifacts (
            artifact_id VARCHAR(64) PRIMARY KEY NOT NULL,
            tenant_id VARCHAR(64) NOT NULL,
            workspace_id VARCHAR(64) NOT NULL,
            scope_key VARCHAR(160) NOT NULL,
            work_order_id VARCHAR(160) NOT NULL,
            attempt_id VARCHAR(64) NOT NULL,
            source_ref VARCHAR(500) NOT NULL,
            storage_ref VARCHAR(500) NOT NULL,
            content_hash VARCHAR(80) NOT NULL,
            media_type VARCHAR(120) NOT NULL,
            size_bytes INTEGER NOT NULL,
            sensitivity VARCHAR(32) NOT NULL,
            validation_status VARCHAR(32) NOT NULL,
            authority VARCHAR(64) NOT NULL
                CHECK (authority = 'pilot_non_authoritative'),
            visibility VARCHAR(32) NOT NULL
                CHECK (visibility = 'restricted'),
            source_path VARCHAR(80) NOT NULL
                CHECK (source_path = 'os_governed_work_review'),
            source_authority VARCHAR(64) NOT NULL
                CHECK (source_authority = 'pilot_non_authoritative'),
            provenance_json TEXT NOT NULL,
            content_text TEXT NOT NULL,
            created_by VARCHAR(64) NOT NULL,
            created_at DATETIME NOT NULL,
            FOREIGN KEY(attempt_id) REFERENCES work_attempts(attempt_id)
                ON DELETE RESTRICT,
            UNIQUE(scope_key, attempt_id, content_hash)
        );
        CREATE TABLE IF NOT EXISTS pilot_assets (
            asset_id VARCHAR(64) PRIMARY KEY NOT NULL,
            tenant_id VARCHAR(64) NOT NULL,
            workspace_id VARCHAR(64) NOT NULL,
            scope_key VARCHAR(160) NOT NULL,
            title VARCHAR(240) NOT NULL,
            asset_type VARCHAR(80) NOT NULL,
            source_work_order_id VARCHAR(160) NOT NULL,
            source_review_id VARCHAR(64) NOT NULL,
            version INTEGER NOT NULL CHECK (version = 1),
            status VARCHAR(32) NOT NULL
                CHECK (status IN ('candidate', 'approved')),
            content_ref VARCHAR(500) NOT NULL,
            public_safe_ref VARCHAR(500),
            sensitivity VARCHAR(32) NOT NULL,
            visibility VARCHAR(32) NOT NULL
                CHECK (visibility = 'restricted'),
            authority VARCHAR(64) NOT NULL
                CHECK (authority = 'pilot_non_authoritative'),
            source_path VARCHAR(80) NOT NULL
                CHECK (source_path = 'os_governed_work_review'),
            source_authority VARCHAR(64) NOT NULL
                CHECK (source_authority = 'pilot_non_authoritative'),
            owner_id VARCHAR(64) NOT NULL,
            approval_id VARCHAR(64),
            row_version INTEGER NOT NULL CHECK (row_version >= 1),
            created_by VARCHAR(64) NOT NULL,
            created_at DATETIME NOT NULL,
            approved_by VARCHAR(64),
            approved_at DATETIME,
            FOREIGN KEY(source_review_id) REFERENCES work_reviews(review_id)
                ON DELETE RESTRICT,
            FOREIGN KEY(approval_id) REFERENCES work_approvals(approval_id)
                ON DELETE RESTRICT,
            UNIQUE(scope_key, source_review_id),
            CHECK (public_safe_ref IS NULL),
            CHECK (
                (status = 'candidate' AND approval_id IS NULL
                    AND approved_by IS NULL AND approved_at IS NULL)
                OR
                (status = 'approved' AND approval_id IS NOT NULL
                    AND approved_by IS NOT NULL AND approved_at IS NOT NULL)
            )
        );
        CREATE TABLE IF NOT EXISTS pilot_asset_artifacts (
            asset_id VARCHAR(64) NOT NULL,
            artifact_id VARCHAR(64) NOT NULL,
            tenant_id VARCHAR(64) NOT NULL,
            workspace_id VARCHAR(64) NOT NULL,
            scope_key VARCHAR(160) NOT NULL,
            content_hash VARCHAR(80) NOT NULL,
            created_at DATETIME NOT NULL,
            PRIMARY KEY(asset_id, artifact_id),
            FOREIGN KEY(asset_id) REFERENCES pilot_assets(asset_id)
                ON DELETE RESTRICT,
            FOREIGN KEY(artifact_id) REFERENCES pilot_artifacts(artifact_id)
                ON DELETE RESTRICT
        );
        CREATE TRIGGER IF NOT EXISTS pilot_artifacts_no_update
        BEFORE UPDATE ON pilot_artifacts
        BEGIN
            SELECT RAISE(ABORT, 'pilot_artifacts_append_only');
        END;
        CREATE TRIGGER IF NOT EXISTS pilot_artifacts_no_delete
        BEFORE DELETE ON pilot_artifacts
        BEGIN
            SELECT RAISE(ABORT, 'pilot_artifacts_append_only');
        END;
        CREATE TRIGGER IF NOT EXISTS pilot_asset_artifacts_no_update
        BEFORE UPDATE ON pilot_asset_artifacts
        BEGIN
            SELECT RAISE(ABORT, 'pilot_asset_artifacts_append_only');
        END;
        CREATE TRIGGER IF NOT EXISTS pilot_asset_artifacts_no_delete
        BEFORE DELETE ON pilot_asset_artifacts
        BEGIN
            SELECT RAISE(ABORT, 'pilot_asset_artifacts_append_only');
        END;
        CREATE TABLE IF NOT EXISTS pilot_workbench_runs (
            run_id VARCHAR(64) PRIMARY KEY NOT NULL,
            product_line_id VARCHAR(120) NOT NULL,
            founder_goal TEXT NOT NULL,
            status VARCHAR(32) NOT NULL
                CHECK (status IN (
                    'planned',
                    'active',
                    'ready_for_decision',
                    'go',
                    'no_go'
                )),
            authority VARCHAR(64) NOT NULL
                CHECK (authority = 'pilot_non_authoritative'),
            mode VARCHAR(64) NOT NULL
                CHECK (mode = 'real_workbench_pilot'),
            source_path VARCHAR(120) NOT NULL
                CHECK (source_path = 'founder_control_center_real_workbench'),
            task_plan_hash VARCHAR(80) NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL
        );
        CREATE TABLE IF NOT EXISTS pilot_workbench_tasks (
            task_id VARCHAR(64) PRIMARY KEY NOT NULL,
            run_id VARCHAR(64) NOT NULL,
            step_index INTEGER NOT NULL CHECK (step_index >= 1),
            title VARCHAR(240) NOT NULL,
            executor_slot VARCHAR(80) NOT NULL,
            status VARCHAR(32) NOT NULL CHECK (status = 'planned'),
            expected_output TEXT NOT NULL,
            audit_summary TEXT NOT NULL,
            authority VARCHAR(64) NOT NULL
                CHECK (authority = 'pilot_non_authoritative'),
            created_at DATETIME NOT NULL,
            assigned_slot VARCHAR(80),
            assignment_status VARCHAR(32) NOT NULL DEFAULT 'unassigned'
                CHECK (assignment_status IN (
                    'unassigned',
                    'assigned',
                    'revised'
                )),
            assignment_note TEXT NOT NULL DEFAULT '',
            assigned_by VARCHAR(64),
            assigned_at DATETIME,
            updated_at DATETIME NOT NULL,
            FOREIGN KEY(run_id) REFERENCES pilot_workbench_runs(run_id)
                ON DELETE RESTRICT,
            UNIQUE(run_id, step_index)
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
    _validate_asset_schema(connection)
    component = connection.execute(
        "SELECT component, version, authority FROM pilot_schema_components"
        " WHERE component='assets'"
    ).fetchall()
    expected_component = [("assets", "vs002-1", PILOT_AUTHORITY)]
    if not component:
        connection.execute(
            "INSERT INTO pilot_schema_components"
            " (component, version, authority) VALUES (?, ?, ?)",
            expected_component[0],
        )
    elif component != expected_component:
        raise RuntimeError("pilot_asset_schema_version_invalid")
    _upgrade_real_workbench_schema(connection)
    _validate_real_workbench_schema(connection)
    workbench_component = connection.execute(
        "SELECT component, version, authority FROM pilot_schema_components"
        " WHERE component=?",
        (REAL_WORKBENCH_SCHEMA_COMPONENT,),
    ).fetchall()
    expected_workbench_component = [
        (
            REAL_WORKBENCH_SCHEMA_COMPONENT,
            REAL_WORKBENCH_SCHEMA_VERSION,
            PILOT_AUTHORITY,
        )
    ]
    if not workbench_component:
        connection.execute(
            "INSERT INTO pilot_schema_components"
            " (component, version, authority) VALUES (?, ?, ?)",
            expected_workbench_component[0],
        )
    elif workbench_component == [
        (REAL_WORKBENCH_SCHEMA_COMPONENT, "rs1a-1", PILOT_AUTHORITY)
    ]:
        connection.execute(
            "UPDATE pilot_schema_components SET version=?"
            " WHERE component=? AND authority=?",
            (
                REAL_WORKBENCH_SCHEMA_VERSION,
                REAL_WORKBENCH_SCHEMA_COMPONENT,
                PILOT_AUTHORITY,
            ),
        )
    elif workbench_component != expected_workbench_component:
        raise RuntimeError("pilot_real_workbench_schema_version_invalid")
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
