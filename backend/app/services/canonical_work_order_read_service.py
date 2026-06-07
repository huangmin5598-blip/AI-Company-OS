"""Truthful canonical and legacy WorkOrder projection assembly."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Any

from app.foundation.work_order_state import CANONICAL_STATES
from app.models.canonical_work_order import CanonicalWorkOrder


CLASSIFICATIONS = frozenset(
    {
        "high_confidence",
        "provisional",
        "ambiguous",
        "conflicting",
        "noncanonical_history",
        "orphaned",
    }
)
EVIDENCE_TIERS = frozenset({"A", "B", "C", "D"})
MODE_B_AUTHORITY = frozenset({"legacy_only", "projection"})
RESOLUTION_STATUSES = frozenset({"resolved", "unresolved", "conflicting"})
SOURCE_SYSTEMS = frozenset(
    {
        "work_orders",
        "tasks",
        "task_pool",
        "execution_requests",
        "code_runtime_jobs",
        "private_work_queue",
    }
)
MODE_B_CLASSIFICATION = {
    "noncanonical_history": ("legacy_only", "unresolved"),
    "conflicting": ("legacy_only", "conflicting"),
    "provisional": ("legacy_only", "unresolved"),
    "ambiguous": ("legacy_only", "unresolved"),
    "orphaned": ("legacy_only", "unresolved"),
    "high_confidence": ("projection", "resolved"),
}
PROVENANCE_KEYS = frozenset(
    {
        "authority",
        "classification",
        "evidence_tier",
        "resolution_status",
        "reason_codes",
        "source_system",
        "source_key",
        "source_hash",
        "evidence_refs",
        "anomaly_refs",
    }
)


def _serialized_time(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _data(
    *,
    work_order_id: str,
    skill_id: str,
    task_type: str,
    input_context: str,
    expected_output: str,
    canonical_state: str | None,
    legacy_status: str | None,
    row_version: int | None,
    created_at: Any,
    terminal_at: Any,
    optional: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    result = {
        "work_order_id": work_order_id,
        "skill_id": skill_id,
        "task_type": task_type,
        "input_context": input_context,
        "expected_output": expected_output,
        "canonical_state": canonical_state,
        "legacy_status": legacy_status,
        "row_version": row_version,
        "created_at": _serialized_time(created_at),
        "terminal_at": _serialized_time(terminal_at),
    }
    if optional:
        result.update(optional)
    return result


def _provenance(
    *,
    authority: str,
    classification: str,
    evidence_tier: str,
    resolution_status: str,
    reason_codes: Sequence[str],
    source_system: str,
    source_key: str,
    source_hash: str,
    evidence_refs: Sequence[Mapping[str, str]],
    anomaly_refs: Sequence[str],
) -> dict[str, Any]:
    if classification not in CLASSIFICATIONS or evidence_tier not in EVIDENCE_TIERS:
        raise ValueError("invalid_provenance_evidence")
    if resolution_status not in RESOLUTION_STATUSES:
        raise ValueError("invalid_resolution_status")
    if source_system not in SOURCE_SYSTEMS or not source_key or not source_hash:
        raise ValueError("invalid_provenance_source")
    value = {
        "authority": authority,
        "classification": classification,
        "evidence_tier": evidence_tier,
        "resolution_status": resolution_status,
        "reason_codes": list(reason_codes),
        "source_system": source_system,
        "source_key": source_key,
        "source_hash": source_hash,
        "evidence_refs": [dict(reference) for reference in evidence_refs],
        "anomaly_refs": list(anomaly_refs),
    }
    if frozenset(value) != PROVENANCE_KEYS:
        raise AssertionError("invalid_provenance_shape")
    return value


def _envelope(
    *,
    data: Mapping[str, Any],
    provenance: Mapping[str, Any],
    tenant_id: str | None,
    workspace_id: str | None,
) -> dict[str, Any]:
    return {
        "data": dict(data),
        "provenance": dict(provenance),
        "tenant_id": tenant_id,
        "workspace_id": workspace_id,
    }


def project_canonical(
    work_order: CanonicalWorkOrder,
    *,
    source_hash: str,
    classification: str = "high_confidence",
    evidence_tier: str = "A",
    reason_codes: Sequence[str] = (),
    anomaly_refs: Sequence[str] = (),
) -> dict[str, Any]:
    if (
        work_order.tenant_id is None
        or work_order.workspace_id is None
        or work_order.canonical_state not in CANONICAL_STATES
        or work_order.row_version is None
        or work_order.row_version < 1
    ):
        raise ValueError("canonical_projection_requires_resolved_record")
    return _envelope(
        data=_data(
            work_order_id=work_order.work_order_id,
            skill_id=work_order.skill_id,
            task_type=work_order.task_type,
            input_context=work_order.input_context,
            expected_output=work_order.expected_output,
            canonical_state=work_order.canonical_state,
            legacy_status=work_order.status,
            row_version=work_order.row_version,
            created_at=work_order.created_at,
            terminal_at=work_order.terminal_at,
            optional={
                "result_summary": work_order.result_summary,
                "error": work_order.error,
                "attempt_count": work_order.attempt_count,
                "completed_at": _serialized_time(work_order.completed_at),
            },
        ),
        provenance=_provenance(
            authority="canonical",
            classification=classification,
            evidence_tier=evidence_tier,
            resolution_status="resolved",
            reason_codes=reason_codes,
            source_system="work_orders",
            source_key=work_order.work_order_id,
            source_hash=source_hash,
            evidence_refs=(),
            anomaly_refs=anomaly_refs,
        ),
        tenant_id=work_order.tenant_id,
        workspace_id=work_order.workspace_id,
    )


def project_legacy(
    legacy_snapshot: Mapping[str, Any],
    rt3_evidence: Mapping[str, Any],
    rt4_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    required_rt3 = {
        "classification",
        "evidence_tier",
        "reason_codes",
        "recommended_disposition",
        "source_system",
        "source_id",
        "authority",
        "resolution_status",
    }
    required_rt4 = {
        "source_hash",
        "source_key",
        "anomaly_refs",
        "mapping_rule",
        "migration_batch_id",
    }
    if not required_rt3.issubset(rt3_evidence) or not required_rt4.issubset(
        rt4_evidence
    ):
        raise ValueError("invalid_mode_b_rt3_evidence")
    classification = str(rt3_evidence["classification"])
    expected = MODE_B_CLASSIFICATION.get(classification)
    actual = (
        rt3_evidence["authority"],
        rt3_evidence["resolution_status"],
    )
    if (
        expected is None
        or actual != expected
        or actual[0] not in MODE_B_AUTHORITY
        or actual[1] not in RESOLUTION_STATUSES
    ):
        raise ValueError("invalid_mode_b_rt3_evidence")
    work_order_id = str(legacy_snapshot.get("work_order_id", ""))
    if (
        not work_order_id
        or rt3_evidence["source_system"] != "work_orders"
        or rt3_evidence["source_id"] != work_order_id
        or rt4_evidence["source_key"] != work_order_id
    ):
        raise ValueError("legacy_projection_source_mismatch")
    return _envelope(
        data=_data(
            work_order_id=work_order_id,
            skill_id=str(legacy_snapshot.get("skill_id", "")),
            task_type=str(legacy_snapshot.get("task_type", "")),
            input_context=str(legacy_snapshot.get("input_context", "")),
            expected_output=str(legacy_snapshot.get("expected_output", "")),
            canonical_state=None,
            legacy_status=legacy_snapshot.get("status"),
            row_version=None,
            created_at=legacy_snapshot.get("created_at"),
            terminal_at=legacy_snapshot.get("completed_at"),
            optional={
                "result_summary": legacy_snapshot.get("result_summary", ""),
                "error": legacy_snapshot.get("error", ""),
                "attempt_count": legacy_snapshot.get("attempt_count", 0),
                "completed_at": _serialized_time(
                    legacy_snapshot.get("completed_at")
                ),
            },
        ),
        provenance=_provenance(
            authority=str(rt3_evidence["authority"]),
            classification=classification,
            evidence_tier=str(rt3_evidence["evidence_tier"]),
            resolution_status=str(rt3_evidence["resolution_status"]),
            reason_codes=rt3_evidence["reason_codes"],
            source_system="work_orders",
            source_key=work_order_id,
            source_hash=str(rt4_evidence["source_hash"]),
            evidence_refs=rt4_evidence.get("evidence_refs", ()),
            anomaly_refs=rt4_evidence["anomaly_refs"],
        ),
        tenant_id=None,
        workspace_id=None,
    )


__all__ = ["project_canonical", "project_legacy"]
