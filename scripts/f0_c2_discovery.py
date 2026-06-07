"""RT3 / F0-C2 read-only legacy discovery and classification.

The tool reads the operational SQLite database through an immutable, read-only
connection and treats ``private/work-queue`` as a filesystem projection. It
never imports backend startup code and never writes to either source.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
from typing import Any, Iterable, Mapping

import yaml


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = REPO_ROOT / "backend/data/ai_company_os.db"
DEFAULT_QUEUE_ROOT = REPO_ROOT / "private/work-queue"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "reports/migration"
RULE_SET_ID = "v0.47-f0-c2-legacy-classification"
RULE_SET_VERSION = "1.0.0"
REPORT_SCHEMA_VERSION = "v0.47-f0-c2-report-v1"
SOURCE_MANIFEST_VERSION = "v0.47-f0-c2-source-manifest-v1"
TOOL_VERSION = "v0.47-f0-c2-tool-v1"
COMPONENT_ORDER = ("db", "wal", "shm")
CLASSIFICATIONS = (
    "high_confidence",
    "provisional",
    "ambiguous",
    "conflicting",
    "noncanonical_history",
    "orphaned",
)
SIX_SYSTEMS = (
    "work_orders",
    "tasks",
    "task_pool",
    "execution_requests",
    "code_runtime_jobs",
    "private_work_queue",
)
RELATED_TABLES = (
    "approvals",
    "reviews",
    "artifacts",
    "execution_records",
    "asset_registry",
    "runtime_registry",
)
WORK_ORDER_ID_PATTERN = re.compile(r"^WO-[A-Z0-9]+(?:-[A-Z0-9]+)*$")
RULES = (
    {
        "id": "WO-COMPLETED-QUARANTINE",
        "source": "work_orders",
        "precondition": "status == completed",
        "classification": "noncanonical_history",
        "candidate_state": "waiting_review",
        "disposition": "legacy_completed_review_required",
    },
    {
        "id": "WO-IN-PROGRESS-NO-LIVE-ATTEMPT",
        "source": "work_orders",
        "precondition": "status == in_progress",
        "classification": "provisional_or_ambiguous",
        "candidate_state": None,
        "disposition": "do_not_fabricate_attempt",
    },
    {
        "id": "WO-CREATED-DRAFT-CANDIDATE",
        "source": "work_orders",
        "precondition": "status == created and identity is valid",
        "classification": "high_confidence",
        "candidate_state": "draft",
        "disposition": "future_mapping_candidate",
    },
    {
        "id": "WO-ROUTED-ASSIGNED-CONSERVATIVE",
        "source": "work_orders",
        "precondition": "status in routed, assigned",
        "classification": "provisional",
        "candidate_state": "draft_or_queued",
        "disposition": "prove_gates_before_queue",
    },
    {
        "id": "WO-FAILED-HISTORY",
        "source": "work_orders",
        "precondition": "status == failed",
        "classification": "noncanonical_history",
        "candidate_state": "waiting_review",
        "disposition": "preserve_terminal_claim_without_acceptance",
    },
    {
        "id": "WO-BLOCKED-CONSERVATIVE",
        "source": "work_orders",
        "precondition": "status == blocked",
        "classification": "high_confidence_or_conflicting",
        "candidate_state": "blocked",
        "disposition": "conflict_if_execution_or_result_evidence_exists",
    },
    {
        "id": "LEGACY-SUCCESS-NOT-WORKORDER-DONE",
        "source": "tasks,execution_requests,code_runtime_jobs",
        "precondition": "legacy terminal success claim",
        "classification": "noncanonical_history",
        "candidate_state": None,
        "disposition": "preserve_as_evidence_only",
    },
    {
        "id": "FILESYSTEM-PROJECTION-NONAUTHORITATIVE",
        "source": "private_work_queue",
        "precondition": "any queue file",
        "classification": "noncanonical_history_or_conflicting",
        "candidate_state": None,
        "disposition": "projection_or_legacy_transport",
    },
)


class DiscoveryError(RuntimeError):
    """Base class for fail-closed discovery failures."""


class SourceChanged(DiscoveryError):
    """Raised when a source changes during one discovery run."""


class ProtectedOutputRefused(DiscoveryError):
    """Raised when report output targets a protected source tree."""


def canonical_json_bytes(payload: object) -> bytes:
    """Return deterministic UTF-8 JSON with no trailing newline."""
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _stable_file_record(path: Path, *, name: str) -> dict[str, object]:
    if not path.exists():
        return {
            "name": name,
            "present": False,
            "size_bytes": None,
            "mtime_ns": None,
            "sha256": None,
        }
    if not path.is_file():
        raise SourceChanged(f"source_component_not_file:{name}")
    before = path.stat()
    digest = sha256_file(path)
    after = path.stat()
    before_signature = (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    )
    after_signature = (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    )
    if before_signature != after_signature:
        raise SourceChanged(f"source_changed_while_hashing:{name}")
    return {
        "name": name,
        "present": True,
        "size_bytes": int(after.st_size),
        "mtime_ns": int(after.st_mtime_ns),
        "sha256": digest,
    }


def _database_component_path(database: Path, role: str) -> Path:
    return database if role == "db" else Path(f"{database}-{role}")


def _journal_mode_from_header(database: Path) -> str:
    before = database.stat()
    with database.open("rb") as source:
        header = source.read(20)
    after = database.stat()
    if (
        before.st_dev,
        before.st_ino,
        before.st_size,
        before.st_mtime_ns,
    ) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        raise SourceChanged("database_changed_while_reading_header")
    if len(header) < 20 or header[:16] != b"SQLite format 3\x00":
        return "unknown"
    if header[18] == 2 or header[19] == 2:
        return "wal"
    if header[18] == 1 and header[19] == 1:
        return "delete"
    return "other"


def database_source_manifest(database_path: Path) -> dict[str, object]:
    database = database_path.expanduser().resolve()
    components = [
        _stable_file_record(
            _database_component_path(database, role),
            name=role,
        )
        for role in COMPONENT_ORDER
    ]
    payload: dict[str, object] = {
        "schema_version": SOURCE_MANIFEST_VERSION,
        "source_ref": "backend/data/ai_company_os.db"
        if database == DEFAULT_DATABASE.resolve()
        else "explicit_database_override",
        "canonical_path_sha256": sha256_bytes(str(database).encode("utf-8")),
        "journal_mode_from_header": _journal_mode_from_header(database),
        "components": components,
    }
    payload["manifest_hash"] = "sha256:" + sha256_bytes(canonical_json_bytes(payload))
    return payload


def queue_source_manifest(queue_root_path: Path) -> dict[str, object]:
    queue_root = queue_root_path.expanduser().resolve()
    entries: list[dict[str, object]] = []
    if queue_root.exists():
        for path in sorted(queue_root.rglob("*"), key=lambda item: item.as_posix()):
            relative = path.relative_to(queue_root).as_posix()
            if path.is_symlink():
                raise DiscoveryError(f"filesystem_queue_symlink_refused:{relative}")
            elif path.is_dir():
                stat_result = path.stat()
                entries.append(
                    {
                        "path": relative,
                        "type": "directory",
                        "mtime_ns": int(stat_result.st_mtime_ns),
                    }
                )
            elif path.is_file():
                record = _stable_file_record(path, name=relative)
                record["path"] = record.pop("name")
                record["type"] = "file"
                entries.append(record)
    payload: dict[str, object] = {
        "schema_version": SOURCE_MANIFEST_VERSION,
        "source_ref": "private/work-queue",
        "present": queue_root.exists(),
        "entries": entries,
    }
    payload["manifest_hash"] = "sha256:" + sha256_bytes(canonical_json_bytes(payload))
    return payload


def _read_only_authorizer(
    action: int,
    _arg1: str | None,
    _arg2: str | None,
    _database: str | None,
    _trigger: str | None,
) -> int:
    write_actions = {
        getattr(sqlite3, name)
        for name in (
            "SQLITE_INSERT",
            "SQLITE_UPDATE",
            "SQLITE_DELETE",
            "SQLITE_CREATE_INDEX",
            "SQLITE_CREATE_TABLE",
            "SQLITE_CREATE_TEMP_INDEX",
            "SQLITE_CREATE_TEMP_TABLE",
            "SQLITE_CREATE_TEMP_TRIGGER",
            "SQLITE_CREATE_TEMP_VIEW",
            "SQLITE_CREATE_TRIGGER",
            "SQLITE_CREATE_VIEW",
            "SQLITE_DROP_INDEX",
            "SQLITE_DROP_TABLE",
            "SQLITE_DROP_TEMP_INDEX",
            "SQLITE_DROP_TEMP_TABLE",
            "SQLITE_DROP_TEMP_TRIGGER",
            "SQLITE_DROP_TEMP_VIEW",
            "SQLITE_DROP_TRIGGER",
            "SQLITE_DROP_VIEW",
            "SQLITE_ALTER_TABLE",
            "SQLITE_REINDEX",
            "SQLITE_ANALYZE",
            "SQLITE_CREATE_VTABLE",
            "SQLITE_DROP_VTABLE",
        )
        if hasattr(sqlite3, name)
    }
    return sqlite3.SQLITE_DENY if action in write_actions else sqlite3.SQLITE_OK


def open_read_only_database(database_path: Path) -> sqlite3.Connection:
    database = database_path.expanduser().resolve()
    if not database.is_file():
        raise DiscoveryError("operational_database_not_found")
    connection = sqlite3.connect(
        f"{database.as_uri()}?mode=ro&immutable=1",
        uri=True,
    )
    connection.row_factory = sqlite3.Row
    connection.set_authorizer(_read_only_authorizer)
    return connection


def _table_exists(connection: sqlite3.Connection, table: str) -> bool:
    row = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone()
    return row is not None


def _rows(connection: sqlite3.Connection, table: str) -> list[dict[str, object]]:
    if not _table_exists(connection, table):
        return []
    return [dict(row) for row in connection.execute(f'SELECT * FROM "{table}"')]


def _status_distribution(
    rows: Iterable[Mapping[str, object]],
    field: str = "status",
) -> dict[str, int]:
    counts = Counter(str(row.get(field)) for row in rows)
    return dict(sorted(counts.items()))


def _schema_inventory(connection: sqlite3.Connection) -> dict[str, object]:
    objects = [
        dict(row)
        for row in connection.execute(
            """
            SELECT type, name, tbl_name, sql
            FROM sqlite_master
            WHERE name NOT LIKE 'sqlite_%'
            ORDER BY type, name
            """
        )
    ]
    normalized = canonical_json_bytes(objects)
    return {
        "object_count": len(objects),
        "schema_dump_sha256": sha256_bytes(normalized),
    }


def _database_settings(connection: sqlite3.Connection) -> dict[str, object]:
    def scalar(pragma: str) -> object:
        row = connection.execute(f"PRAGMA {pragma}").fetchone()
        return None if row is None else row[0]

    return {
        "query_only_connection": True,
        "sqlite_open_mode": "ro+immutable",
        "write_authorizer": "deny",
        "foreign_keys": scalar("foreign_keys"),
        "user_version": scalar("user_version"),
        "application_id": scalar("application_id"),
        "schema_version": scalar("schema_version"),
    }


def _has_value(row: Mapping[str, object], *fields: str) -> bool:
    return any(row.get(field) not in (None, "", [], {}) for field in fields)


def _path_signal(value: object) -> dict[str, object]:
    if not value:
        return {"declared": False, "scope": None, "existence": "not_applicable"}
    raw = str(value)
    expanded = Path(raw).expanduser()
    if not expanded.is_absolute():
        candidate = (REPO_ROOT / expanded).resolve()
        if candidate == REPO_ROOT or REPO_ROOT in candidate.parents:
            return {
                "declared": True,
                "scope": "repository",
                "existence": "present" if candidate.exists() else "missing",
            }
        return {"declared": True, "scope": "relative_external", "existence": "unverified"}
    candidate = expanded.resolve(strict=False)
    if candidate == REPO_ROOT or REPO_ROOT in candidate.parents:
        return {
            "declared": True,
            "scope": "repository",
            "existence": "present" if candidate.exists() else "missing",
        }
    return {"declared": True, "scope": "external", "existence": "unverified"}


def _work_order_evidence_tier(row: Mapping[str, object]) -> str:
    output = _has_value(row, "output_path")
    evidence = _has_value(row, "evidence_path")
    runtime = _has_value(row, "runtime_id", "assigned_agent")
    summary = _has_value(row, "result_summary", "artifacts_json")
    conflict = (
        int(row.get("attempt_count") or 0) == 0
        and _has_value(row, "completed_at", "result_summary", "error")
    )
    if conflict:
        return "D"
    if output and evidence and runtime:
        return "B"
    if output or evidence or summary:
        return "C"
    return "D"


def classify_work_order(row: Mapping[str, object]) -> dict[str, object]:
    work_order_id = str(row.get("work_order_id") or "")
    status = str(row.get("status") or "")
    attempt_count = int(row.get("attempt_count") or 0)
    execution_signal = _has_value(
        row,
        "runtime_id",
        "assigned_agent",
        "assigned_at",
        "openclaw_dispatched_at",
        "openclaw_claimed_at",
        "execution_log_json",
    ) or attempt_count > 0
    result_signal = _has_value(
        row,
        "output_path",
        "evidence_path",
        "result_summary",
        "artifacts_json",
        "error",
        "completed_at",
    )
    reasons: list[str] = []
    candidate_state: str | None = None
    disposition = "manual_reconciliation"

    if not WORK_ORDER_ID_PATTERN.fullmatch(work_order_id):
        classification = "orphaned"
        reasons.append("malformed_work_order_id")
    elif status == "completed":
        classification = "noncanonical_history"
        candidate_state = "waiting_review"
        disposition = "legacy_completed_review_required"
        reasons.extend(
            [
                "legacy_completed_is_not_canonical_done",
                "canonical_attempt_not_proven",
                "canonical_review_not_proven",
            ]
        )
    elif status == "failed":
        classification = "noncanonical_history"
        candidate_state = "waiting_review" if execution_signal else "blocked"
        disposition = "preserve_terminal_claim_for_review"
        reasons.append("legacy_failure_without_canonical_attempt_review")
    elif status == "in_progress":
        candidate_state = None
        disposition = "do_not_fabricate_live_attempt"
        if result_signal or _has_value(row, "completed_at"):
            classification = "conflicting"
            reasons.append("in_progress_has_terminal_or_result_signal")
        elif execution_signal:
            classification = "provisional"
            reasons.append("execution_hint_without_canonical_attempt")
        else:
            classification = "ambiguous"
            reasons.append("in_progress_without_execution_proof")
    elif status == "blocked":
        candidate_state = "blocked"
        if execution_signal or result_signal:
            classification = "conflicting"
            reasons.append("blocked_has_execution_or_result_signal")
        else:
            classification = "high_confidence"
            disposition = "blocked_candidate"
            reasons.append("pre_execution_blocked_fact_is_consistent")
    elif status == "created":
        classification = "high_confidence"
        candidate_state = "draft"
        disposition = "draft_candidate"
        reasons.append("explicit_identity_and_nonterminal_created_state")
    elif status in {"routed", "assigned"}:
        classification = "provisional"
        candidate_state = "draft_or_queued"
        disposition = "prove_gates_before_queue"
        reasons.append("legacy_routing_or_assignment_does_not_prove_queue_gate")
    else:
        classification = "ambiguous"
        reasons.append("unknown_legacy_status")

    if row.get("approval_required") and not row.get("approval_id"):
        reasons.append("approval_required_without_link")
        if classification == "high_confidence":
            classification = "provisional"
    if attempt_count == 0 and result_signal:
        reasons.append("result_signal_without_attempt_count")
        if status not in {"completed", "failed"}:
            classification = "conflicting"

    return {
        "source_system": "work_orders",
        "source_id": work_order_id,
        "legacy_status": status,
        "classification": classification,
        "canonical_candidate_state": candidate_state,
        "recommended_disposition": disposition,
        "reason_codes": sorted(set(reasons)),
        "attempt_count": attempt_count,
        "approval_required": bool(row.get("approval_required")),
        "approval_link_declared": bool(row.get("approval_id")),
        "runtime_claim_declared": bool(row.get("runtime_id")),
        "assigned_actor_declared": bool(row.get("assigned_agent")),
        "execution_signal": execution_signal,
        "result_signal": result_signal,
        "output_ref": _path_signal(row.get("output_path")),
        "evidence_ref": _path_signal(row.get("evidence_path")),
        "evidence_tier": _work_order_evidence_tier(row),
        "created_at": row.get("created_at"),
        "assigned_at": row.get("assigned_at"),
        "completed_at": row.get("completed_at"),
    }


def _legacy_record(
    source_system: str,
    source_id: object,
    legacy_status: object,
    classification: str,
    reason_codes: Iterable[str],
    *,
    candidate_state: str | None = None,
    disposition: str = "preserve_as_provenance",
) -> dict[str, object]:
    return {
        "source_system": source_system,
        "source_id": str(source_id),
        "legacy_status": None if legacy_status is None else str(legacy_status),
        "classification": classification,
        "canonical_candidate_state": candidate_state,
        "recommended_disposition": disposition,
        "reason_codes": sorted(set(reason_codes)),
    }


def classify_tasks(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    records = []
    for row in rows:
        status = str(row.get("status") or "")
        if status == "completed":
            records.append(
                _legacy_record(
                    "tasks",
                    row.get("id"),
                    status,
                    "noncanonical_history",
                    ["legacy_task_completion_is_not_work_order_acceptance"],
                )
            )
        elif status in {"running", "in_progress"}:
            records.append(
                _legacy_record(
                    "tasks",
                    row.get("id"),
                    status,
                    "provisional",
                    ["legacy_task_execution_without_canonical_attempt"],
                )
            )
        else:
            records.append(
                _legacy_record(
                    "tasks",
                    row.get("id"),
                    status,
                    "high_confidence",
                    ["legacy_task_fact_preserved"],
                )
            )
    return records


def classify_task_pool(
    rows: list[dict[str, object]],
    reviews: list[dict[str, object]],
) -> list[dict[str, object]]:
    review_results: dict[str, set[str]] = defaultdict(set)
    for review in reviews:
        review_results[str(review.get("task_id"))].add(str(review.get("result")))
    records = []
    for row in rows:
        source_id = str(row.get("id"))
        status = str(row.get("status") or "")
        linked_results = review_results.get(source_id, set())
        if len(linked_results) > 1:
            classification = "conflicting"
            reasons = ["multiple_materially_different_legacy_reviews"]
            disposition = "manual_review_reconciliation"
        elif status == "approval_required":
            classification = "provisional"
            reasons = ["approval_gate_candidate_without_canonical_work_order"]
            disposition = "future_intake_or_work_order_candidate"
        elif status == "review":
            classification = "provisional"
            reasons = ["legacy_review_state_without_canonical_attempt"]
            disposition = "preserve_review_candidate"
        elif status in {"completed", "done"}:
            classification = "noncanonical_history"
            reasons = ["legacy_task_pool_terminal_state_not_canonical_done"]
            disposition = "preserve_as_provenance"
        else:
            classification = "ambiguous"
            reasons = ["unknown_task_pool_mapping"]
            disposition = "manual_reconciliation"
        record = _legacy_record(
            "task_pool",
            source_id,
            status,
            classification,
            reasons,
            disposition=disposition,
        )
        record["legacy_review_results"] = sorted(linked_results)
        records.append(record)
    return records


def classify_execution_requests(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    records = []
    for row in rows:
        status = str(row.get("status") or "")
        reasons = ["execution_request_is_command_history_not_execution_aggregate"]
        if status == "verified_success":
            reasons.append("verified_success_does_not_equal_work_order_done")
        records.append(
            _legacy_record(
                "execution_requests",
                row.get("id"),
                status,
                "noncanonical_history",
                reasons,
            )
        )
    return records


def classify_code_runtime_jobs(
    rows: list[dict[str, object]],
) -> list[dict[str, object]]:
    source_groups: dict[tuple[str, str], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        source_groups[(str(row.get("source_type")), str(row.get("source_id")))].append(row)
    records = []
    for row in rows:
        status = str(row.get("status") or "")
        siblings = source_groups[(str(row.get("source_type")), str(row.get("source_id")))]
        sibling_statuses = {str(item.get("status")) for item in siblings}
        if "running" in sibling_statuses and "success" in sibling_statuses:
            classification = "conflicting"
            reasons = ["same_source_has_running_and_success_jobs"]
            disposition = "reconstruct_retry_boundaries"
        elif status == "success":
            classification = "noncanonical_history"
            reasons = ["runtime_success_is_attempt_candidate_not_work_order_done"]
            disposition = "attempt_evidence_candidate"
        elif status in {"queued", "running"}:
            classification = "provisional"
            reasons = ["legacy_runtime_job_without_canonical_attempt"]
            disposition = "do_not_treat_as_live_attempt"
        else:
            classification = "ambiguous"
            reasons = ["unknown_code_runtime_job_status"]
            disposition = "manual_reconciliation"
        records.append(
            _legacy_record(
                "code_runtime_jobs",
                row.get("id"),
                status,
                classification,
                reasons,
                disposition=disposition,
            )
        )
    return records


def _load_structured_file(path: Path) -> object:
    before = _stable_file_record(path, name=path.name)
    try:
        if path.suffix.lower() == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
        else:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, yaml.YAMLError) as error:
        raise DiscoveryError(f"structured_parse_failed:{path.name}:{type(error).__name__}") from error
    after = _stable_file_record(path, name=path.name)
    if before != after:
        raise SourceChanged(f"queue_file_changed_while_parsing:{path.name}")
    return payload


def classify_private_queue(queue_root_path: Path) -> list[dict[str, object]]:
    queue_root = queue_root_path.expanduser().resolve()
    records: list[dict[str, object]] = []
    for path in sorted(queue_root.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_symlink():
            raise DiscoveryError(
                f"filesystem_queue_symlink_refused:{path.relative_to(queue_root).as_posix()}"
            )
        if not path.is_file() or path.suffix.lower() not in {".yaml", ".yml", ".json"}:
            continue
        relative = path.relative_to(queue_root).as_posix()
        payload = _load_structured_file(path)
        mapping = payload if isinstance(payload, dict) else {}
        directory_state = relative.split("/", 1)[0]
        declared_status = mapping.get("status")
        source_id = (
            mapping.get("work_id")
            or mapping.get("attempt_id")
            or mapping.get("audit_packet_id")
            or relative
        )
        reasons = [
            "filesystem_queue_is_projection_or_legacy_transport",
            "no_backend_work_order_identity_proven",
        ]
        if declared_status and directory_state in {
            "inbox",
            "claimed",
            "running",
            "waiting_review",
            "done",
            "failed",
        } and str(declared_status).lower() != directory_state:
            classification = "conflicting"
            reasons.append("directory_state_conflicts_with_declared_status")
            disposition = "preserve_and_reconcile_projection"
        else:
            classification = "noncanonical_history"
            disposition = "preserve_as_projection_evidence"
        records.append(
            {
                **_legacy_record(
                    "private_work_queue",
                    source_id,
                    declared_status or directory_state,
                    classification,
                    reasons,
                    disposition=disposition,
                ),
                "relative_path": relative,
                "directory_state": directory_state,
                "record_kind": "mapping" if isinstance(payload, dict) else "sequence",
            }
        )
    return records


def classify_related_rows(
    table: str,
    rows: list[dict[str, object]],
    task_pool_ids: set[str],
    execution_record_ids: set[str],
) -> list[dict[str, object]]:
    records = []
    for row in rows:
        source_id = row.get("id", row.get("runtime_id", "unknown"))
        status = row.get("status", row.get("result", row.get("artifact_status")))
        classification = "noncanonical_history"
        reasons = [f"legacy_{table}_preserved_as_supporting_evidence"]
        disposition = "preserve_as_provenance"
        if table == "approvals":
            target_type = str(row.get("target_type"))
            target_id = str(row.get("target_id"))
            if target_type == "task" and target_id not in task_pool_ids:
                classification = "orphaned"
                reasons.append("approval_target_not_found_in_task_pool")
        elif table == "reviews":
            if str(row.get("task_id")) not in task_pool_ids:
                classification = "orphaned"
                reasons.append("review_target_not_found_in_task_pool")
        elif table == "artifacts":
            if str(row.get("run_id")) not in execution_record_ids:
                classification = "orphaned"
                reasons.append("artifact_run_not_found")
            else:
                classification = "high_confidence"
                reasons.append("artifact_run_link_is_explicit")
                if str(row.get("data_source")) == "mock":
                    reasons.append("artifact_provenance_is_mock")
        records.append(
            _legacy_record(
                table,
                source_id,
                status,
                classification,
                reasons,
                disposition=disposition,
            )
        )
    return records


def _timestamp_range(
    rows: Iterable[Mapping[str, object]],
    fields: Iterable[str],
) -> dict[str, object]:
    values = [
        str(row.get(field))
        for row in rows
        for field in fields
        if row.get(field) not in (None, "")
    ]
    return {"minimum": min(values) if values else None, "maximum": max(values) if values else None}


def _identity_range(
    rows: Iterable[Mapping[str, object]],
    fields: Iterable[str],
) -> dict[str, object]:
    values = []
    for row in rows:
        for field in fields:
            if row.get(field) not in (None, ""):
                values.append(row[field])
                break
    if not values:
        return {"minimum": None, "maximum": None}
    if all(isinstance(value, int) for value in values):
        return {"minimum": min(values), "maximum": max(values)}
    normalized = sorted(str(value) for value in values)
    return {"minimum": normalized[0], "maximum": normalized[-1]}


def build_report(
    database_path: Path,
    queue_root_path: Path,
    *,
    observed_at: str | None = None,
) -> dict[str, object]:
    run_started_at = observed_at or datetime.now(timezone.utc).isoformat(
        timespec="microseconds"
    ).replace("+00:00", "Z")
    database_before = database_source_manifest(database_path)
    live_components = {
        component["name"]
        for component in database_before["components"]
        if component["name"] in {"wal", "shm"} and component["present"]
    }
    if live_components:
        raise DiscoveryError(
            "live_sqlite_sidecars_require_separately_authorized_quiesced_copy:"
            + ",".join(sorted(live_components))
        )
    queue_before = queue_source_manifest(queue_root_path)

    with open_read_only_database(database_path) as connection:
        schema = _schema_inventory(connection)
        settings = _database_settings(connection)
        tables = {
            table: _rows(connection, table)
            for table in SIX_SYSTEMS[:-1] + RELATED_TABLES
        }

    work_orders = [classify_work_order(row) for row in tables["work_orders"]]
    reviews = tables["reviews"]
    system_records = {
        "work_orders": work_orders,
        "tasks": classify_tasks(tables["tasks"]),
        "task_pool": classify_task_pool(tables["task_pool"], reviews),
        "execution_requests": classify_execution_requests(tables["execution_requests"]),
        "code_runtime_jobs": classify_code_runtime_jobs(tables["code_runtime_jobs"]),
        "private_work_queue": classify_private_queue(queue_root_path),
    }
    task_pool_ids = {str(row.get("id")) for row in tables["task_pool"]}
    execution_record_ids = {str(row.get("id")) for row in tables["execution_records"]}
    related_records = {
        table: classify_related_rows(
            table,
            tables[table],
            task_pool_ids,
            execution_record_ids,
        )
        for table in RELATED_TABLES
    }

    database_after = database_source_manifest(database_path)
    queue_after = queue_source_manifest(queue_root_path)
    if database_before != database_after:
        raise SourceChanged("database_source_changed_during_discovery")
    if queue_before != queue_after:
        raise SourceChanged("filesystem_queue_changed_during_discovery")

    all_records = [
        record
        for records in list(system_records.values()) + list(related_records.values())
        for record in records
    ]
    completed_records = [
        record for record in work_orders if record["legacy_status"] == "completed"
    ]
    classification_counts = Counter(
        str(record["classification"]) for record in all_records
    )
    work_order_classification_counts = Counter(
        str(record["classification"]) for record in work_orders
    )
    status_counts = {
        table: _status_distribution(tables[table])
        for table in SIX_SYSTEMS[:-1]
    }
    status_counts["private_work_queue"] = _status_distribution(
        system_records["private_work_queue"],
        "legacy_status",
    )
    identity_ranges = {
        table: _identity_range(
            tables[table],
            (
                "work_order_id",
                "id",
                "runtime_id",
            ),
        )
        for table in SIX_SYSTEMS[:-1] + RELATED_TABLES
    }
    identity_ranges["private_work_queue"] = _identity_range(
        system_records["private_work_queue"],
        ("source_id",),
    )
    rule_payload = {
        "rule_set_id": RULE_SET_ID,
        "rule_set_version": RULE_SET_VERSION,
        "rules": RULES,
    }
    rule_payload["rule_set_hash"] = "sha256:" + sha256_bytes(
        canonical_json_bytes(rule_payload)
    )
    source_manifest = {
        "database": database_before,
        "private_work_queue": queue_before,
        "schema": schema,
        "database_settings": settings,
    }
    source_manifest["combined_source_hash"] = "sha256:" + sha256_bytes(
        canonical_json_bytes(source_manifest)
    )
    report: dict[str, object] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": run_started_at,
        "mode": "read_only_discovery",
        "run_metadata": {
            "actor": "local-founder",
            "tool_version": TOOL_VERSION,
            "started_at": run_started_at,
            "finished_at": observed_at
            or datetime.now(timezone.utc).isoformat(timespec="microseconds").replace(
                "+00:00", "Z"
            ),
            "database_override": database_path.expanduser().resolve()
            != DEFAULT_DATABASE.resolve(),
            "queue_override": queue_root_path.expanduser().resolve()
            != DEFAULT_QUEUE_ROOT.resolve(),
        },
        "source_manifest": source_manifest,
        "rule_set": rule_payload,
        "summary": {
            "six_system_counts": {
                name: len(system_records[name]) for name in SIX_SYSTEMS
            },
            "related_table_counts": {
                name: len(related_records[name]) for name in RELATED_TABLES
            },
            "status_distributions": status_counts,
            "identity_ranges": identity_ranges,
            "classification_counts": {
                name: classification_counts.get(name, 0) for name in CLASSIFICATIONS
            },
            "work_order_classification_counts": {
                name: work_order_classification_counts.get(name, 0)
                for name in CLASSIFICATIONS
            },
            "legacy_completed_count": len(completed_records),
            "legacy_completed_quarantine_count": sum(
                1
                for record in completed_records
                if record["recommended_disposition"]
                == "legacy_completed_review_required"
                and record["canonical_candidate_state"] == "waiting_review"
                and record["classification"] == "noncanonical_history"
            ),
            "legacy_completed_promoted_to_done_count": 0,
            "work_order_timestamp_range": _timestamp_range(
                tables["work_orders"],
                ("created_at", "assigned_at", "completed_at"),
            ),
            "source_rows_rewritten": 0,
        },
        "systems": system_records,
        "related_evidence": related_records,
    }
    stable_payload = dict(report)
    stable_payload.pop("generated_at")
    stable_payload.pop("run_metadata")
    report["classification_hash"] = "sha256:" + sha256_bytes(
        canonical_json_bytes(stable_payload)
    )
    return report


def source_manifest_document(report: Mapping[str, object]) -> dict[str, object]:
    return {
        "schema_version": SOURCE_MANIFEST_VERSION,
        "mode": report["mode"],
        "generated_at": report["generated_at"],
        "source_manifest": report["source_manifest"],
        "rule_set_hash": report["rule_set"]["rule_set_hash"],  # type: ignore[index]
        "classification_hash": report["classification_hash"],
    }


def render_markdown(report: Mapping[str, object]) -> str:
    summary = report["summary"]  # type: ignore[assignment]
    six_counts = summary["six_system_counts"]  # type: ignore[index]
    classifications = summary["classification_counts"]  # type: ignore[index]
    work_order_classifications = summary["work_order_classification_counts"]  # type: ignore[index]
    status_distributions = summary["status_distributions"]  # type: ignore[index]
    lines = [
        "# v0.47 F0-C2 Read-only Discovery & Classification",
        "",
        f"- Generated at: `{report['generated_at']}`",
        f"- Mode: `{report['mode']}`",
        f"- Classification hash: `{report['classification_hash']}`",
        f"- Rule set: `{report['rule_set']['rule_set_id']}@{report['rule_set']['rule_set_version']}`",  # type: ignore[index]
        "- Source rows rewritten: `0`",
        "",
        "## Gate Result",
        "",
        f"- WorkOrders discovered: `{six_counts['work_orders']}`",
        f"- Legacy completed discovered: `{summary['legacy_completed_count']}`",
        f"- Completed quarantined as `legacy_completed_review_required`: `{summary['legacy_completed_quarantine_count']}`",
        f"- Legacy completed promoted directly to canonical done: `{summary['legacy_completed_promoted_to_done_count']}`",
        "",
        "## Six-system Inventory",
        "",
        "| System | Records | Legacy status distribution |",
        "|---|---:|---|",
    ]
    for system in SIX_SYSTEMS:
        distribution = ", ".join(
            f"{key}={value}"
            for key, value in status_distributions[system].items()
        )
        lines.append(f"| `{system}` | {six_counts[system]} | {distribution or 'n/a'} |")
    lines.extend(
        [
            "",
            "## Classification Summary",
            "",
            "| Classification | All sources | WorkOrders |",
            "|---|---:|---:|",
        ]
    )
    for classification in CLASSIFICATIONS:
        lines.append(
            f"| `{classification}` | {classifications[classification]} | "
            f"{work_order_classifications[classification]} |"
        )
    lines.extend(
        [
            "",
            "## Conservative Decisions",
            "",
            "- Every legacy WorkOrder with `status=completed` remains "
            "`noncanonical_history` and is a `waiting_review` candidate.",
            "- No live Attempt is fabricated from legacy `in_progress`, runtime jobs, "
            "or filesystem queue state.",
            "- CodeRuntimeJob success, ExecutionRequest verified success, Task completion, "
            "and filesystem `done` are evidence only, never canonical WorkOrder `done`.",
            "- `private/work-queue` is treated as projection / legacy compatibility "
            "transport, not authoritative state.",
            "- Missing, contradictory, or unresolvable facts remain visible as "
            "`ambiguous`, `conflicting`, or `orphaned`.",
            "",
            "## Source Integrity",
            "",
            f"- Database manifest: `{report['source_manifest']['database']['manifest_hash']}`",  # type: ignore[index]
            f"- Queue manifest: `{report['source_manifest']['private_work_queue']['manifest_hash']}`",  # type: ignore[index]
            f"- Combined source hash: `{report['source_manifest']['combined_source_hash']}`",  # type: ignore[index]
            f"- Schema dump SHA-256: `{report['source_manifest']['schema']['schema_dump_sha256']}`",  # type: ignore[index]
            "",
            "The JSON report contains the complete per-record classification and reason codes.",
            "",
        ]
    )
    return "\n".join(lines)


def _assert_output_allowed(output_dir: Path) -> Path:
    output = output_dir.expanduser().resolve()
    protected = (
        (REPO_ROOT / "backend/data").resolve(),
        (REPO_ROOT / "private").resolve(),
    )
    if any(output == root or root in output.parents for root in protected):
        raise ProtectedOutputRefused("report_output_must_not_target_protected_source")
    return output


def _atomic_write(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def write_reports(report: Mapping[str, object], output_dir: Path) -> list[Path]:
    output = _assert_output_allowed(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    targets = [
        output / "v0.47-F0-C2-source-manifest.json",
        output / "v0.47-F0-C2-classification.json",
        output / "v0.47-F0-C2-classification.md",
    ]
    _atomic_write(
        targets[0],
        json.dumps(
            source_manifest_document(report),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ).encode("utf-8")
        + b"\n",
    )
    _atomic_write(
        targets[1],
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        + b"\n",
    )
    _atomic_write(targets[2], render_markdown(report).encode("utf-8"))
    return targets


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--queue-root", type=Path, default=DEFAULT_QUEUE_ROOT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--observed-at")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_args(argv)
    report = build_report(
        arguments.database,
        arguments.queue_root,
        observed_at=arguments.observed_at,
    )
    targets = write_reports(report, arguments.output_dir)
    print(
        json.dumps(
            {
                "status": "ok",
                "mode": "read_only_discovery",
                "classification_hash": report["classification_hash"],
                "legacy_completed_count": report["summary"]["legacy_completed_count"],  # type: ignore[index]
                "legacy_completed_quarantine_count": report["summary"][  # type: ignore[index]
                    "legacy_completed_quarantine_count"
                ],
                "reports": [str(path) for path in targets],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
