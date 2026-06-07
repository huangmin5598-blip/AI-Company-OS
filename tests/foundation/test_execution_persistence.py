from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from sqlalchemy.orm import Session

from path_bootstrap import ensure_backend_path

ensure_backend_path()

from app.foundation.context import RequestContext, RequestOrigin, ScopeContext
from app.foundation.local_founder import resolve_local_founder
from app.models.foundation_execution import WorkAttempt
from app.services.execution_persistence_service import (
    AttemptConflict,
    LeaseRejected,
    claim_attempt,
    create_approval_request,
    create_attempt,
    create_review_request,
    heartbeat_attempt,
)
from app.services.foundation_bootstrap import bootstrap_local_foundation
from support import create_foundation_schema, make_sqlite_session


class ExecutionPersistenceTests(unittest.TestCase):
    def _request(self, session, *, key: str = "execution-1") -> RequestContext:
        bootstrap = bootstrap_local_foundation(session)
        session.commit()
        principal = resolve_local_founder(
            client_host="127.0.0.1",
            local_mode_enabled=True,
            permission_names=bootstrap.permission_names,
        )
        return RequestContext(
            scope=ScopeContext(
                principal,
                bootstrap.tenant_id,
                bootstrap.workspace_id,
            ),
            origin=RequestOrigin.API,
            idempotency_key=key,
        )

    def _create(self, session, request, work_order_id="wo_future"):
        return create_attempt(
            session,
            request,
            work_order_id=work_order_id,
            runtime_adapter_id="local_script",
            runtime_adapter_version="p0",
            runtime_config_snapshot={"enabled": True},
            allowed_read_refs=["workspace://input"],
            allowed_write_refs=["workspace://output"],
        )

    def test_claim_uses_hash_only_and_heartbeat_fences_token(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            engine, session = make_sqlite_session(
                Path(temporary_directory) / "lease.db"
            )
            try:
                create_foundation_schema(engine)
                request = self._request(session)
                attempt = self._create(session, request)
                session.commit()
                claim = claim_attempt(
                    session,
                    request,
                    attempt_id=attempt.attempt_id,
                    lease_owner="wrapper:local",
                    lease_duration=timedelta(minutes=5),
                    expected_row_version=1,
                    now=datetime(2026, 6, 7, tzinfo=timezone.utc),
                )
                session.commit()

                self.assertEqual(64, len(claim.lease_token))
                self.assertNotEqual(
                    claim.lease_token,
                    claim.attempt.lease_token_hash,
                )
                self.assertTrue(claim.attempt.lease_token_hash.startswith("sha256:"))
                self.assertEqual(1, claim.attempt.lease_generation)
                self.assertEqual(2, claim.attempt.row_version)

                heartbeat = heartbeat_attempt(
                    session,
                    request,
                    attempt_id=attempt.attempt_id,
                    lease_token=claim.lease_token,
                    lease_generation=1,
                    extend_by=timedelta(minutes=5),
                    expected_row_version=2,
                    now=datetime(2026, 6, 7, 0, 1, tzinfo=timezone.utc),
                )
                self.assertEqual(3, heartbeat.row_version)
                with self.assertRaises(LeaseRejected):
                    heartbeat_attempt(
                        session,
                        request,
                        attempt_id=attempt.attempt_id,
                        lease_token="00" * 32,
                        lease_generation=1,
                        extend_by=timedelta(minutes=5),
                        expected_row_version=3,
                        now=datetime(2026, 6, 7, 0, 2, tzinfo=timezone.utc),
                    )
            finally:
                session.rollback()
                session.close()
                engine.dispose()

    def test_second_claim_is_rejected_by_optimistic_version(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Path(temporary_directory) / "claim-race.db"
            engine, bootstrap_session = make_sqlite_session(database)
            try:
                create_foundation_schema(engine)
                request = self._request(bootstrap_session)
                attempt = self._create(bootstrap_session, request, "wo_race")
                bootstrap_session.commit()
                attempt_id = attempt.attempt_id

                first = Session(engine)
                second = Session(engine)
                try:
                    claim_attempt(
                        first,
                        request,
                        attempt_id=attempt_id,
                        lease_owner="wrapper:first",
                        lease_duration=timedelta(minutes=5),
                        expected_row_version=1,
                    )
                    first.commit()
                    with self.assertRaises(AttemptConflict):
                        claim_attempt(
                            second,
                            request,
                            attempt_id=attempt_id,
                            lease_owner="wrapper:second",
                            lease_duration=timedelta(minutes=5),
                            expected_row_version=1,
                        )
                finally:
                    first.close()
                    second.close()
            finally:
                bootstrap_session.close()
                engine.dispose()

    def test_parallel_attempt_claim_is_disabled_by_database_constraint(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            engine, session = make_sqlite_session(
                Path(temporary_directory) / "parallel.db"
            )
            try:
                create_foundation_schema(engine)
                request = self._request(session)
                first = self._create(session, request, "wo_parallel")
                second = create_attempt(
                    session,
                    request,
                    work_order_id="wo_parallel",
                    runtime_adapter_id="local_script",
                    runtime_adapter_version="p0",
                    runtime_config_snapshot={},
                    trigger_reason="retry",
                    parent_attempt_id=first.attempt_id,
                )
                session.commit()
                claim_attempt(
                    session,
                    request,
                    attempt_id=first.attempt_id,
                    lease_owner="wrapper:first",
                    lease_duration=timedelta(minutes=5),
                    expected_row_version=1,
                )
                session.commit()
                with self.assertRaisesRegex(
                    AttemptConflict,
                    "active_attempt_exists",
                ):
                    claim_attempt(
                        session,
                        request,
                        attempt_id=second.attempt_id,
                        lease_owner="wrapper:second",
                        lease_duration=timedelta(minutes=5),
                        expected_row_version=1,
                    )
                session.rollback()
                self.assertEqual("created", session.get(WorkAttempt, second.attempt_id).state)
            finally:
                session.close()
                engine.dispose()

    def test_retry_number_and_review_scope_are_canonical(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            engine, session = make_sqlite_session(
                Path(temporary_directory) / "review.db"
            )
            try:
                create_foundation_schema(engine)
                request = self._request(session)
                first = self._create(session, request, "wo_review")
                second = create_attempt(
                    session,
                    request,
                    work_order_id="wo_review",
                    runtime_adapter_id="local_script",
                    runtime_adapter_version="p0",
                    runtime_config_snapshot={},
                    trigger_reason="retry",
                    parent_attempt_id=first.attempt_id,
                )
                self.assertEqual((1, 2), (first.attempt_number, second.attempt_number))
                approval = create_approval_request(
                    session,
                    request,
                    target_type="work_order",
                    target_id="wo_review",
                    target_version="1",
                    action="execute",
                    risk_level="medium",
                )
                with self.assertRaisesRegex(
                    ValueError,
                    "review_requires_terminal_attempt",
                ):
                    create_review_request(
                        session,
                        request,
                        work_order_id="wo_review",
                        attempt_id=second.attempt_id,
                        review_type="acceptance",
                        artifact_ids=["artifact://one"],
                        criteria_snapshot={"required": ["quality"]},
                    )
                second.state = "succeeded"
                session.flush()
                review = create_review_request(
                    session,
                    request,
                    work_order_id="wo_review",
                    attempt_id=second.attempt_id,
                    review_type="acceptance",
                    artifact_ids=["artifact://one"],
                    criteria_snapshot={"required": ["quality"]},
                )
                self.assertEqual("requested", approval.decision)
                self.assertEqual("requested", review.state)
                self.assertEqual(second.attempt_id, review.attempt_id)
                self.assertEqual("succeeded", second.state)
                self.assertEqual(2, session.query(WorkAttempt).count())
            finally:
                session.rollback()
                session.close()
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
