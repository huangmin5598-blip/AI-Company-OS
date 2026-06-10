from __future__ import annotations

from datetime import timedelta
import unittest
from unittest import mock

from sqlalchemy import create_engine, text
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
from app.models.foundation_audit import IdempotencyRecord
from app.models.foundation_execution import WorkApproval, WorkAttempt, WorkReview
from app.services.canonical_execution_service import (
    allocate_execution_attempt,
    claim_execution_attempt,
    decide_execution_approval,
    ingest_attempt_result,
    record_invocation_started,
    request_execution_approval,
)
from support import (
    add_result_artifact_fixture,
    fixture_preflight_lineage,
    phase2a_authority_database,
)


def _request(
    *,
    key: str = "atomicity",
    principal_id: str = "operator",
    principal_type: PrincipalType = PrincipalType.HUMAN,
    permissions: set[str] | None = None,
) -> RequestContext:
    principal = PrincipalContext(
        principal_id=principal_id,
        principal_type=principal_type,
        authentication_method=AuthenticationMethod.SESSION,
        tenant_id="ten_local",
        workspace_id="wsp_personal",
        permission_names=frozenset(
            permissions
            or {"work_order.read", "work_order.execute", "approval.request"}
        ),
    )
    return RequestContext(
        scope=ScopeContext(principal, "ten_local", "wsp_personal"),
        origin=RequestOrigin.API,
        idempotency_key=key,
    )


class E1BTransactionAtomicityTests(unittest.TestCase):
    def test_audit_failure_rolls_back_state_approval_and_idempotency(self) -> None:
        with phase2a_authority_database() as (database, work_order_id):
            engine = create_engine(f"sqlite:///{database}")
            session = Session(engine)
            try:
                with (
                    mock.patch(
                        "app.services.canonical_execution_service.append_audit_event",
                        side_effect=RuntimeError("audit unavailable"),
                    ),
                    self.assertRaisesRegex(RuntimeError, "audit unavailable"),
                ):
                    request_execution_approval(
                        session,
                        _request(),
                        work_order_id=work_order_id,
                        expected_row_version=1,
                        risk_level="low",
                    )
                session.rollback()
                row = session.execute(
                    text(
                        "SELECT canonical_state, row_version FROM work_orders"
                        " WHERE work_order_id=:work_order_id"
                    ),
                    {"work_order_id": work_order_id},
                ).one()
                self.assertEqual(("draft", 1), tuple(row))
                self.assertEqual(0, session.query(WorkApproval).count())
                self.assertEqual(0, session.query(IdempotencyRecord).count())
            finally:
                session.close()
                engine.dispose()

    def test_result_audit_failure_rolls_back_attempt_work_order_and_review(self) -> None:
        with phase2a_authority_database() as (database, work_order_id):
            engine = create_engine(f"sqlite:///{database}")
            session = Session(engine)
            try:
                requested = request_execution_approval(
                    session,
                    _request(key="request"),
                    work_order_id=work_order_id,
                    expected_row_version=1,
                    risk_level="low",
                )
                session.commit()
                decide_execution_approval(
                    session,
                    _request(
                        key="approve",
                        principal_id="reviewer",
                        permissions={"work_order.read", "approval.decide"},
                    ),
                    work_order_id=work_order_id,
                    approval_id=requested.approval_id,
                    decision="approved",
                    expected_work_order_version=2,
                    expected_approval_version=1,
                )
                session.commit()
                allocated = allocate_execution_attempt(
                    session,
                    _request(key="allocate"),
                    work_order_id=work_order_id,
                    expected_work_order_version=3,
                )
                session.commit()
                wrapper_permissions = {"work_order.read", "work_order.execute"}
                claimed = claim_execution_attempt(
                    session,
                    _request(
                        key="claim",
                        principal_id="wrapper",
                        principal_type=PrincipalType.RUNTIME_WRAPPER,
                        permissions=wrapper_permissions,
                    ),
                    work_order_id=work_order_id,
                    attempt_id=allocated.attempt_id,
                    expected_work_order_version=3,
                    expected_attempt_version=1,
                    lease_owner="wrapper",
                    lease_duration=timedelta(minutes=5),
                )
                session.commit()
                preflight_payload, preflight_hash, preflight_ref = (
                    fixture_preflight_lineage(
                        allocated.attempt_id,
                        work_order_id,
                    )
                )
                record_invocation_started(
                    session,
                    _request(
                        key="start",
                        principal_id="wrapper",
                        principal_type=PrincipalType.RUNTIME_WRAPPER,
                        permissions=wrapper_permissions,
                    ),
                    work_order_id=work_order_id,
                    attempt_id=allocated.attempt_id,
                    lease_token=claimed.lease_token,
                    lease_generation=1,
                    expected_attempt_version=2,
                    runtime_session_id="run-atomicity",
                    preflight_ref=preflight_ref,
                    preflight_hash=preflight_hash,
                    preflight_evidence=preflight_payload,
                )
                session.commit()
                artifact_set_hash = add_result_artifact_fixture(
                    session,
                    work_order_id=work_order_id,
                    attempt_id=allocated.attempt_id,
                    content_hash="sha256:" + ("c" * 64),
                )
                session.commit()
                existing_idempotency = session.query(IdempotencyRecord).count()

                with (
                    mock.patch(
                        "app.services.canonical_execution_service.append_audit_event",
                        side_effect=RuntimeError("audit unavailable"),
                    ),
                    self.assertRaisesRegex(RuntimeError, "audit unavailable"),
                ):
                    ingest_attempt_result(
                        session,
                        _request(
                            key="result",
                            principal_id="wrapper",
                            principal_type=PrincipalType.RUNTIME_WRAPPER,
                            permissions=wrapper_permissions,
                        ),
                        work_order_id=work_order_id,
                        attempt_id=allocated.attempt_id,
                        lease_token=claimed.lease_token,
                        lease_generation=1,
                        expected_work_order_version=4,
                        expected_attempt_version=3,
                        result_idempotency_key="result-atomicity",
                        evidence=AttemptResultEvidence(
                            terminal_state="succeeded",
                            result_ref="scratch://result.md",
                            stdout_ref="scratch://stdout.txt",
                            stderr_ref="scratch://stderr.txt",
                            exit_code=0,
                            result_payload_hash="sha256:" + ("c" * 64),
                            cost_summary={"amount": 0},
                        ),
                        artifact_ids=["art_fixture_result"],
                        artifact_set_hash=artifact_set_hash,
                    )
                session.rollback()

                attempt = session.get(WorkAttempt, allocated.attempt_id)
                self.assertEqual(("running", 3), (attempt.state, attempt.row_version))
                state = session.execute(
                    text(
                        "SELECT canonical_state, row_version FROM work_orders"
                        " WHERE work_order_id=:work_order_id"
                    ),
                    {"work_order_id": work_order_id},
                ).one()
                self.assertEqual(("running", 4), tuple(state))
                self.assertEqual(0, session.query(WorkReview).count())
                self.assertEqual(
                    existing_idempotency,
                    session.query(IdempotencyRecord).count(),
                )
            finally:
                session.close()
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
