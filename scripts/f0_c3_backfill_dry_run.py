"""RT4 / F0-C3 quarantine backfill dry-run planner.

This command binds a deterministic proposal to the accepted F0-C2 source and
classification hashes. It reads the operational database through the F0-C2
read-only harness, writes reports only, and never applies schema or data
changes.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
from types import ModuleType
from typing import Any, Mapping


REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATABASE = REPO_ROOT / "backend/data/ai_company_os.db"
DEFAULT_QUEUE_ROOT = REPO_ROOT / "private/work-queue"
DEFAULT_CLASSIFICATION_REPORT = (
    REPO_ROOT / "reports/migration/v0.47-F0-C2-classification.json"
)
DEFAULT_OUTPUT_DIR = REPO_ROOT / "reports/migration"

REPORT_SCHEMA_VERSION = "v0.47-f0-c3-dry-run-v1"
RULE_SET_ID = "v0.47-f0-c3-quarantine-backfill"
RULE_SET_VERSION = "1.0.0"
TOOL_VERSION = "v0.47-f0-c3-tool-v1"

DEFAULT_TENANT_ID = "ten_local"
DEFAULT_TENANT_NAME = "Local Organization"
DEFAULT_WORKSPACE_ID = "wsp_personal"
DEFAULT_WORKSPACE_NAME = "Personal Workspace"
DEFAULT_USER_ID = "usr_local_founder"
DEFAULT_MEMBERSHIP_ID = "mem_local_founder_personal"
LOCAL_FOUNDER_PRINCIPAL_ID = "local-founder"
MIGRATION_PRINCIPAL_ID = "migration-f0-c3"
DEFAULT_SCOPE_KEY = f"{DEFAULT_TENANT_ID}:{DEFAULT_WORKSPACE_ID}"
DEFAULT_VISIBILITY = "restricted"

STATE_RULES = {
    "created": {
        "canonical_state": "draft",
        "rule_id": "WO-CREATED-TO-DRAFT",
    },
    "blocked": {
        "canonical_state": "blocked",
        "rule_id": "WO-BLOCKED-TO-BLOCKED",
    },
    "completed": {
        "canonical_state": "waiting_review",
        "rule_id": "WO-COMPLETED-TO-QUARANTINE",
    },
    "failed": {
        "canonical_state": "waiting_review",
        "rule_id": "WO-FAILED-TO-WAITING-REVIEW",
    },
    "routed": {
        "canonical_state": None,
        "rule_id": "WO-ROUTED-UNRESOLVED",
    },
    "assigned": {
        "canonical_state": None,
        "rule_id": "WO-ASSIGNED-UNRESOLVED",
    },
    "in_progress": {
        "canonical_state": None,
        "rule_id": "WO-IN-PROGRESS-NO-ATTEMPT",
    },
}


class DryRunError(RuntimeError):
    """Base class for fail-closed dry-run errors."""


class ClassificationReportMismatch(DryRunError):
    """Raised when the accepted F0-C2 report no longer matches its source."""


class ProtectedOutputRefused(DryRunError):
    """Raised when reports target a protected source tree."""


def canonical_json_bytes(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_payload(payload: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def deterministic_id(prefix: str, *parts: object, length: int = 24) -> str:
    digest = hashlib.sha256(canonical_json_bytes(list(parts))).hexdigest()
    return f"{prefix}_{digest[:length]}"


def load_f0_c2_module() -> ModuleType:
    path = REPO_ROOT / "scripts/f0_c2_discovery.py"
    spec = importlib.util.spec_from_file_location("f0_c2_for_f0_c3", path)
    if spec is None or spec.loader is None:
        raise DryRunError("f0_c2_discovery_module_unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_classification_report(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise DryRunError("classification_report_unreadable") from error
    if payload.get("schema_version") != "v0.47-f0-c2-report-v1":
        raise ClassificationReportMismatch("classification_report_schema_mismatch")
    return payload


def _work_order_rows(
    discovery: ModuleType,
    database_path: Path,
) -> dict[str, dict[str, object]]:
    with discovery.open_read_only_database(database_path) as connection:
        rows = discovery._rows(connection, "work_orders")
    return {str(row["work_order_id"]): row for row in rows}


def _verify_f0_c2_binding(
    discovery: ModuleType,
    classification: Mapping[str, Any],
    database_path: Path,
    queue_root_path: Path,
) -> None:
    current = discovery.build_report(
        database_path,
        queue_root_path,
        observed_at="binding-check",
    )
    if current["classification_hash"] != classification.get("classification_hash"):
        raise ClassificationReportMismatch("classification_hash_mismatch")
    accepted_manifest = classification["source_manifest"]
    current_manifest = current["source_manifest"]
    if (
        accepted_manifest["combined_source_hash"]
        != current_manifest["combined_source_hash"]
    ):
        raise ClassificationReportMismatch("combined_source_hash_mismatch")
    if (
        accepted_manifest["database"]["components"][0]["sha256"]
        != current_manifest["database"]["components"][0]["sha256"]
    ):
        raise ClassificationReportMismatch("operational_database_hash_mismatch")


def root_record_plan() -> list[dict[str, object]]:
    return [
        {
            "operation": "proposed_insert",
            "object_type": "Tenant",
            "object_id": DEFAULT_TENANT_ID,
            "fields": {
                "name": DEFAULT_TENANT_NAME,
                "slug": "local",
                "status": "active",
                "created_by": LOCAL_FOUNDER_PRINCIPAL_ID,
                "updated_by": LOCAL_FOUNDER_PRINCIPAL_ID,
            },
        },
        {
            "operation": "proposed_insert",
            "object_type": "Workspace",
            "object_id": DEFAULT_WORKSPACE_ID,
            "fields": {
                "tenant_id": DEFAULT_TENANT_ID,
                "name": DEFAULT_WORKSPACE_NAME,
                "slug": "personal",
                "status": "active",
                "created_by": LOCAL_FOUNDER_PRINCIPAL_ID,
                "updated_by": LOCAL_FOUNDER_PRINCIPAL_ID,
            },
        },
        {
            "operation": "proposed_insert",
            "object_type": "User",
            "object_id": DEFAULT_USER_ID,
            "fields": {
                "principal_name": LOCAL_FOUNDER_PRINCIPAL_ID,
                "display_name": "Founder",
                "status": "active",
            },
        },
        {
            "operation": "proposed_insert",
            "object_type": "Membership",
            "object_id": DEFAULT_MEMBERSHIP_ID,
            "fields": {
                "tenant_id": DEFAULT_TENANT_ID,
                "workspace_id": DEFAULT_WORKSPACE_ID,
                "user_id": DEFAULT_USER_ID,
                "scope_key": DEFAULT_SCOPE_KEY,
                "status": "active",
                "role": "Owner",
            },
        },
    ]


def _source_row_hash(row: Mapping[str, object]) -> str:
    return sha256_payload(
        {
            key: row[key]
            for key in sorted(row)
        }
    )


def _anomaly_type(classification: Mapping[str, object], proposed_state: object) -> str:
    legacy_status = str(classification["legacy_status"])
    if legacy_status == "completed":
        return "legacy_completed_review_required"
    if legacy_status == "failed":
        return "legacy_failed_review_required"
    if proposed_state is None:
        return "canonical_state_unresolved"
    if classification["classification"] == "conflicting":
        return "legacy_state_conflict"
    return "migration_review_required"


def _anomaly_severity(classification: Mapping[str, object], proposed_state: object) -> str:
    if classification["classification"] in {"conflicting", "orphaned"}:
        return "high"
    if proposed_state is None:
        return "high"
    if classification.get("evidence_tier") == "D":
        return "warning"
    return "info"


def _needs_anomaly(
    classification: Mapping[str, object],
    proposed_state: object,
) -> bool:
    return (
        proposed_state is None
        or classification["legacy_status"] in {"completed", "failed"}
        or classification["classification"]
        in {"ambiguous", "conflicting", "orphaned"}
    )


def plan_work_order(
    classification: Mapping[str, object],
    source_row: Mapping[str, object],
    *,
    migration_batch_id: str,
) -> tuple[dict[str, object], dict[str, object] | None]:
    work_order_id = str(classification["source_id"])
    legacy_status = str(classification["legacy_status"])
    if legacy_status not in STATE_RULES:
        raise DryRunError(f"unhandled_legacy_status:{legacy_status}")
    state_rule = STATE_RULES[legacy_status]
    canonical_state = state_rule["canonical_state"]
    source_hash = _source_row_hash(source_row)
    mapping_id = deterministic_id(
        "map",
        migration_batch_id,
        "work_orders",
        work_order_id,
        source_hash,
    )
    proposed_fields = {
        "tenant_id": DEFAULT_TENANT_ID,
        "workspace_id": DEFAULT_WORKSPACE_ID,
        "created_by": MIGRATION_PRINCIPAL_ID,
        "updated_by": MIGRATION_PRINCIPAL_ID,
        "visibility": DEFAULT_VISIBILITY,
        "canonical_state": canonical_state,
        "row_version": 1,
        "parallel_attempts_allowed": False,
        "max_attempts": None,
        "canonicalized_at": None,
        "canonical_migration_batch_id": migration_batch_id,
        "legacy_status_snapshot": legacy_status,
        "terminal_at": None,
    }
    mapping = {
        "legacy_mapping_id": mapping_id,
        "source_system": "work_orders",
        "source_type": "WorkOrder",
        "source_key": work_order_id,
        "source_state": legacy_status,
        "source_hash": source_hash,
        "canonical_object_type": "WorkOrder",
        "canonical_object_id": work_order_id,
        "classification": classification["classification"],
        "mapping_rule": state_rule["rule_id"],
        "migration_batch_id": migration_batch_id,
        "scope_plan": {
            "tenant_id": DEFAULT_TENANT_ID,
            "workspace_id": DEFAULT_WORKSPACE_ID,
            "scope_key": DEFAULT_SCOPE_KEY,
        },
        "proposed_fields": proposed_fields,
        "quarantine_reason": (
            "legacy_completed_review_required"
            if legacy_status == "completed"
            else None
        ),
        "evidence_tier": classification.get("evidence_tier"),
        "reason_codes": classification.get("reason_codes", []),
        "legacy_fields_unchanged": ["status", "attempt_count", "output_path", "evidence_path"],
    }

    anomaly = None
    if _needs_anomaly(classification, canonical_state):
        anomaly_type = _anomaly_type(classification, canonical_state)
        anomaly_id = deterministic_id(
            "ano",
            migration_batch_id,
            work_order_id,
            anomaly_type,
            source_hash,
        )
        anomaly = {
            "anomaly_id": anomaly_id,
            "migration_batch_id": migration_batch_id,
            "tenant_id": DEFAULT_TENANT_ID,
            "workspace_id": DEFAULT_WORKSPACE_ID,
            "source_system": "work_orders",
            "source_type": "WorkOrder",
            "source_key": work_order_id,
            "anomaly_type": anomaly_type,
            "severity": _anomaly_severity(classification, canonical_state),
            "status": "open",
            "details": {
                "legacy_status": legacy_status,
                "classification": classification["classification"],
                "evidence_tier": classification.get("evidence_tier"),
                "reason_codes": classification.get("reason_codes", []),
                "proposed_canonical_state": canonical_state,
                "recommended_disposition": classification.get(
                    "recommended_disposition"
                ),
            },
        }
    return mapping, anomaly


def _validate_plan(plan: Mapping[str, Any]) -> None:
    summary = plan["summary"]
    mappings = plan["work_order_mappings"]
    anomalies = plan["reconciliation_anomalies"]
    if len(mappings) != 497:
        raise DryRunError("work_order_count_conservation_failed")
    if len({item["source_key"] for item in mappings}) != len(mappings):
        raise DryRunError("duplicate_work_order_mapping")
    if len({item["legacy_mapping_id"] for item in mappings}) != len(mappings):
        raise DryRunError("duplicate_legacy_mapping_id")
    if len({item["anomaly_id"] for item in anomalies}) != len(anomalies):
        raise DryRunError("duplicate_anomaly_id")
    if any(
        item["scope_plan"]["tenant_id"] != DEFAULT_TENANT_ID
        or item["scope_plan"]["workspace_id"] != DEFAULT_WORKSPACE_ID
        for item in mappings
    ):
        raise DryRunError("cross_tenant_scope_candidate")
    completed = [
        item for item in mappings if item["source_state"] == "completed"
    ]
    if len(completed) != 168:
        raise DryRunError("legacy_completed_count_mismatch")
    if any(
        item["proposed_fields"]["canonical_state"] != "waiting_review"
        or item["quarantine_reason"] != "legacy_completed_review_required"
        for item in completed
    ):
        raise DryRunError("legacy_completed_quarantine_failed")
    if summary["direct_canonical_done_count"] != 0:
        raise DryRunError("direct_canonical_done_forbidden")
    if summary["source_rows_rewritten"] != 0:
        raise DryRunError("dry_run_source_rewrite_forbidden")


def build_plan(
    database_path: Path,
    queue_root_path: Path,
    classification_report_path: Path,
    *,
    observed_at: str | None = None,
) -> dict[str, object]:
    discovery = load_f0_c2_module()
    classification = load_classification_report(classification_report_path)
    _verify_f0_c2_binding(
        discovery,
        classification,
        database_path,
        queue_root_path,
    )
    source_rows = _work_order_rows(discovery, database_path)
    classification_rows = classification["systems"]["work_orders"]
    if set(source_rows) != {
        str(item["source_id"]) for item in classification_rows
    }:
        raise ClassificationReportMismatch("work_order_identity_set_mismatch")

    rule_bundle = {
        "rule_set_id": RULE_SET_ID,
        "rule_set_version": RULE_SET_VERSION,
        "default_scope": {
            "tenant_id": DEFAULT_TENANT_ID,
            "workspace_id": DEFAULT_WORKSPACE_ID,
            "scope_key": DEFAULT_SCOPE_KEY,
            "visibility": DEFAULT_VISIBILITY,
            "migration_principal_id": MIGRATION_PRINCIPAL_ID,
        },
        "state_rules": STATE_RULES,
    }
    rule_bundle["rule_set_hash"] = sha256_payload(rule_bundle)
    migration_batch_id = deterministic_id(
        "mig",
        classification["source_manifest"]["combined_source_hash"],
        classification["classification_hash"],
        rule_bundle["rule_set_hash"],
    )
    mappings: list[dict[str, object]] = []
    anomalies: list[dict[str, object]] = []
    for classification_row in sorted(
        classification_rows,
        key=lambda item: str(item["source_id"]),
    ):
        work_order_id = str(classification_row["source_id"])
        mapping, anomaly = plan_work_order(
            classification_row,
            source_rows[work_order_id],
            migration_batch_id=migration_batch_id,
        )
        mappings.append(mapping)
        if anomaly is not None:
            anomalies.append(anomaly)

    proposed_state_counts = Counter(
        str(mapping["proposed_fields"]["canonical_state"])
        if mapping["proposed_fields"]["canonical_state"] is not None
        else "unresolved_null"
        for mapping in mappings
    )
    anomaly_counts = Counter(
        str(anomaly["anomaly_type"]) for anomaly in anomalies
    )
    severity_counts = Counter(
        str(anomaly["severity"]) for anomaly in anomalies
    )
    generated_at = observed_at or datetime.now(timezone.utc).isoformat(
        timespec="microseconds"
    ).replace("+00:00", "Z")
    plan: dict[str, object] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "generated_at": generated_at,
        "mode": "quarantine_backfill_dry_run",
        "run_metadata": {
            "actor": LOCAL_FOUNDER_PRINCIPAL_ID,
            "migration_principal": MIGRATION_PRINCIPAL_ID,
            "tool_version": TOOL_VERSION,
        },
        "source_binding": {
            "operational_database_hash": classification["source_manifest"][
                "database"
            ]["components"][0]["sha256"],
            "combined_source_hash": classification["source_manifest"][
                "combined_source_hash"
            ],
            "classification_hash": classification["classification_hash"],
            "classification_rule_set_hash": classification["rule_set"][
                "rule_set_hash"
            ],
        },
        "migration_batch": {
            "migration_batch_id": migration_batch_id,
            "mode": "dry_run",
            "status": "proposed",
            "source_manifest_hash": classification["source_manifest"][
                "combined_source_hash"
            ],
            "ruleset_version": RULE_SET_VERSION,
            "created_by": MIGRATION_PRINCIPAL_ID,
            "persisted": False,
        },
        "rule_set": rule_bundle,
        "default_root_records": root_record_plan(),
        "work_order_mappings": mappings,
        "reconciliation_anomalies": anomalies,
        "summary": {
            "source_work_order_count": len(source_rows),
            "planned_work_order_mapping_count": len(mappings),
            "scope_backfill_count": len(mappings),
            "tenant_null_after_proposed_backfill": 0,
            "workspace_null_after_proposed_backfill": 0,
            "cross_tenant_candidate_count": 0,
            "legacy_completed_count": sum(
                1 for item in mappings if item["source_state"] == "completed"
            ),
            "legacy_completed_quarantine_count": sum(
                1
                for item in mappings
                if item["quarantine_reason"]
                == "legacy_completed_review_required"
            ),
            "direct_canonical_done_count": 0,
            "proposed_canonical_state_counts": dict(
                sorted(proposed_state_counts.items())
            ),
            "anomaly_count": len(anomalies),
            "anomaly_type_counts": dict(sorted(anomaly_counts.items())),
            "anomaly_severity_counts": dict(sorted(severity_counts.items())),
            "legacy_rows_unchanged_count": len(mappings),
            "source_rows_rewritten": 0,
            "canonical_rows_inserted": 0,
            "root_rows_inserted": 0,
            "migration_rows_inserted": 0,
        },
        "constraint_simulation": {
            "mapping_ids_unique": True,
            "source_keys_unique": True,
            "anomaly_ids_unique": True,
            "all_scope_candidates_match_default_tenant_workspace": True,
            "parallel_attempts_disabled_for_all_candidates": True,
            "legacy_status_preserved": True,
            "canonical_done_inference_disabled": True,
        },
        "compatibility_projection": {
            "legacy_status_write": "unchanged",
            "legacy_attempt_count_write": "unchanged",
            "filesystem_queue_write": "none",
            "user_facing_authority_switch": False,
        },
        "rollback_preview": {
            "current_dry_run": {
                "required": False,
                "reason": "reports_only_zero_source_writes",
            },
            "future_shadow_backfill_inverse_operations": [
                "clear canonical support columns only for rows bound to migration_batch_id",
                "delete proposed reconciliation anomaly rows for migration_batch_id",
                "delete proposed legacy mapping rows for migration_batch_id",
                "delete migration batch row after dependent rows are removed",
                "remove default root records only if created by the batch and unreferenced",
                "leave every legacy status, result, path, and filesystem queue fact unchanged",
            ],
            "executable_sql_included": False,
        },
        "cutover_blockers": [
            {
                "blocker": "unresolved_canonical_states",
                "count": proposed_state_counts.get("unresolved_null", 0),
            },
            {
                "blocker": "open_reconciliation_anomalies",
                "count": len(anomalies),
            },
            {
                "blocker": "migration_apply_not_authorized",
                "count": 1,
            },
            {
                "blocker": "epic_1_not_authorized",
                "count": 1,
            },
        ],
    }
    stable_payload = dict(plan)
    stable_payload.pop("generated_at")
    stable_payload.pop("run_metadata")
    plan["plan_hash"] = sha256_payload(stable_payload)
    _validate_plan(plan)
    return plan


def render_markdown(plan: Mapping[str, Any]) -> str:
    summary = plan["summary"]
    state_counts = summary["proposed_canonical_state_counts"]
    anomaly_types = summary["anomaly_type_counts"]
    lines = [
        "# v0.47 F0-C3 Quarantine Backfill Dry Run",
        "",
        f"- Generated at: `{plan['generated_at']}`",
        f"- Mode: `{plan['mode']}`",
        f"- Migration batch: `{plan['migration_batch']['migration_batch_id']}`",
        f"- Plan hash: `{plan['plan_hash']}`",
        f"- Bound F0-C2 classification: `{plan['source_binding']['classification_hash']}`",
        "- Source rows rewritten: `0`",
        "- Canonical rows inserted: `0`",
        "",
        "## Default Scope Proposal",
        "",
        f"- Tenant: `{DEFAULT_TENANT_ID}` / {DEFAULT_TENANT_NAME}",
        f"- Workspace: `{DEFAULT_WORKSPACE_ID}` / {DEFAULT_WORKSPACE_NAME}",
        f"- Founder principal: `{LOCAL_FOUNDER_PRINCIPAL_ID}`",
        f"- Migration principal: `{MIGRATION_PRINCIPAL_ID}`",
        f"- Visibility: `{DEFAULT_VISIBILITY}`",
        "",
        "## Count Conservation",
        "",
        f"- Source WorkOrders: `{summary['source_work_order_count']}`",
        f"- Planned mappings: `{summary['planned_work_order_mapping_count']}`",
        f"- Scope backfills proposed: `{summary['scope_backfill_count']}`",
        f"- Tenant-null after proposal: `{summary['tenant_null_after_proposed_backfill']}`",
        f"- Workspace-null after proposal: `{summary['workspace_null_after_proposed_backfill']}`",
        f"- Cross-Tenant candidates: `{summary['cross_tenant_candidate_count']}`",
        "",
        "## Quarantine Gate",
        "",
        f"- Legacy completed: `{summary['legacy_completed_count']}`",
        f"- `legacy_completed_review_required`: `{summary['legacy_completed_quarantine_count']}`",
        f"- Direct canonical done: `{summary['direct_canonical_done_count']}`",
        "",
        "## Proposed Canonical States",
        "",
        "| State | Count |",
        "|---|---:|",
    ]
    for state, count in sorted(state_counts.items()):
        lines.append(f"| `{state}` | {count} |")
    lines.extend(
        [
            "",
            "## Reconciliation Anomalies",
            "",
            f"- Total open anomalies: `{summary['anomaly_count']}`",
            "",
            "| Type | Count |",
            "|---|---:|",
        ]
    )
    for anomaly_type, count in sorted(anomaly_types.items()):
        lines.append(f"| `{anomaly_type}` | {count} |")
    lines.extend(
        [
            "",
            "## Safety Decisions",
            "",
            "- `routed`, `assigned`, and `in_progress` do not receive an inferred "
            "canonical state.",
            "- No Attempt, Approval, Review, Audit Event, Tenant, Workspace, or "
            "mapping row is created by this dry run.",
            "- Existing legacy status/result/path fields remain unchanged.",
            "- Rollback is a no-op for this report-only run; the JSON contains an "
            "abstract inverse plan for a separately authorized shadow backfill.",
            "- Migration apply, E1-A, and Epic 1 remain blocked.",
            "",
            "The JSON report contains every proposed WorkOrder field mapping and "
            "reconciliation anomaly.",
            "",
        ]
    )
    return "\n".join(lines)


def rollback_document(plan: Mapping[str, Any]) -> dict[str, object]:
    return {
        "schema_version": "v0.47-f0-c3-rollback-preview-v1",
        "generated_at": plan["generated_at"],
        "migration_batch_id": plan["migration_batch"]["migration_batch_id"],
        "plan_hash": plan["plan_hash"],
        "source_binding": plan["source_binding"],
        "rollback_preview": plan["rollback_preview"],
        "source_rows_rewritten": 0,
        "executable": False,
    }


def _assert_output_allowed(output_dir: Path) -> Path:
    output = output_dir.expanduser().resolve()
    protected = (
        (REPO_ROOT / "backend/data").resolve(),
        (REPO_ROOT / "private").resolve(),
    )
    if any(output == root or root in output.parents for root in protected):
        raise ProtectedOutputRefused("dry_run_output_must_not_target_protected_source")
    return output


def _atomic_write(path: Path, payload: bytes) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def write_reports(plan: Mapping[str, Any], output_dir: Path) -> list[Path]:
    output = _assert_output_allowed(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    targets = [
        output / "v0.47-F0-C3-backfill-dry-run.json",
        output / "v0.47-F0-C3-backfill-dry-run.md",
        output / "v0.47-F0-C3-rollback-preview.json",
    ]
    _atomic_write(
        targets[0],
        json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
        + b"\n",
    )
    _atomic_write(targets[1], render_markdown(plan).encode("utf-8"))
    _atomic_write(
        targets[2],
        json.dumps(
            rollback_document(plan),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ).encode("utf-8")
        + b"\n",
    )
    return targets


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--queue-root", type=Path, default=DEFAULT_QUEUE_ROOT)
    parser.add_argument(
        "--classification-report",
        type=Path,
        default=DEFAULT_CLASSIFICATION_REPORT,
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--observed-at")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    arguments = parse_args(argv)
    plan = build_plan(
        arguments.database,
        arguments.queue_root,
        arguments.classification_report,
        observed_at=arguments.observed_at,
    )
    targets = write_reports(plan, arguments.output_dir)
    print(
        json.dumps(
            {
                "status": "ok",
                "mode": plan["mode"],
                "migration_batch_id": plan["migration_batch"]["migration_batch_id"],
                "plan_hash": plan["plan_hash"],
                "work_orders": plan["summary"]["source_work_order_count"],
                "legacy_completed_quarantine_count": plan["summary"][
                    "legacy_completed_quarantine_count"
                ],
                "direct_canonical_done_count": plan["summary"][
                    "direct_canonical_done_count"
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
