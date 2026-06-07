"""Persistence-only canonical Attempt, Approval, and Review primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import secrets
from typing import Iterable

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.foundation.canonical_json import canonical_json_bytes
from app.foundation.clock import utc_now
from app.foundation.context import RequestContext
from app.foundation.identity import new_id
from app.models.foundation_execution import (
    ACTIVE_ATTEMPT_STATES,
    WorkApproval,
    WorkAttempt,
    WorkReview,
)


class AttemptConflict(RuntimeError):
    pass


class LeaseRejected(RuntimeError):
    pass


@dataclass(frozen=True)
class AttemptClaim:
    attempt: WorkAttempt
    lease_token: str


def _lease_token_hash(raw_token: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw_token).hexdigest()


def _decode_lease_token(token: str) -> bytes:
    try:
        raw = bytes.fromhex(token)
    except ValueError as exc:
        raise LeaseRejected("invalid_lease_token") from exc
    if len(raw) != 32:
        raise LeaseRejected("invalid_lease_token")
    return raw


def create_attempt(
    session: Session,
    request: RequestContext,
    *,
    work_order_id: str,
    runtime_adapter_id: str,
    runtime_adapter_version: str,
    runtime_config_snapshot: dict[str, object],
    trigger_reason: str = "initial",
    parent_attempt_id: str | None = None,
    handoff_packet_ref: str | None = None,
    context_pack_snapshot_ref: str | None = None,
    policy_snapshot_ref: str | None = None,
    allowed_read_refs: Iterable[str] = (),
    allowed_write_refs: Iterable[str] = (),
) -> WorkAttempt:
    request.scope.require("work_order.execute")
    if request.scope.workspace_id is None:
        raise AttemptConflict("workspace_scope_required")

    active_count = session.execute(
        select(func.count())
        .select_from(WorkAttempt)
        .where(
            WorkAttempt.scope_key == request.scope.scope_key,
            WorkAttempt.work_order_id == work_order_id,
            WorkAttempt.state.in_(ACTIVE_ATTEMPT_STATES),
        )
    ).scalar_one()
    if active_count:
        raise AttemptConflict("active_attempt_exists")

    maximum = session.execute(
        select(func.max(WorkAttempt.attempt_number)).where(
            WorkAttempt.scope_key == request.scope.scope_key,
            WorkAttempt.work_order_id == work_order_id,
        )
    ).scalar_one()
    attempt = WorkAttempt(
        attempt_id=new_id("att"),
        tenant_id=request.scope.tenant_id,
        workspace_id=request.scope.workspace_id,
        scope_key=request.scope.scope_key,
        work_order_id=work_order_id,
        attempt_number=int(maximum or 0) + 1,
        parent_attempt_id=parent_attempt_id,
        trigger_reason=trigger_reason,
        state="created",
        row_version=1,
        runtime_adapter_id=runtime_adapter_id,
        runtime_adapter_version=runtime_adapter_version,
        runtime_config_snapshot_json=canonical_json_bytes(
            runtime_config_snapshot
        ).decode("utf-8"),
        lease_generation=0,
        invocation_authenticity_json="{}",
        handoff_packet_ref=handoff_packet_ref,
        context_pack_snapshot_ref=context_pack_snapshot_ref,
        policy_snapshot_ref=policy_snapshot_ref,
        allowed_read_refs_json=canonical_json_bytes(
            list(allowed_read_refs)
        ).decode("utf-8"),
        allowed_write_refs_json=canonical_json_bytes(
            list(allowed_write_refs)
        ).decode("utf-8"),
        created_by=request.scope.principal_id,
    )
    session.add(attempt)
    try:
        session.flush()
    except IntegrityError as exc:
        raise AttemptConflict("attempt_allocation_conflict") from exc
    return attempt


def claim_attempt(
    session: Session,
    request: RequestContext,
    *,
    attempt_id: str,
    lease_owner: str,
    lease_duration: timedelta,
    expected_row_version: int,
    now: datetime | None = None,
) -> AttemptClaim:
    request.scope.require("work_order.execute")
    if lease_duration <= timedelta(0):
        raise ValueError("lease_duration_must_be_positive")
    claimed_at = (now or utc_now()).astimezone(timezone.utc)
    raw_token = secrets.token_bytes(32)
    token_hash = _lease_token_hash(raw_token)
    statement = (
        update(WorkAttempt)
        .where(
            WorkAttempt.attempt_id == attempt_id,
            WorkAttempt.scope_key == request.scope.scope_key,
            WorkAttempt.state == "created",
            WorkAttempt.row_version == expected_row_version,
        )
        .values(
            state="claimed",
            row_version=WorkAttempt.row_version + 1,
            lease_owner=lease_owner,
            lease_token_hash=token_hash,
            lease_generation=WorkAttempt.lease_generation + 1,
            claimed_at=claimed_at,
            heartbeat_at=claimed_at,
            lease_expires_at=claimed_at + lease_duration,
        )
    )
    try:
        rowcount = session.execute(statement).rowcount
    except IntegrityError as exc:
        raise AttemptConflict("active_attempt_exists") from exc
    if rowcount != 1:
        raise AttemptConflict("attempt_claim_conflict")
    session.flush()
    attempt = session.get(WorkAttempt, attempt_id)
    if attempt is None:
        raise AttemptConflict("attempt_claim_conflict")
    return AttemptClaim(attempt=attempt, lease_token=raw_token.hex())


def heartbeat_attempt(
    session: Session,
    request: RequestContext,
    *,
    attempt_id: str,
    lease_token: str,
    lease_generation: int,
    extend_by: timedelta,
    expected_row_version: int,
    now: datetime | None = None,
) -> WorkAttempt:
    request.scope.require("work_order.execute")
    if extend_by <= timedelta(0):
        raise ValueError("lease_duration_must_be_positive")
    raw_token = _decode_lease_token(lease_token)
    token_hash = _lease_token_hash(raw_token)
    heartbeat_at = (now or utc_now()).astimezone(timezone.utc)
    attempt = session.execute(
        select(WorkAttempt).where(
            WorkAttempt.attempt_id == attempt_id,
            WorkAttempt.scope_key == request.scope.scope_key,
        )
    ).scalar_one_or_none()
    if (
        attempt is None
        or attempt.state not in ACTIVE_ATTEMPT_STATES
        or attempt.lease_generation != lease_generation
        or attempt.row_version != expected_row_version
        or attempt.lease_token_hash is None
        or not hmac.compare_digest(attempt.lease_token_hash, token_hash)
        or attempt.lease_expires_at is None
    ):
        raise LeaseRejected("lease_validation_failed")
    expiry = attempt.lease_expires_at
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)
    if expiry < heartbeat_at:
        raise LeaseRejected("lease_expired")

    attempt.heartbeat_at = heartbeat_at
    attempt.lease_expires_at = heartbeat_at + extend_by
    attempt.row_version += 1
    session.flush()
    return attempt


def create_approval_request(
    session: Session,
    request: RequestContext,
    *,
    target_type: str,
    target_id: str,
    target_version: str,
    action: str,
    risk_level: str,
    conditions: Iterable[str] = (),
    context_snapshot_ref: str | None = None,
    expires_at: datetime | None = None,
    supersedes_approval_id: str | None = None,
) -> WorkApproval:
    request.scope.require("approval.request")
    approval = WorkApproval(
        approval_id=new_id("apr"),
        tenant_id=request.scope.tenant_id,
        workspace_id=request.scope.workspace_id,
        scope_key=request.scope.scope_key,
        target_type=target_type,
        target_id=target_id,
        target_version=target_version,
        action=action,
        risk_level=risk_level,
        requested_by=request.scope.principal_id,
        requested_at=utc_now(),
        decision="requested",
        expires_at=expires_at,
        conditions_json=canonical_json_bytes(list(conditions)).decode("utf-8"),
        context_snapshot_ref=context_snapshot_ref,
        supersedes_approval_id=supersedes_approval_id,
        row_version=1,
    )
    session.add(approval)
    session.flush()
    return approval


def create_review_request(
    session: Session,
    request: RequestContext,
    *,
    work_order_id: str,
    attempt_id: str,
    review_type: str,
    artifact_ids: Iterable[str],
    criteria_snapshot: dict[str, object],
    supersedes_review_id: str | None = None,
) -> WorkReview:
    request.scope.require("review.request")
    attempt = session.execute(
        select(WorkAttempt).where(
            WorkAttempt.attempt_id == attempt_id,
            WorkAttempt.work_order_id == work_order_id,
            WorkAttempt.scope_key == request.scope.scope_key,
        )
    ).scalar_one_or_none()
    if attempt is None:
        raise ValueError("review_attempt_scope_mismatch")
    if attempt.state not in {"succeeded", "failed", "timed_out", "cancelled", "stale"}:
        raise ValueError("review_requires_terminal_attempt")
    review = WorkReview(
        review_id=new_id("rev"),
        tenant_id=request.scope.tenant_id,
        workspace_id=request.scope.workspace_id,
        scope_key=request.scope.scope_key,
        work_order_id=work_order_id,
        attempt_id=attempt_id,
        state="requested",
        review_type=review_type,
        artifact_ids_json=canonical_json_bytes(list(artifact_ids)).decode("utf-8"),
        criteria_snapshot_json=canonical_json_bytes(
            criteria_snapshot
        ).decode("utf-8"),
        findings_json="[]",
        required_revisions_json="[]",
        supersedes_review_id=supersedes_review_id,
        row_version=1,
        created_by=request.scope.principal_id,
    )
    session.add(review)
    session.flush()
    return review
