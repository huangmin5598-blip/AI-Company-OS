"""Orchestrate the fixed builtin without weakening canonical command gates."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
import tempfile
from typing import Callable, Mapping

from app.foundation.context import RequestContext
from app.models.foundation_execution import WorkAttempt
from app.pilot.database import PilotDatabase
from app.services.canonical_execution_service import (
    allocate_execution_attempt,
    claim_execution_attempt,
    ingest_attempt_result,
    record_invocation_started,
)
from app.services.controlled_builtin_executor import (
    execute_controlled_builtin,
    preflight_controlled_builtin,
)


@dataclass(frozen=True)
class ControlledExecutionReceipt:
    work_order_id: str
    attempt_id: str
    review_id: str
    work_order_state: str
    work_order_row_version: int
    result_markdown: str
    result_ref: str
    result_payload_hash: str
    scratch_root: str


def execute_approved_controlled_builtin(
    database: PilotDatabase,
    *,
    work_order_id: str,
    expected_work_order_version: int,
    request_factory: Callable[[str, bool], RequestContext],
    payload: Mapping[str, object],
    scratch_parent: Path | None = None,
) -> ControlledExecutionReceipt:
    with database.command_session() as session:
        allocated = allocate_execution_attempt(
            session,
            request_factory("allocate", False),
            work_order_id=work_order_id,
            expected_work_order_version=expected_work_order_version,
        )

    with database.command_session() as session:
        claimed = claim_execution_attempt(
            session,
            request_factory("claim", True),
            work_order_id=work_order_id,
            attempt_id=str(allocated.attempt_id),
            expected_work_order_version=expected_work_order_version,
            expected_attempt_version=1,
            lease_owner="pilot:controlled-builtin",
            lease_duration=timedelta(minutes=5),
        )

    if not claimed.lease_token:
        raise RuntimeError("controlled_execution_lease_missing")

    if scratch_parent is None:
        allowed_root = Path(
            tempfile.mkdtemp(prefix="ai-company-os-vs001-")
        ).resolve()
    else:
        allowed_root = scratch_parent.resolve(strict=True)
    scratch_root = allowed_root / str(allocated.attempt_id)
    scratch_root.mkdir(mode=0o700)

    with database.command_session() as session:
        attempt = session.get(WorkAttempt, allocated.attempt_id)
        if attempt is None:
            raise RuntimeError("controlled_execution_attempt_missing")
        wrapper_request = request_factory("preflight", True)
        preflight = preflight_controlled_builtin(
            attempt,
            wrapper_request.scope,
            scratch_root=scratch_root,
            allowed_temp_root=allowed_root,
        )
        record_invocation_started(
            session,
            request_factory("start", True),
            work_order_id=work_order_id,
            attempt_id=str(allocated.attempt_id),
            lease_token=claimed.lease_token,
            lease_generation=1,
            expected_attempt_version=2,
            runtime_session_id=f"builtin:{allocated.attempt_id}",
            preflight_ref=preflight.evidence_ref,
            preflight_hash=preflight.decision_hash,
            preflight_evidence=preflight.payload(),
        )

    run = execute_controlled_builtin(preflight, payload)
    result_path = scratch_root / "output/result.md"
    result_markdown = result_path.read_text(encoding="utf-8")

    with database.command_session() as session:
        ingested = ingest_attempt_result(
            session,
            request_factory("result", True),
            work_order_id=work_order_id,
            attempt_id=str(allocated.attempt_id),
            lease_token=claimed.lease_token,
            lease_generation=1,
            expected_work_order_version=claimed.work_order_row_version,
            expected_attempt_version=3,
            result_idempotency_key=f"pilot-result:{allocated.attempt_id}",
            evidence=run.evidence,
        )

    if not ingested.review_id:
        raise RuntimeError("controlled_execution_review_missing")
    return ControlledExecutionReceipt(
        work_order_id=work_order_id,
        attempt_id=str(allocated.attempt_id),
        review_id=ingested.review_id,
        work_order_state=ingested.work_order_state,
        work_order_row_version=ingested.work_order_row_version,
        result_markdown=result_markdown,
        result_ref=run.evidence.result_ref,
        result_payload_hash=run.evidence.result_payload_hash,
        scratch_root=str(scratch_root),
    )


__all__ = [
    "ControlledExecutionReceipt",
    "execute_approved_controlled_builtin",
]
