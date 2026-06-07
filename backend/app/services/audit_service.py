"""Transactional append-only Audit Event and Audit Packet service."""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.orm import Session

from app.foundation.canonical_json import canonical_json_bytes, payload_hash
from app.foundation.clock import utc_now
from app.foundation.context import RequestContext
from app.foundation.identity import new_id
from app.models.foundation_audit import (
    AuditAggregateSequence,
    AuditEvent,
    AuditPacket,
    IdempotencyRecord,
)

MAX_FUTURE_CLOCK_SKEW = timedelta(minutes=5)
MIN_PLAUSIBLE_OCCURRED_AT = datetime(1970, 1, 1, tzinfo=timezone.utc)


def _validated_occurred_at(
    occurred_at: datetime | None,
    occurred_at_source: str | None,
    recorded_at: datetime,
) -> tuple[datetime, str, str | None]:
    if occurred_at is None:
        return recorded_at, "backend_fallback", None
    if occurred_at.tzinfo is None or occurred_at.utcoffset() is None:
        raise ValueError("occurred_at_timezone_required")
    if not occurred_at_source:
        raise ValueError("occurred_at_source_required")

    normalized = occurred_at.astimezone(timezone.utc)
    if normalized > recorded_at + MAX_FUTURE_CLOCK_SKEW:
        return normalized, occurred_at_source, "future_clock_skew"
    if normalized < MIN_PLAUSIBLE_OCCURRED_AT:
        return normalized, occurred_at_source, "implausibly_old"
    return normalized, occurred_at_source, None


def _next_aggregate_sequence(
    session: Session,
    request: RequestContext,
    *,
    aggregate_type: str,
    aggregate_id: str,
) -> int:
    scope = request.scope
    if session.bind is not None and session.bind.dialect.name == "sqlite":
        statement = sqlite_insert(AuditAggregateSequence).values(
            sequence_id=new_id("aseq"),
            tenant_id=scope.tenant_id,
            workspace_id=scope.workspace_id,
            scope_key=scope.scope_key,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            last_sequence=1,
        )
        statement = statement.on_conflict_do_update(
            index_elements=["scope_key", "aggregate_type", "aggregate_id"],
            set_={
                "last_sequence": AuditAggregateSequence.last_sequence + 1,
            },
        ).returning(AuditAggregateSequence.last_sequence)
        return int(session.execute(statement).scalar_one())

    sequence_row = session.execute(
        select(AuditAggregateSequence)
        .where(
            AuditAggregateSequence.scope_key == scope.scope_key,
            AuditAggregateSequence.aggregate_type == aggregate_type,
            AuditAggregateSequence.aggregate_id == aggregate_id,
        )
        .with_for_update()
    ).scalar_one_or_none()
    if sequence_row is None:
        sequence_row = AuditAggregateSequence(
            sequence_id=new_id("aseq"),
            tenant_id=scope.tenant_id,
            workspace_id=scope.workspace_id,
            scope_key=scope.scope_key,
            aggregate_type=aggregate_type,
            aggregate_id=aggregate_id,
            last_sequence=1,
        )
        session.add(sequence_row)
        session.flush()
        return 1
    sequence_row.last_sequence += 1
    session.flush()
    return int(sequence_row.last_sequence)


def append_audit_event(
    session: Session,
    request: RequestContext,
    *,
    aggregate_type: str,
    aggregate_id: str,
    event_type: str,
    source_type: str,
    summary: str,
    payload: Any,
    occurred_at=None,
    occurred_at_source: str | None = None,
    source_id: str | None = None,
    payload_ref: str | None = None,
    provenance: dict[str, Any] | None = None,
    work_order_id: str | None = None,
    attempt_id: str | None = None,
    approval_id: str | None = None,
    review_id: str | None = None,
) -> AuditEvent:
    recorded_at = utc_now()
    occurred_at, occurred_at_source, clock_anomaly = _validated_occurred_at(
        occurred_at,
        occurred_at_source,
        recorded_at,
    )
    event_provenance = dict(provenance or {})
    if clock_anomaly is not None:
        event_provenance["clock_anomaly"] = clock_anomaly

    sequence = _next_aggregate_sequence(
        session,
        request,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
    )
    scope = request.scope
    event = AuditEvent(
        audit_event_id=new_id("aud"),
        tenant_id=scope.tenant_id,
        workspace_id=scope.workspace_id,
        scope_key=scope.scope_key,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        aggregate_sequence=sequence,
        event_type=event_type,
        occurred_at=occurred_at,
        recorded_at=recorded_at,
        occurred_at_source=occurred_at_source,
        actor_type=scope.principal_type,
        actor_id=scope.principal_id,
        mode=request.mode,
        source_type=source_type,
        source_id=source_id,
        correlation_id=request.correlation_id,
        causation_id=request.causation_id,
        summary=summary,
        payload_ref=payload_ref,
        payload_hash=payload_hash(payload),
        provenance_json=canonical_json_bytes(event_provenance).decode("utf-8"),
        work_order_id=work_order_id,
        attempt_id=attempt_id,
        approval_id=approval_id,
        review_id=review_id,
    )
    session.add(event)
    session.flush()
    return event


def append_denied_action_event(
    session: Session,
    request: RequestContext,
    *,
    action_type: str,
    reason_code: str,
    target_type: str | None = None,
) -> AuditEvent:
    """Append a non-disclosing security event for a denied protected action."""
    payload = {
        "action_type": action_type,
        "reason_code": reason_code,
        "target_type": target_type,
    }
    return append_audit_event(
        session,
        request,
        aggregate_type="security_scope",
        aggregate_id=request.scope.scope_key,
        event_type="security.action_denied",
        source_type=request.origin.value,
        summary="Protected action denied",
        payload=payload,
        provenance={"target_identifier_recorded": False},
    )


def create_audit_packet(
    session: Session,
    request: RequestContext,
    *,
    event: AuditEvent,
    action_type: str,
    evidence_refs: Iterable[str],
    idempotency_record: IdempotencyRecord | None = None,
    work_order_id: str | None = None,
    attempt_id: str | None = None,
    invocation_authenticity_ref: str | None = None,
    result_ref: str | None = None,
    previous_event_ref: str | None = None,
    reviewer_ref: str | None = None,
    idempotency_required: bool = True,
) -> AuditPacket:
    if idempotency_required and idempotency_record is None:
        raise ValueError("idempotency_ref_required")
    produced_at = utc_now()
    evidence = list(evidence_refs)
    packet_payload = {
        "audit_event_id": event.audit_event_id,
        "actor_id": request.scope.principal_id,
        "actor_type": request.scope.principal_type,
        "mode": request.mode,
        "tenant_id": request.scope.tenant_id,
        "workspace_id": request.scope.workspace_id,
        "work_order_id": work_order_id,
        "attempt_id": attempt_id,
        "action_type": action_type,
        "invocation_authenticity_ref": invocation_authenticity_ref,
        "result_ref": result_ref,
        "evidence_refs": evidence,
        "produced_at": produced_at,
        "previous_event_ref": previous_event_ref,
        "reviewer_ref": reviewer_ref,
        "idempotency_ref": (
            idempotency_record.idempotency_record_id
            if idempotency_record is not None
            else None
        ),
    }
    packet = AuditPacket(
        audit_packet_id=new_id("ap"),
        audit_event_id=event.audit_event_id,
        actor_id=request.scope.principal_id,
        actor_type=request.scope.principal_type,
        mode=request.mode,
        tenant_id=request.scope.tenant_id,
        workspace_id=request.scope.workspace_id,
        work_order_id=work_order_id,
        attempt_id=attempt_id,
        action_type=action_type,
        invocation_authenticity_ref=invocation_authenticity_ref,
        result_ref=result_ref,
        evidence_refs_json=json.dumps(
            evidence,
            ensure_ascii=False,
            separators=(",", ":"),
        ),
        produced_at=produced_at,
        payload_hash=payload_hash(packet_payload),
        previous_event_ref=previous_event_ref,
        reviewer_ref=reviewer_ref,
        idempotency_ref=packet_payload["idempotency_ref"],
    )
    session.add(packet)
    session.flush()
    return packet
