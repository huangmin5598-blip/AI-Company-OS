"""Sole OS-governed command gateway for the non-authoritative pilot."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.foundation.canonical_json import payload_hash
from app.foundation.context import (
    AuthenticationMethod,
    PrincipalContext,
    PrincipalType,
    RequestContext,
    RequestOrigin,
    ScopeContext,
)
from app.foundation.local_founder import (
    DEFAULT_TENANT_ID,
    DEFAULT_WORKSPACE_ID,
    resolve_local_founder,
)
from app.models.foundation_execution import WorkApproval, WorkAttempt, WorkReview
from app.repositories.canonical_work_order_read import (
    CanonicalWorkOrderReadRepository,
)
from app.services.canonical_execution_orchestrator import (
    execute_approved_controlled_builtin,
)
from app.services.canonical_execution_service import (
    BUILTIN_RUNTIME_ID,
    decide_execution_approval,
    decide_execution_review,
    request_execution_approval,
)
from app.services.canonical_work_order_create_service import (
    create_canonical_draft,
)
from app.services.canonical_work_order_read_service import project_canonical
from app.services.foundation_bootstrap import PERMISSIONS
from app.pilot.database import PilotDatabase


PILOT_MODE = "os_governed_pilot"
PILOT_POLICY = {
    "loopback_only": True,
    "single_user": True,
    "risk_level": "low",
    "runtime": "controlled_builtin",
    "approval_review_same_actor_exception": True,
}


class PilotCommandGateway:
    """The only pilot entry point allowed to invoke canonical commands."""

    def __init__(self, database: PilotDatabase):
        self.database = database

    def founder_request(
        self,
        *,
        client_host: str,
        forwarded_for: str | None,
        idempotency_key: str,
    ) -> RequestContext:
        principal = resolve_local_founder(
            client_host=client_host,
            local_mode_enabled=True,
            permission_names=frozenset(PERMISSIONS),
            forwarded_for=forwarded_for,
        )
        return RequestContext(
            scope=ScopeContext(
                principal,
                DEFAULT_TENANT_ID,
                DEFAULT_WORKSPACE_ID,
            ),
            origin=RequestOrigin.UI,
            idempotency_key=idempotency_key,
            mode=PILOT_MODE,
        )

    def _wrapper_request(self, idempotency_key: str) -> RequestContext:
        principal = PrincipalContext(
            principal_id="runtime-wrapper:controlled-builtin",
            principal_type=PrincipalType.RUNTIME_WRAPPER,
            authentication_method=AuthenticationMethod.SERVICE_CREDENTIAL,
            tenant_id=DEFAULT_TENANT_ID,
            workspace_id=DEFAULT_WORKSPACE_ID,
            permission_names=frozenset(
                {"work_order.read", "work_order.execute"}
            ),
            local_mode=True,
        )
        return RequestContext(
            scope=ScopeContext(
                principal,
                DEFAULT_TENANT_ID,
                DEFAULT_WORKSPACE_ID,
            ),
            origin=RequestOrigin.INTERNAL_WORKER,
            idempotency_key=idempotency_key,
            mode=PILOT_MODE,
        )

    def create_draft(
        self,
        request: RequestContext,
        *,
        skill_id: str,
        task_type: str,
        input_context: str,
        expected_output: str,
    ) -> dict[str, Any]:
        with self.database.command_session() as session:
            receipt = create_canonical_draft(
                session,
                request,
                skill_id=skill_id,
                task_type=task_type,
                input_context=input_context,
                expected_output=expected_output,
            )
        return self.get_work_order(request, receipt.work_order_id)

    def request_approval(
        self,
        request: RequestContext,
        work_order_id: str,
    ) -> dict[str, Any]:
        with self.database.command_session() as session:
            work_order = CanonicalWorkOrderReadRepository(session).get_by_id(
                request.scope,
                work_order_id,
            )
            if work_order is None:
                raise LookupError("canonical_work_order_not_found")
            request_execution_approval(
                session,
                request,
                work_order_id=work_order_id,
                expected_row_version=int(work_order.row_version),
                risk_level="low",
            )
        return self.get_work_order(request, work_order_id)

    def approve(
        self,
        request: RequestContext,
        work_order_id: str,
    ) -> dict[str, Any]:
        with self.database.command_session() as session:
            work_order = CanonicalWorkOrderReadRepository(session).get_by_id(
                request.scope,
                work_order_id,
            )
            approval = session.execute(
                select(WorkApproval)
                .where(
                    WorkApproval.scope_key == request.scope.scope_key,
                    WorkApproval.target_id == work_order_id,
                    WorkApproval.decision == "requested",
                )
                .order_by(WorkApproval.created_at.desc())
            ).scalars().first()
            if work_order is None or approval is None:
                raise LookupError("approval_request_not_found")
            if (
                request.scope.principal_id != "local-founder"
                or approval.risk_level != "low"
            ):
                raise PermissionError(
                    "pilot_single_actor_approval_exception_not_applicable"
                )
            decide_execution_approval(
                session,
                request,
                work_order_id=work_order_id,
                approval_id=approval.approval_id,
                decision="approved",
                expected_work_order_version=int(work_order.row_version),
                expected_approval_version=int(approval.row_version),
            )
        return self.get_work_order(request, work_order_id)

    def execute(
        self,
        request: RequestContext,
        work_order_id: str,
        *,
        heading: str,
        body: str,
        scratch_parent: Path | None = None,
    ) -> dict[str, Any]:
        with self.database.command_session() as session:
            work_order = CanonicalWorkOrderReadRepository(session).get_by_id(
                request.scope,
                work_order_id,
            )
            if work_order is None:
                raise LookupError("canonical_work_order_not_found")
            if work_order.canonical_state != "queued":
                raise ValueError("pilot_execution_requires_queued")
            expected_version = int(work_order.row_version)

        base_key = str(request.idempotency_key)

        def request_factory(stage: str, wrapper: bool) -> RequestContext:
            if wrapper:
                return self._wrapper_request(f"{base_key}:{stage}")
            return RequestContext(
                scope=request.scope,
                origin=request.origin,
                correlation_id=request.correlation_id,
                causation_id=request.correlation_id,
                idempotency_key=f"{base_key}:{stage}",
                mode=PILOT_MODE,
            )

        receipt = execute_approved_controlled_builtin(
            self.database,
            work_order_id=work_order_id,
            expected_work_order_version=expected_version,
            request_factory=request_factory,
            payload={"heading": heading, "body": body},
            scratch_parent=scratch_parent,
        )
        result = self.get_work_order(request, work_order_id)
        result["execution"] = {
            "attempt_id": receipt.attempt_id,
            "review_id": receipt.review_id,
            "result_markdown": receipt.result_markdown,
            "result_ref": receipt.result_ref,
            "result_payload_hash": receipt.result_payload_hash,
            "scratch_root": receipt.scratch_root,
        }
        return result

    def review(
        self,
        request: RequestContext,
        work_order_id: str,
        *,
        decision: str = "passed",
    ) -> dict[str, Any]:
        with self.database.command_session() as session:
            work_order = CanonicalWorkOrderReadRepository(session).get_by_id(
                request.scope,
                work_order_id,
            )
            review = session.execute(
                select(WorkReview)
                .where(
                    WorkReview.scope_key == request.scope.scope_key,
                    WorkReview.work_order_id == work_order_id,
                    WorkReview.state == "requested",
                )
                .order_by(WorkReview.created_at.desc())
            ).scalars().first()
            approval = session.execute(
                select(WorkApproval)
                .where(
                    WorkApproval.scope_key == request.scope.scope_key,
                    WorkApproval.target_id == work_order_id,
                    WorkApproval.decision == "approved",
                )
                .order_by(WorkApproval.created_at.desc())
            ).scalars().first()
            attempt = (
                None
                if review is None
                else session.get(WorkAttempt, review.attempt_id)
            )
            if work_order is None or review is None:
                raise LookupError("review_request_not_found")
            if (
                request.scope.principal_id != "local-founder"
                or approval is None
                or approval.risk_level != "low"
                or approval.decided_by != request.scope.principal_id
                or attempt is None
                or attempt.runtime_adapter_id != BUILTIN_RUNTIME_ID
            ):
                raise PermissionError(
                    "pilot_single_actor_review_exception_not_applicable"
                )
            decide_execution_review(
                session,
                request,
                work_order_id=work_order_id,
                review_id=review.review_id,
                decision=decision,
                expected_work_order_version=int(work_order.row_version),
                expected_review_version=int(review.row_version),
                findings=[
                    {
                        "code": "local_pilot_founder_review",
                        "governance_exception": (
                            "single_actor_approval_review_local_pilot"
                        ),
                        "policy": PILOT_POLICY,
                    }
                ],
            )
        return self.get_work_order(request, work_order_id)

    def list_work_orders(
        self,
        request: RequestContext,
    ) -> list[dict[str, Any]]:
        with self.database.command_session() as session:
            repository = CanonicalWorkOrderReadRepository(session)
            return [
                project_canonical(
                    work_order,
                    source_hash=self._work_order_hash(work_order),
                )
                for work_order in repository.list(
                    request.scope,
                    limit=100,
                )
            ]

    def get_work_order(
        self,
        request: RequestContext,
        work_order_id: str,
    ) -> dict[str, Any]:
        with self.database.command_session() as session:
            work_order = CanonicalWorkOrderReadRepository(session).get_by_id(
                request.scope,
                work_order_id,
            )
            if work_order is None:
                raise LookupError("canonical_work_order_not_found")
            envelope = project_canonical(
                work_order,
                source_hash=self._work_order_hash(work_order),
            )
            approval = session.execute(
                select(WorkApproval)
                .where(
                    WorkApproval.scope_key == request.scope.scope_key,
                    WorkApproval.target_id == work_order_id,
                )
                .order_by(WorkApproval.created_at.desc())
            ).scalars().first()
            attempt = session.execute(
                select(WorkAttempt)
                .where(
                    WorkAttempt.scope_key == request.scope.scope_key,
                    WorkAttempt.work_order_id == work_order_id,
                )
                .order_by(WorkAttempt.created_at.desc())
            ).scalars().first()
            review = session.execute(
                select(WorkReview)
                .where(
                    WorkReview.scope_key == request.scope.scope_key,
                    WorkReview.work_order_id == work_order_id,
                )
                .order_by(WorkReview.created_at.desc())
            ).scalars().first()
            envelope["governance"] = {
                "mode": PILOT_MODE,
                "authority": "pilot_non_authoritative",
                "policy": PILOT_POLICY,
            }
            envelope["latest_approval"] = (
                None
                if approval is None
                else {
                    "approval_id": approval.approval_id,
                    "decision": approval.decision,
                    "row_version": approval.row_version,
                    "requested_by": approval.requested_by,
                    "decided_by": approval.decided_by,
                }
            )
            envelope["latest_attempt"] = (
                None
                if attempt is None
                else {
                    "attempt_id": attempt.attempt_id,
                    "state": attempt.state,
                    "row_version": attempt.row_version,
                    "result_ref": attempt.result_ref,
                    "result_payload_hash": attempt.result_payload_hash,
                }
            )
            envelope["latest_review"] = (
                None
                if review is None
                else {
                    "review_id": review.review_id,
                    "state": review.state,
                    "row_version": review.row_version,
                    "reviewer_id": review.reviewer_id,
                    "findings": json.loads(review.findings_json),
                }
            )
            return envelope

    @staticmethod
    def _work_order_hash(work_order) -> str:
        return payload_hash(
            {
                "work_order_id": work_order.work_order_id,
                "canonical_state": work_order.canonical_state,
                "row_version": work_order.row_version,
                "tenant_id": work_order.tenant_id,
                "workspace_id": work_order.workspace_id,
            }
        )


__all__ = ["PILOT_MODE", "PILOT_POLICY", "PilotCommandGateway"]
