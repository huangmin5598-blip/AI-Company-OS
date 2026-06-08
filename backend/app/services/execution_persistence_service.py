"""Persistence-only canonical Attempt, Approval, and Review primitives."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import json
import secrets
from typing import Iterable

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.foundation.canonical_json import canonical_json_bytes
from app.foundation.clock import utc_now
from app.foundation.context import RequestContext
from app.foundation.execution_evidence import AttemptResultEvidence
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


def _leased_attempt(
    session: Session,
    request: RequestContext,
    *,
    attempt_id: str,
    lease_token: str,
    lease_generation: int,
    expected_row_version: int,
    allowed_states: set[str],
    now: datetime | None = None,
) -> WorkAttempt:
    raw_token = _decode_lease_token(lease_token)
    token_hash = _lease_token_hash(raw_token)
    checked_at = (now or utc_now()).astimezone(timezone.utc)
    attempt = session.execute(
        select(WorkAttempt).where(
            WorkAttempt.attempt_id == attempt_id,
            WorkAttempt.scope_key == request.scope.scope_key,
        )
    ).scalar_one_or_none()
    if (
        attempt is None
        or attempt.state not in allowed_states
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
    if expiry < checked_at:
        raise LeaseRejected("lease_expired")
    return attempt


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
    heartbeat_at = (now or utc_now()).astimezone(timezone.utc)
    attempt = _leased_attempt(
        session,
        request,
        attempt_id=attempt_id,
        lease_token=lease_token,
        lease_generation=lease_generation,
        expected_row_version=expected_row_version,
        allowed_states=set(ACTIVE_ATTEMPT_STATES),
        now=heartbeat_at,
    )

    attempt.heartbeat_at = heartbeat_at
    attempt.lease_expires_at = heartbeat_at + extend_by
    attempt.row_version += 1
    session.flush()
    return attempt


def start_attempt(
    session: Session,
    request: RequestContext,
    *,
    attempt_id: str,
    lease_token: str,
    lease_generation: int,
    expected_row_version: int,
    runtime_session_id: str,
    invocation_authenticity: dict[str, object],
    now: datetime | None = None,
) -> WorkAttempt:
    request.scope.require("work_order.execute")
    attempt = _leased_attempt(
        session,
        request,
        attempt_id=attempt_id,
        lease_token=lease_token,
        lease_generation=lease_generation,
        expected_row_version=expected_row_version,
        allowed_states={"claimed"},
        now=now,
    )
    if not runtime_session_id:
        raise ValueError("runtime_session_id_required")
    attempt.state = "running"
    attempt.runtime_session_id = runtime_session_id
    attempt.invocation_authenticity_json = canonical_json_bytes(
        invocation_authenticity
    ).decode("utf-8")
    attempt.started_at = (now or utc_now()).astimezone(timezone.utc)
    attempt.row_version += 1
    session.flush()
    return attempt


def submit_attempt_result(
    session: Session,
    request: RequestContext,
    *,
    attempt_id: str,
    lease_token: str,
    lease_generation: int,
    expected_row_version: int,
    result_idempotency_key: str,
    evidence: AttemptResultEvidence,
    now: datetime | None = None,
) -> WorkAttempt:
    request.scope.require("work_order.execute")
    if not result_idempotency_key:
        raise ValueError("result_idempotency_key_required")
    attempt = _leased_attempt(
        session,
        request,
        attempt_id=attempt_id,
        lease_token=lease_token,
        lease_generation=lease_generation,
        expected_row_version=expected_row_version,
        allowed_states={"running"},
        now=now,
    )
    attempt.state = evidence.terminal_state
    attempt.finished_at = (now or utc_now()).astimezone(timezone.utc)
    attempt.result_ref = evidence.result_ref
    attempt.stdout_ref = evidence.stdout_ref
    attempt.stderr_ref = evidence.stderr_ref
    attempt.exit_code = evidence.exit_code
    attempt.error_code = evidence.error_code
    attempt.error_summary = evidence.error_summary
    attempt.cost_summary_json = evidence.cost_summary_json()
    attempt.result_idempotency_key = result_idempotency_key
    attempt.result_payload_hash = evidence.result_payload_hash
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


def decide_approval(
    session: Session,
    request: RequestContext,
    *,
    approval_id: str,
    decision: str,
    expected_row_version: int,
    decision_note: str | None = None,
    now: datetime | None = None,
) -> WorkApproval:
    request.scope.require("approval.decide")
    if decision not in {"approved", "rejected"}:
        raise ValueError("unsupported_approval_decision")
    approval = session.execute(
        select(WorkApproval).where(
            WorkApproval.approval_id == approval_id,
            WorkApproval.scope_key == request.scope.scope_key,
        )
    ).scalar_one_or_none()
    if (
        approval is None
        or approval.decision != "requested"
        or approval.row_version != expected_row_version
    ):
        raise AttemptConflict("approval_decision_conflict")
    approval.decision = decision
    approval.decided_by = request.scope.principal_id
    approval.decided_at = (now or utc_now()).astimezone(timezone.utc)
    approval.decision_note = decision_note
    approval.row_version += 1
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


def create_result_review_request(
    session: Session,
    request: RequestContext,
    *,
    work_order_id: str,
    attempt_id: str,
    review_type: str,
    artifact_ids: Iterable[str],
    criteria_snapshot: dict[str, object],
) -> WorkReview:
    request.scope.require("work_order.execute")
    attempt = session.execute(
        select(WorkAttempt).where(
            WorkAttempt.attempt_id == attempt_id,
            WorkAttempt.work_order_id == work_order_id,
            WorkAttempt.scope_key == request.scope.scope_key,
        )
    ).scalar_one_or_none()
    if attempt is None or attempt.state not in {
        "succeeded",
        "failed",
        "timed_out",
        "cancelled",
        "stale",
    }:
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
        row_version=1,
        created_by=request.scope.principal_id,
    )
    session.add(review)
    session.flush()
    return review


def decide_review(
    session: Session,
    request: RequestContext,
    *,
    review_id: str,
    decision: str,
    expected_row_version: int,
    findings: Iterable[dict[str, object]] = (),
    required_revisions: Iterable[dict[str, object]] = (),
    next_action: str | None = None,
    now: datetime | None = None,
) -> WorkReview:
    request.scope.require("review.decide")
    if request.scope.principal_type == "runtime_wrapper":
        raise PermissionError("runtime_wrapper_cannot_review")
    if decision not in {"passed", "revision_required", "failed", "cancelled"}:
        raise ValueError("unsupported_review_decision")
    review = session.execute(
        select(WorkReview).where(
            WorkReview.review_id == review_id,
            WorkReview.scope_key == request.scope.scope_key,
        )
    ).scalar_one_or_none()
    if (
        review is None
        or review.state not in {"requested", "in_review"}
        or review.row_version != expected_row_version
    ):
        raise AttemptConflict("review_decision_conflict")
    review.state = decision
    review.reviewer_type = request.scope.principal_type
    review.reviewer_id = request.scope.principal_id
    review.findings_json = json.dumps(
        list(findings),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    review.required_revisions_json = json.dumps(
        list(required_revisions),
        ensure_ascii=False,
        separators=(",", ":"),
    )
    review.next_action = next_action
    review.reviewed_at = (now or utc_now()).astimezone(timezone.utc)
    review.row_version += 1
    session.flush()
    return review
