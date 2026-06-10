from __future__ import annotations

from datetime import timedelta
import json
from pathlib import Path
import tempfile
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from path_bootstrap import ensure_backend_path


ensure_backend_path()

from app.foundation.context import (  # noqa: E402
    AuthenticationMethod,
    PrincipalContext,
    PrincipalType,
    RequestContext,
    RequestOrigin,
    ScopeContext,
)
from app.models.foundation_audit import AuditPacket  # noqa: E402
from app.models.foundation_execution import WorkAttempt  # noqa: E402
from app.repositories.canonical_work_order_command import (  # noqa: E402
    CanonicalCommandRejected,
)
from app.services.canonical_execution_service import (  # noqa: E402
    allocate_execution_attempt,
    claim_execution_attempt,
    decide_execution_approval,
    decide_execution_review,
    ingest_attempt_result,
    record_invocation_started,
    request_execution_approval,
)
from app.services.controlled_builtin_executor import (  # noqa: E402
    execute_controlled_builtin,
    preflight_controlled_builtin,
)
from support import (  # noqa: E402
    REPO_ROOT,
    add_result_artifact_fixture,
    phase2a_authority_database,
    tree_manifest,
)


def _request(
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


class E1BExecutorIntegrationTests(unittest.TestCase):
    def test_attempt_bound_builtin_requires_review_before_done(self) -> None:
        before_data = tree_manifest(REPO_ROOT / "backend/data")
        before_private = tree_manifest(REPO_ROOT / "private")
        operator_permissions = {
            "approval.request",
            "work_order.execute",
            "work_order.read",
        }
        reviewer_permissions = {
            "approval.decide",
            "review.decide",
            "work_order.read",
        }
        wrapper_permissions = {"work_order.execute", "work_order.read"}
        with phase2a_authority_database() as (database, work_order_id):
            engine = create_engine(f"sqlite:///{database}")
            session = Session(engine)
            try:
                with tempfile.TemporaryDirectory() as temporary:
                    requested = request_execution_approval(
                        session,
                        _request(
                            "p2b-request",
                            "operator",
                            PrincipalType.HUMAN,
                            operator_permissions,
                        ),
                        work_order_id=work_order_id,
                        expected_row_version=1,
                        risk_level="low",
                    )
                    session.commit()
                    decide_execution_approval(
                        session,
                        _request(
                            "p2b-approve",
                            "reviewer",
                            PrincipalType.HUMAN,
                            reviewer_permissions,
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
                        _request(
                            "p2b-allocate",
                            "operator",
                            PrincipalType.HUMAN,
                            operator_permissions,
                        ),
                        work_order_id=work_order_id,
                        expected_work_order_version=3,
                    )
                    session.commit()
                    claimed = claim_execution_attempt(
                        session,
                        _request(
                            "p2b-claim",
                            "wrapper",
                            PrincipalType.RUNTIME_WRAPPER,
                            wrapper_permissions,
                        ),
                        work_order_id=work_order_id,
                        attempt_id=allocated.attempt_id,
                        expected_work_order_version=3,
                        expected_attempt_version=1,
                        lease_owner="controlled-builtin",
                        lease_duration=timedelta(minutes=5),
                    )
                    session.commit()

                    attempt = session.get(WorkAttempt, allocated.attempt_id)
                    scratch = Path(temporary) / allocated.attempt_id
                    scratch.mkdir()
                    preflight = preflight_controlled_builtin(
                        attempt,
                        _request(
                            "p2b-preflight",
                            "wrapper",
                            PrincipalType.RUNTIME_WRAPPER,
                            wrapper_permissions,
                        ).scope,
                        scratch_root=scratch,
                        allowed_temp_root=Path(temporary),
                    )
                    with self.assertRaisesRegex(
                        CanonicalCommandRejected,
                        "invocation_preflight_lineage_mismatch",
                    ):
                        record_invocation_started(
                            session,
                            _request(
                                "p2b-start-invalid",
                                "wrapper",
                                PrincipalType.RUNTIME_WRAPPER,
                                wrapper_permissions,
                            ),
                            work_order_id=work_order_id,
                            attempt_id=allocated.attempt_id,
                            lease_token=claimed.lease_token,
                            lease_generation=1,
                            expected_attempt_version=2,
                            runtime_session_id=f"builtin:{allocated.attempt_id}",
                            preflight_ref=(
                                "preflight://wrong/"
                                + preflight.decision_hash
                            ),
                            preflight_hash=preflight.decision_hash,
                            preflight_evidence=preflight.payload(),
                        )
                    record_invocation_started(
                        session,
                        _request(
                            "p2b-start",
                            "wrapper",
                            PrincipalType.RUNTIME_WRAPPER,
                            wrapper_permissions,
                        ),
                        work_order_id=work_order_id,
                        attempt_id=allocated.attempt_id,
                        lease_token=claimed.lease_token,
                        lease_generation=1,
                        expected_attempt_version=2,
                        runtime_session_id=f"builtin:{allocated.attempt_id}",
                        preflight_ref=preflight.evidence_ref,
                        preflight_hash=preflight.decision_hash,
                        preflight_evidence=preflight.payload(),
                    )
                    session.commit()
                    self.assertFalse(session.in_transaction())

                    run = execute_controlled_builtin(
                        preflight,
                        {
                            "heading": "Attempt-bound output",
                            "body": "Review remains authoritative.",
                        },
                    )
                    self.assertFalse(session.in_transaction())

                    artifact_set_hash = add_result_artifact_fixture(
                        session,
                        work_order_id=work_order_id,
                        attempt_id=allocated.attempt_id,
                        content_hash=run.evidence.result_payload_hash,
                    )
                    session.commit()
                    ingested = ingest_attempt_result(
                        session,
                        _request(
                            "p2b-result",
                            "wrapper",
                            PrincipalType.RUNTIME_WRAPPER,
                            wrapper_permissions,
                        ),
                        work_order_id=work_order_id,
                        attempt_id=allocated.attempt_id,
                        lease_token=claimed.lease_token,
                        lease_generation=1,
                        expected_work_order_version=4,
                        expected_attempt_version=3,
                        result_idempotency_key="p2b-result-1",
                        evidence=run.evidence,
                        artifact_ids=["art_fixture_result"],
                        artifact_set_hash=artifact_set_hash,
                    )
                    session.commit()
                    self.assertEqual("waiting_review", ingested.work_order_state)
                    persisted = session.get(WorkAttempt, allocated.attempt_id)
                    authenticity = json.loads(
                        persisted.invocation_authenticity_json
                    )
                    self.assertEqual(
                        preflight.evidence_ref,
                        authenticity["preflight_ref"],
                    )
                    self.assertEqual(
                        preflight.decision_hash,
                        authenticity["preflight_hash"],
                    )
                    self.assertEqual(
                        preflight.payload(),
                        authenticity["preflight_evidence"],
                    )
                    self.assertEqual(run.evidence.result_ref, persisted.result_ref)
                    packet = session.get(AuditPacket, ingested.audit_packet_id)
                    self.assertEqual(
                        "artifact://art_fixture_result",
                        packet.result_ref,
                    )

                    reviewed = decide_execution_review(
                        session,
                        _request(
                            "p2b-review",
                            "reviewer",
                            PrincipalType.HUMAN,
                            reviewer_permissions,
                        ),
                        work_order_id=work_order_id,
                        review_id=ingested.review_id,
                        decision="passed",
                        expected_work_order_version=5,
                        expected_review_version=1,
                        findings=[{"code": "builtin_result_verified"}],
                    )
                    session.commit()
                    self.assertEqual("done", reviewed.work_order_state)
            finally:
                session.close()
                engine.dispose()
        self.assertEqual(before_data, tree_manifest(REPO_ROOT / "backend/data"))
        self.assertEqual(before_private, tree_manifest(REPO_ROOT / "private"))


if __name__ == "__main__":
    unittest.main()
