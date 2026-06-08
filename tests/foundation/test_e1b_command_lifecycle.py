from __future__ import annotations

from datetime import timedelta
import json
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from path_bootstrap import ensure_backend_path

ensure_backend_path()

from app.foundation.context import (
    AuthenticationMethod,
    PrincipalContext,
    PrincipalType,
    RequestContext,
    RequestOrigin,
    ScopeContext,
)
from app.foundation.execution_evidence import AttemptResultEvidence
from app.models.foundation_audit import AuditEvent, AuditPacket, IdempotencyRecord
from app.models.foundation_execution import WorkApproval, WorkAttempt, WorkReview
from app.repositories.canonical_work_order_command import (
    CanonicalWorkOrderCommandRepository,
)
from app.services.canonical_execution_service import (
    allocate_execution_attempt,
    claim_execution_attempt,
    decide_execution_approval,
    decide_execution_review,
    ingest_attempt_result,
    record_invocation_started,
    request_execution_approval,
)
from support import (
    controlled_builtin_script_hash,
    fixture_preflight_lineage,
    phase2a_authority_database,
)


def _request(
    *,
    key: str,
    principal_id: str,
    principal_type: PrincipalType,
    permissions: set[str],
) -> RequestContext:
    principal = PrincipalContext(
        principal_id=principal_id,
        principal_type=principal_type,
        authentication_method=AuthenticationMethod.SERVICE_CREDENTIAL,
        tenant_id="ten_local",
        workspace_id="wsp_personal",
        permission_names=frozenset(permissions),
    )
    return RequestContext(
        scope=ScopeContext(principal, "ten_local", "wsp_personal"),
        origin=RequestOrigin.INTERNAL_WORKER,
        idempotency_key=key,
    )


OPERATOR_PERMISSIONS = {
    "work_order.read",
    "work_order.execute",
    "approval.request",
}
REVIEWER_PERMISSIONS = {
    "work_order.read",
    "approval.decide",
    "review.decide",
}
WRAPPER_PERMISSIONS = {"work_order.read", "work_order.execute"}


class E1BCommandLifecycleTests(unittest.TestCase):
    def test_truthful_attempt_bound_lifecycle_requires_review_for_done(self) -> None:
        with phase2a_authority_database() as (database, work_order_id):
            engine = create_engine(f"sqlite:///{database}")
            session = Session(engine)
            try:
                approval_request = request_execution_approval(
                    session,
                    _request(
                        key="approval-request",
                        principal_id="operator",
                        principal_type=PrincipalType.HUMAN,
                        permissions=OPERATOR_PERMISSIONS,
                    ),
                    work_order_id=work_order_id,
                    expected_row_version=1,
                    risk_level="low",
                )
                session.commit()
                self.assertEqual("waiting_approval", approval_request.work_order_state)

                approved = decide_execution_approval(
                    session,
                    _request(
                        key="approval-decision",
                        principal_id="reviewer",
                        principal_type=PrincipalType.HUMAN,
                        permissions=REVIEWER_PERMISSIONS,
                    ),
                    work_order_id=work_order_id,
                    approval_id=approval_request.approval_id,
                    decision="approved",
                    expected_work_order_version=2,
                    expected_approval_version=1,
                )
                session.commit()
                self.assertEqual("queued", approved.work_order_state)

                allocated = allocate_execution_attempt(
                    session,
                    _request(
                        key="attempt-allocate",
                        principal_id="operator",
                        principal_type=PrincipalType.HUMAN,
                        permissions=OPERATOR_PERMISSIONS,
                    ),
                    work_order_id=work_order_id,
                    expected_work_order_version=3,
                )
                session.commit()

                claimed = claim_execution_attempt(
                    session,
                    _request(
                        key="attempt-claim",
                        principal_id="wrapper",
                        principal_type=PrincipalType.RUNTIME_WRAPPER,
                        permissions=WRAPPER_PERMISSIONS,
                    ),
                    work_order_id=work_order_id,
                    attempt_id=allocated.attempt_id,
                    expected_work_order_version=3,
                    expected_attempt_version=1,
                    lease_owner="wrapper:controlled-builtin",
                    lease_duration=timedelta(minutes=5),
                )
                session.commit()
                self.assertEqual("running", claimed.work_order_state)
                self.assertIsNotNone(claimed.lease_token)

                preflight_payload, preflight_hash, preflight_ref = (
                    fixture_preflight_lineage(
                        allocated.attempt_id,
                        work_order_id,
                    )
                )
                started = record_invocation_started(
                    session,
                    _request(
                        key="attempt-start",
                        principal_id="wrapper",
                        principal_type=PrincipalType.RUNTIME_WRAPPER,
                        permissions=WRAPPER_PERMISSIONS,
                    ),
                    work_order_id=work_order_id,
                    attempt_id=allocated.attempt_id,
                    lease_token=claimed.lease_token,
                    lease_generation=1,
                    expected_attempt_version=2,
                    runtime_session_id="run_vs001_test",
                    preflight_ref=preflight_ref,
                    preflight_hash=preflight_hash,
                    preflight_evidence=preflight_payload,
                )
                session.commit()
                self.assertEqual("running", started.work_order_state)
                attempt = session.get(WorkAttempt, allocated.attempt_id)
                self.assertEqual(
                    "builtin.vs001_echo_markdown",
                    attempt.runtime_adapter_id,
                )
                self.assertEqual(
                    controlled_builtin_script_hash(),
                    attempt.runtime_adapter_version,
                )
                authenticity = json.loads(attempt.invocation_authenticity_json)
                self.assertTrue(authenticity["registry_selected"])
                self.assertEqual(
                    "disposable_test_fixture",
                    authenticity["registry_source"],
                )
                self.assertFalse(authenticity["production_registered"])
                self.assertEqual(
                    preflight_hash,
                    authenticity["preflight_hash"],
                )
                self.assertEqual(
                    preflight_payload,
                    authenticity["preflight_evidence"],
                )

                result = ingest_attempt_result(
                    session,
                    _request(
                        key="attempt-result",
                        principal_id="wrapper",
                        principal_type=PrincipalType.RUNTIME_WRAPPER,
                        permissions=WRAPPER_PERMISSIONS,
                    ),
                    work_order_id=work_order_id,
                    attempt_id=allocated.attempt_id,
                    lease_token=claimed.lease_token,
                    lease_generation=1,
                    expected_work_order_version=4,
                    expected_attempt_version=3,
                    result_idempotency_key="result-1",
                    evidence=AttemptResultEvidence(
                        terminal_state="succeeded",
                        result_ref="scratch://output/result.md",
                        stdout_ref="scratch://output/stdout.txt",
                        stderr_ref="scratch://output/stderr.txt",
                        exit_code=0,
                        result_payload_hash="sha256:" + ("b" * 64),
                        cost_summary={"currency": "USD", "amount": 0},
                    ),
                )
                session.commit()
                self.assertEqual("waiting_review", result.work_order_state)
                self.assertEqual(
                    "succeeded",
                    session.get(WorkAttempt, allocated.attempt_id).state,
                )
                self.assertEqual(
                    "requested",
                    session.get(WorkReview, result.review_id).state,
                )

                self.assertFalse(
                    hasattr(
                        CanonicalWorkOrderCommandRepository(session),
                        "compare_and_set_state",
                    )
                )
                with self.assertRaisesRegex(
                    PermissionError,
                    "runtime_wrapper_cannot_review",
                ):
                    decide_execution_review(
                        session,
                        _request(
                            key="force-done",
                            principal_id="wrapper",
                            principal_type=PrincipalType.RUNTIME_WRAPPER,
                            permissions={
                                "work_order.read",
                                "review.decide",
                            },
                        ),
                        work_order_id=work_order_id,
                        review_id=result.review_id,
                        decision="passed",
                        expected_work_order_version=5,
                        expected_review_version=1,
                    )
                session.rollback()

                reviewed = decide_execution_review(
                    session,
                    _request(
                        key="review-pass",
                        principal_id="reviewer",
                        principal_type=PrincipalType.HUMAN,
                        permissions=REVIEWER_PERMISSIONS,
                    ),
                    work_order_id=work_order_id,
                    review_id=result.review_id,
                    decision="passed",
                    expected_work_order_version=5,
                    expected_review_version=1,
                    findings=[{"code": "accepted"}],
                )
                session.commit()
                self.assertEqual("done", reviewed.work_order_state)
                self.assertEqual(7, session.query(AuditEvent).count())
                self.assertEqual(7, session.query(AuditPacket).count())
                self.assertEqual(7, session.query(IdempotencyRecord).count())
                self.assertEqual(
                    "approved",
                    session.get(WorkApproval, approval_request.approval_id).decision,
                )
            finally:
                session.close()
                engine.dispose()

    def test_idempotent_replay_returns_original_receipt_without_duplicate_rows(self) -> None:
        with phase2a_authority_database() as (database, work_order_id):
            engine = create_engine(f"sqlite:///{database}")
            session = Session(engine)
            try:
                request = _request(
                    key="same-request",
                    principal_id="operator",
                    principal_type=PrincipalType.HUMAN,
                    permissions=OPERATOR_PERMISSIONS,
                )
                first = request_execution_approval(
                    session,
                    request,
                    work_order_id=work_order_id,
                    expected_row_version=1,
                    risk_level="low",
                )
                session.commit()
                replay = request_execution_approval(
                    session,
                    request,
                    work_order_id=work_order_id,
                    expected_row_version=1,
                    risk_level="low",
                )
                session.commit()
                self.assertTrue(replay.replayed)
                self.assertEqual(first.approval_id, replay.approval_id)
                self.assertEqual("waiting_approval", replay.work_order_state)
                self.assertEqual(1, session.query(WorkApproval).count())
                self.assertEqual(1, session.query(AuditEvent).count())
            finally:
                session.close()
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
