"""Named canonical lifecycle commands for the VS-001 execution core."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta, timezone
import json
from typing import Any, Iterable, Mapping

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.foundation.context import RequestContext
from app.foundation.canonical_json import (
    canonical_json_bytes,
    payload_hash as canonical_payload_hash,
)
from app.foundation.clock import utc_now
from app.foundation.execution_evidence import (
    AttemptResultEvidence,
    RuntimeSelection,
)
from app.models.foundation_audit import AuditEvent, AuditPacket
from app.models.foundation_execution import WorkApproval, WorkAttempt, WorkReview
from app.repositories.canonical_work_order_command import (
    CanonicalCommandRejected,
    CanonicalWorkOrderCommandRepository,
)
from app.services.audit_service import append_audit_event, create_audit_packet
from app.services.execution_persistence_service import (
    AttemptClaim,
    claim_attempt,
    create_approval_request,
    create_attempt,
    create_result_review_request,
    decide_approval,
    decide_review,
    start_attempt,
    submit_attempt_result,
)
from app.services.idempotency_service import (
    IdempotencyBeginResult,
    begin_idempotent_command,
    complete_idempotent_command,
)


BUILTIN_RUNTIME_ID = "builtin.vs001_echo_markdown"
BUILTIN_RUNTIME_TYPE = "controlled_builtin"
BUILTIN_ADAPTER_MODULE = "app.services.controlled_builtin_executor"


@dataclass(frozen=True)
class CommandReceipt:
    command: str
    work_order_id: str
    work_order_state: str
    work_order_row_version: int
    audit_event_id: str
    audit_packet_id: str
    approval_id: str | None = None
    attempt_id: str | None = None
    review_id: str | None = None
    lease_token: str | None = None
    replayed: bool = False


def _work_order_repository(
    session: Session,
) -> CanonicalWorkOrderCommandRepository:
    return CanonicalWorkOrderCommandRepository(session)


def _begin(
    session: Session,
    request: RequestContext,
    *,
    command: str,
    work_order_id: str,
    payload: dict[str, object],
) -> IdempotencyBeginResult:
    return begin_idempotent_command(
        session,
        request,
        command=command,
        target_type="work_order",
        target_id=work_order_id,
        request_payload=payload,
    )


def _replay_receipt(
    session: Session,
    *,
    request: RequestContext,
    command: str,
    work_order_id: str,
    idempotency_ref: str,
    response_ref: str | None,
) -> CommandReceipt:
    packet = session.execute(
        select(AuditPacket).where(
            AuditPacket.idempotency_ref == idempotency_ref,
            AuditPacket.work_order_id == work_order_id,
        )
    ).scalar_one_or_none()
    if packet is None:
        raise CanonicalCommandRejected("idempotency_replay_evidence_missing")
    event = session.get(AuditEvent, packet.audit_event_id)
    if event is None:
        raise CanonicalCommandRejected("idempotency_replay_evidence_missing")
    try:
        original = json.loads(response_ref or "")
    except json.JSONDecodeError as exc:
        raise CanonicalCommandRejected(
            "idempotency_replay_response_missing"
        ) from exc
    return CommandReceipt(
        command=command,
        work_order_id=work_order_id,
        work_order_state=str(original["work_order_state"]),
        work_order_row_version=int(original["work_order_row_version"]),
        audit_event_id=event.audit_event_id,
        audit_packet_id=packet.audit_packet_id,
        approval_id=original.get("approval_id"),
        attempt_id=original.get("attempt_id"),
        review_id=original.get("review_id"),
        lease_token=None,
        replayed=True,
    )


def _finish(
    session: Session,
    request: RequestContext,
    *,
    command: str,
    work_order_id: str,
    work_order_state: str,
    work_order_row_version: int,
    idempotency: IdempotencyBeginResult,
    payload: dict[str, object],
    evidence_refs: Iterable[str] = (),
    approval_id: str | None = None,
    attempt_id: str | None = None,
    review_id: str | None = None,
    invocation_authenticity_ref: str | None = None,
    result_ref: str | None = None,
    reviewer_ref: str | None = None,
    lease_token: str | None = None,
) -> CommandReceipt:
    event = append_audit_event(
        session,
        request,
        aggregate_type="work_order",
        aggregate_id=work_order_id,
        event_type=command,
        source_type=request.origin.value,
        summary=command,
        payload=payload,
        provenance={"named_command": True},
        work_order_id=work_order_id,
        attempt_id=attempt_id,
        approval_id=approval_id,
        review_id=review_id,
    )
    packet = create_audit_packet(
        session,
        request,
        event=event,
        action_type=command,
        evidence_refs=evidence_refs,
        idempotency_record=idempotency.record,
        work_order_id=work_order_id,
        attempt_id=attempt_id,
        invocation_authenticity_ref=invocation_authenticity_ref,
        result_ref=result_ref,
        reviewer_ref=reviewer_ref,
    )
    response_payload = {
        "work_order_id": work_order_id,
        "work_order_state": work_order_state,
        "work_order_row_version": work_order_row_version,
        "approval_id": approval_id,
        "attempt_id": attempt_id,
        "review_id": review_id,
        "audit_packet_id": packet.audit_packet_id,
    }
    complete_idempotent_command(
        idempotency.record,
        response_ref=json.dumps(
            response_payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ),
        response_payload=response_payload,
    )
    return CommandReceipt(
        command=command,
        work_order_id=work_order_id,
        work_order_state=work_order_state,
        work_order_row_version=work_order_row_version,
        audit_event_id=event.audit_event_id,
        audit_packet_id=packet.audit_packet_id,
        approval_id=approval_id,
        attempt_id=attempt_id,
        review_id=review_id,
        lease_token=lease_token,
    )


def _begin_or_replay(
    session: Session,
    request: RequestContext,
    *,
    command: str,
    work_order_id: str,
    payload: dict[str, object],
) -> tuple[IdempotencyBeginResult, CommandReceipt | None]:
    result = _begin(
        session,
        request,
        command=command,
        work_order_id=work_order_id,
        payload=payload,
    )
    if result.replay:
        return result, _replay_receipt(
            session,
            request=request,
            command=command,
            work_order_id=work_order_id,
            idempotency_ref=result.record.idempotency_record_id,
            response_ref=result.record.response_ref,
        )
    return result, None


def _runtime_selection(session: Session) -> RuntimeSelection:
    row = session.execute(
        text(
            "SELECT runtime_id, runtime_type, display_name, adapter_module,"
            " config_json, enabled FROM runtime_registry"
            " WHERE runtime_id = :runtime_id"
        ),
        {"runtime_id": BUILTIN_RUNTIME_ID},
    ).mappings().one_or_none()
    if row is None:
        raise CanonicalCommandRejected("runtime_registry_entry_not_found")
    selection = RuntimeSelection.from_registry_row(dict(row))
    if (
        selection.runtime_type != BUILTIN_RUNTIME_TYPE
        or selection.adapter_module != BUILTIN_ADAPTER_MODULE
    ):
        raise CanonicalCommandRejected("runtime_registry_entry_mismatch")
    return selection


def _require_effective_execution_approval(
    session: Session,
    request: RequestContext,
    *,
    work_order_id: str,
    queued_row_version: int,
) -> WorkApproval:
    approval = session.execute(
        select(WorkApproval).where(
            WorkApproval.scope_key == request.scope.scope_key,
            WorkApproval.target_type == "work_order",
            WorkApproval.target_id == work_order_id,
            WorkApproval.target_version == str(queued_row_version - 1),
            WorkApproval.action == "execute",
            WorkApproval.decision == "approved",
        )
    ).scalar_one_or_none()
    if approval is None:
        raise CanonicalCommandRejected("effective_execution_approval_required")
    if approval.expires_at is not None:
        expiry = approval.expires_at
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        if expiry < utc_now():
            raise CanonicalCommandRejected("execution_approval_expired")
    return approval


def _require_attempt_runtime_snapshot(
    attempt: WorkAttempt,
    runtime: RuntimeSelection,
) -> None:
    expected_config = canonical_json_bytes(runtime.config_snapshot()).decode("utf-8")
    if (
        attempt.runtime_adapter_id != runtime.runtime_id
        or attempt.runtime_adapter_version != runtime.adapter_version
        or attempt.runtime_config_snapshot_json != expected_config
    ):
        raise CanonicalCommandRejected("attempt_runtime_snapshot_mismatch")


def request_execution_approval(
    session: Session,
    request: RequestContext,
    *,
    work_order_id: str,
    expected_row_version: int,
    risk_level: str,
) -> CommandReceipt:
    request.scope.require("approval.request")
    request.scope.require("work_order.execute")
    command = "work_order.request_execution_approval"
    payload = {
        "work_order_id": work_order_id,
        "expected_row_version": expected_row_version,
        "risk_level": risk_level,
    }
    with session.begin_nested():
        repository = _work_order_repository(session)
        work_order = repository.require_canonical(request.scope, work_order_id)
        idempotency, replay = _begin_or_replay(
            session,
            request,
            command=command,
            work_order_id=work_order_id,
            payload=payload,
        )
        if replay is not None:
            return replay
        if work_order.canonical_state != "draft":
            raise CanonicalCommandRejected("approval_requires_draft")
        updated = repository.request_approval(
            request.scope,
            work_order_id=work_order_id,
            expected_row_version=expected_row_version,
        )
        approval = create_approval_request(
            session,
            request,
            target_type="work_order",
            target_id=work_order_id,
            target_version=str(updated.row_version),
            action="execute",
            risk_level=risk_level,
        )
        return _finish(
            session,
            request,
            command=command,
            work_order_id=work_order_id,
            work_order_state="waiting_approval",
            work_order_row_version=int(updated.row_version),
            idempotency=idempotency,
            payload={**payload, "approval_id": approval.approval_id},
            approval_id=approval.approval_id,
        )


def decide_execution_approval(
    session: Session,
    request: RequestContext,
    *,
    work_order_id: str,
    approval_id: str,
    decision: str,
    expected_work_order_version: int,
    expected_approval_version: int,
) -> CommandReceipt:
    request.scope.require("approval.decide")
    command = f"work_order.approval_{decision}"
    payload = {
        "work_order_id": work_order_id,
        "approval_id": approval_id,
        "decision": decision,
        "expected_work_order_version": expected_work_order_version,
        "expected_approval_version": expected_approval_version,
    }
    with session.begin_nested():
        repository = _work_order_repository(session)
        work_order = repository.require_canonical(request.scope, work_order_id)
        approval = session.execute(
            select(WorkApproval).where(
                WorkApproval.approval_id == approval_id,
                WorkApproval.scope_key == request.scope.scope_key,
                WorkApproval.target_type == "work_order",
                WorkApproval.target_id == work_order_id,
                WorkApproval.target_version == str(expected_work_order_version),
                WorkApproval.action == "execute",
            )
        ).scalar_one_or_none()
        if approval is None:
            raise CanonicalCommandRejected("approval_target_mismatch")
        idempotency, replay = _begin_or_replay(
            session,
            request,
            command=command,
            work_order_id=work_order_id,
            payload=payload,
        )
        if replay is not None:
            return replay
        if work_order.canonical_state != "waiting_approval":
            raise CanonicalCommandRejected("approval_state_mismatch")
        decided = decide_approval(
            session,
            request,
            approval_id=approval_id,
            decision=decision,
            expected_row_version=expected_approval_version,
        )
        updated = repository.apply_approval_decision(
            request.scope,
            work_order_id=work_order_id,
            decision=decision,
            expected_row_version=expected_work_order_version,
        )
        target_state = str(updated.canonical_state)
        return _finish(
            session,
            request,
            command=command,
            work_order_id=work_order_id,
            work_order_state=target_state,
            work_order_row_version=int(updated.row_version),
            idempotency=idempotency,
            payload={**payload, "approval_decision": decided.decision},
            approval_id=approval_id,
        )


def allocate_execution_attempt(
    session: Session,
    request: RequestContext,
    *,
    work_order_id: str,
    expected_work_order_version: int,
) -> CommandReceipt:
    request.scope.require("work_order.execute")
    command = "work_order.allocate_attempt"
    payload = {
        "work_order_id": work_order_id,
        "expected_work_order_version": expected_work_order_version,
        "runtime_id": BUILTIN_RUNTIME_ID,
    }
    with session.begin_nested():
        work_order = _work_order_repository(session).require_canonical(
            request.scope,
            work_order_id,
        )
        idempotency, replay = _begin_or_replay(
            session,
            request,
            command=command,
            work_order_id=work_order_id,
            payload=payload,
        )
        if replay is not None:
            return replay
        if (
            work_order.canonical_state != "queued"
            or work_order.row_version != expected_work_order_version
        ):
            raise CanonicalCommandRejected("attempt_requires_queued_work_order")
        _require_effective_execution_approval(
            session,
            request,
            work_order_id=work_order_id,
            queued_row_version=int(work_order.row_version),
        )
        runtime = _runtime_selection(session)
        attempt = create_attempt(
            session,
            request,
            work_order_id=work_order_id,
            runtime_adapter_id=runtime.runtime_id,
            runtime_adapter_version=runtime.adapter_version,
            runtime_config_snapshot=runtime.config_snapshot(),
            allowed_read_refs=["scratch://input"],
            allowed_write_refs=["scratch://output"],
        )
        return _finish(
            session,
            request,
            command=command,
            work_order_id=work_order_id,
            work_order_state="queued",
            work_order_row_version=int(work_order.row_version),
            idempotency=idempotency,
            payload={**payload, "attempt_id": attempt.attempt_id},
            attempt_id=attempt.attempt_id,
        )


def claim_execution_attempt(
    session: Session,
    request: RequestContext,
    *,
    work_order_id: str,
    attempt_id: str,
    expected_work_order_version: int,
    expected_attempt_version: int,
    lease_owner: str,
    lease_duration: timedelta,
) -> CommandReceipt:
    request.scope.require("work_order.execute")
    command = "work_order.claim_attempt"
    payload = {
        "work_order_id": work_order_id,
        "attempt_id": attempt_id,
        "expected_work_order_version": expected_work_order_version,
        "expected_attempt_version": expected_attempt_version,
        "lease_owner": lease_owner,
        "lease_seconds": int(lease_duration.total_seconds()),
    }
    with session.begin_nested():
        repository = _work_order_repository(session)
        work_order = repository.require_canonical(request.scope, work_order_id)
        idempotency, replay = _begin_or_replay(
            session,
            request,
            command=command,
            work_order_id=work_order_id,
            payload=payload,
        )
        if replay is not None:
            return replay
        if work_order.canonical_state != "queued":
            raise CanonicalCommandRejected("claim_requires_queued_work_order")
        _require_effective_execution_approval(
            session,
            request,
            work_order_id=work_order_id,
            queued_row_version=int(work_order.row_version),
        )
        claim: AttemptClaim = claim_attempt(
            session,
            request,
            attempt_id=attempt_id,
            lease_owner=lease_owner,
            lease_duration=lease_duration,
            expected_row_version=expected_attempt_version,
        )
        if claim.attempt.work_order_id != work_order_id:
            raise CanonicalCommandRejected("attempt_work_order_mismatch")
        updated = repository.mark_running_after_claim(
            request.scope,
            work_order_id=work_order_id,
            expected_row_version=expected_work_order_version,
        )
        return _finish(
            session,
            request,
            command=command,
            work_order_id=work_order_id,
            work_order_state="running",
            work_order_row_version=int(updated.row_version),
            idempotency=idempotency,
            payload={**payload, "lease_generation": claim.attempt.lease_generation},
            attempt_id=attempt_id,
            lease_token=claim.lease_token,
        )


def record_invocation_started(
    session: Session,
    request: RequestContext,
    *,
    work_order_id: str,
    attempt_id: str,
    lease_token: str,
    lease_generation: int,
    expected_attempt_version: int,
    runtime_session_id: str,
    preflight_ref: str,
    preflight_hash: str,
    preflight_evidence: Mapping[str, object],
) -> CommandReceipt:
    request.scope.require("work_order.execute")
    preflight_payload = dict(preflight_evidence)
    calculated_preflight_hash = canonical_payload_hash(preflight_payload)
    if calculated_preflight_hash != preflight_hash:
        raise CanonicalCommandRejected("invocation_preflight_hash_mismatch")
    if preflight_ref != f"preflight://{attempt_id}/{preflight_hash}":
        raise CanonicalCommandRejected("invocation_preflight_lineage_mismatch")
    if (
        preflight_payload.get("attempt_id") != attempt_id
        or preflight_payload.get("work_order_id") != work_order_id
        or preflight_payload.get("tenant_id") != request.scope.tenant_id
        or preflight_payload.get("workspace_id") != request.scope.workspace_id
    ):
        raise CanonicalCommandRejected("invocation_preflight_target_mismatch")
    command = "work_order.start_invocation"
    payload = {
        "work_order_id": work_order_id,
        "attempt_id": attempt_id,
        "lease_generation": lease_generation,
        "expected_attempt_version": expected_attempt_version,
        "runtime_session_id": runtime_session_id,
        "preflight_ref": preflight_ref,
        "preflight_hash": preflight_hash,
    }
    with session.begin_nested():
        work_order = _work_order_repository(session).require_canonical(
            request.scope,
            work_order_id,
        )
        idempotency, replay = _begin_or_replay(
            session,
            request,
            command=command,
            work_order_id=work_order_id,
            payload=payload,
        )
        if replay is not None:
            return replay
        if work_order.canonical_state != "running":
            raise CanonicalCommandRejected("invocation_requires_running_work_order")
        runtime = _runtime_selection(session)
        attempt = start_attempt(
            session,
            request,
            attempt_id=attempt_id,
            lease_token=lease_token,
            lease_generation=lease_generation,
            expected_row_version=expected_attempt_version,
            runtime_session_id=runtime_session_id,
            invocation_authenticity=runtime.invocation_authenticity(
                wrapper="controlled_builtin_executor",
                preflight_ref=preflight_ref,
                preflight_hash=preflight_hash,
                preflight_evidence=preflight_payload,
            ),
        )
        if attempt.work_order_id != work_order_id:
            raise CanonicalCommandRejected("attempt_work_order_mismatch")
        _require_attempt_runtime_snapshot(attempt, runtime)
        return _finish(
            session,
            request,
            command=command,
            work_order_id=work_order_id,
            work_order_state="running",
            work_order_row_version=int(work_order.row_version),
            idempotency=idempotency,
            payload=payload,
            attempt_id=attempt_id,
            invocation_authenticity_ref=(
                f"attempt://{attempt_id}/invocation-authenticity"
            ),
        )


def ingest_attempt_result(
    session: Session,
    request: RequestContext,
    *,
    work_order_id: str,
    attempt_id: str,
    lease_token: str,
    lease_generation: int,
    expected_work_order_version: int,
    expected_attempt_version: int,
    result_idempotency_key: str,
    evidence: AttemptResultEvidence,
) -> CommandReceipt:
    request.scope.require("work_order.execute")
    command = "work_order.ingest_attempt_result"
    payload: dict[str, Any] = {
        "work_order_id": work_order_id,
        "attempt_id": attempt_id,
        "lease_generation": lease_generation,
        "expected_work_order_version": expected_work_order_version,
        "expected_attempt_version": expected_attempt_version,
        "result_idempotency_key": result_idempotency_key,
        "result_payload_hash": evidence.result_payload_hash,
        "terminal_state": evidence.terminal_state,
    }
    with session.begin_nested():
        repository = _work_order_repository(session)
        work_order = repository.require_canonical(request.scope, work_order_id)
        idempotency, replay = _begin_or_replay(
            session,
            request,
            command=command,
            work_order_id=work_order_id,
            payload=payload,
        )
        if replay is not None:
            return replay
        if work_order.canonical_state != "running":
            raise CanonicalCommandRejected("result_requires_running_work_order")
        attempt = submit_attempt_result(
            session,
            request,
            attempt_id=attempt_id,
            lease_token=lease_token,
            lease_generation=lease_generation,
            expected_row_version=expected_attempt_version,
            result_idempotency_key=result_idempotency_key,
            evidence=evidence,
        )
        if attempt.work_order_id != work_order_id:
            raise CanonicalCommandRejected("attempt_work_order_mismatch")
        updated = repository.mark_waiting_review_after_result(
            request.scope,
            work_order_id=work_order_id,
            expected_row_version=expected_work_order_version,
        )
        review = create_result_review_request(
            session,
            request,
            work_order_id=work_order_id,
            attempt_id=attempt_id,
            review_type="acceptance",
            artifact_ids=[evidence.result_ref],
            criteria_snapshot={
                "requires_result_hash": True,
                "requires_zero_exit_for_success": True,
            },
        )
        return _finish(
            session,
            request,
            command=command,
            work_order_id=work_order_id,
            work_order_state="waiting_review",
            work_order_row_version=int(updated.row_version),
            idempotency=idempotency,
            payload={**payload, "review_id": review.review_id},
            evidence_refs=[
                evidence.result_ref,
                evidence.stdout_ref,
                evidence.stderr_ref,
            ],
            attempt_id=attempt_id,
            review_id=review.review_id,
            invocation_authenticity_ref=(
                f"attempt://{attempt_id}/invocation-authenticity"
            ),
            result_ref=evidence.result_ref,
        )


def decide_execution_review(
    session: Session,
    request: RequestContext,
    *,
    work_order_id: str,
    review_id: str,
    decision: str,
    expected_work_order_version: int,
    expected_review_version: int,
    findings: Iterable[dict[str, object]] = (),
) -> CommandReceipt:
    request.scope.require("review.decide")
    command = f"work_order.review_{decision}"
    payload = {
        "work_order_id": work_order_id,
        "review_id": review_id,
        "decision": decision,
        "expected_work_order_version": expected_work_order_version,
        "expected_review_version": expected_review_version,
    }
    target_states = {
        "passed": "done",
        "revision_required": "revision_required",
        "failed": "failed",
        "cancelled": "cancelled",
    }
    if decision not in target_states:
        raise ValueError("unsupported_review_decision")
    with session.begin_nested():
        repository = _work_order_repository(session)
        work_order = repository.require_canonical(request.scope, work_order_id)
        review = session.execute(
            select(WorkReview).where(
                WorkReview.review_id == review_id,
                WorkReview.work_order_id == work_order_id,
                WorkReview.scope_key == request.scope.scope_key,
            )
        ).scalar_one_or_none()
        if review is None:
            raise CanonicalCommandRejected("review_target_mismatch")
        idempotency, replay = _begin_or_replay(
            session,
            request,
            command=command,
            work_order_id=work_order_id,
            payload=payload,
        )
        if replay is not None:
            return replay
        if work_order.canonical_state != "waiting_review":
            raise CanonicalCommandRejected("review_requires_waiting_review")
        attempt = session.get(WorkAttempt, review.attempt_id)
        if (
            attempt is None
            or attempt.work_order_id != work_order_id
            or attempt.scope_key != request.scope.scope_key
            or attempt.state
            not in {"succeeded", "failed", "timed_out", "cancelled", "stale"}
        ):
            raise CanonicalCommandRejected("review_requires_terminal_attempt")
        decided = decide_review(
            session,
            request,
            review_id=review_id,
            decision=decision,
            expected_row_version=expected_review_version,
            findings=findings,
        )
        updated = repository.apply_review_outcome(
            request.scope,
            work_order_id=work_order_id,
            decision=decision,
            expected_row_version=expected_work_order_version,
        )
        target_state = str(updated.canonical_state)
        return _finish(
            session,
            request,
            command=command,
            work_order_id=work_order_id,
            work_order_state=target_state,
            work_order_row_version=int(updated.row_version),
            idempotency=idempotency,
            payload={**payload, "review_state": decided.state},
            attempt_id=review.attempt_id,
            review_id=review_id,
            reviewer_ref=f"principal://{request.scope.principal_id}",
        )


__all__ = [
    "CommandReceipt",
    "allocate_execution_attempt",
    "claim_execution_attempt",
    "decide_execution_approval",
    "decide_execution_review",
    "ingest_attempt_result",
    "record_invocation_started",
    "request_execution_approval",
]
