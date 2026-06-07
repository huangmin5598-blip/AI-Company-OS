"""Scoped idempotency records for canonical commands."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from sqlalchemy.orm import Session

from app.foundation.canonical_json import payload_hash
from app.foundation.clock import utc_now
from app.foundation.context import RequestContext
from app.foundation.identity import new_id
from app.models.foundation_audit import IdempotencyRecord


class IdempotencyConflict(RuntimeError):
    pass


@dataclass(frozen=True)
class IdempotencyBeginResult:
    record: IdempotencyRecord
    created: bool
    replay: bool


def begin_idempotent_command(
    session: Session,
    request: RequestContext,
    *,
    command: str,
    target_type: str,
    target_id: str,
    request_payload: Any,
    expires_at: datetime | None = None,
) -> IdempotencyBeginResult:
    if not request.idempotency_key:
        raise ValueError("idempotency_key_required")
    digest = payload_hash(request_payload)
    scope = request.scope
    existing = session.query(IdempotencyRecord).filter_by(
        scope_key=scope.scope_key,
        actor_id=scope.principal_id,
        command=command,
        target_type=target_type,
        target_id=target_id,
        idempotency_key=request.idempotency_key,
    ).first()
    if existing is not None:
        if existing.request_payload_hash != digest:
            raise IdempotencyConflict("idempotency_payload_conflict")
        return IdempotencyBeginResult(
            record=existing,
            created=False,
            replay=existing.status == "succeeded",
        )

    record = IdempotencyRecord(
        idempotency_record_id=new_id("idem"),
        tenant_id=scope.tenant_id,
        workspace_id=scope.workspace_id,
        scope_key=scope.scope_key,
        actor_id=scope.principal_id,
        command=command,
        target_type=target_type,
        target_id=target_id,
        idempotency_key=request.idempotency_key,
        request_payload_hash=digest,
        status="in_progress",
        correlation_id=request.correlation_id,
        expires_at=expires_at,
    )
    session.add(record)
    session.flush()
    return IdempotencyBeginResult(record=record, created=True, replay=False)


def complete_idempotent_command(
    record: IdempotencyRecord,
    *,
    response_ref: str,
    response_payload: Any,
    completed_at: datetime | None = None,
) -> None:
    if record.status == "succeeded":
        if record.response_hash != payload_hash(response_payload):
            raise IdempotencyConflict("idempotency_response_conflict")
        return
    if record.status != "in_progress":
        raise IdempotencyConflict("idempotency_record_not_completable")
    record.status = "succeeded"
    record.response_ref = response_ref
    record.response_hash = payload_hash(response_payload)
    record.completed_at = completed_at or utc_now()
