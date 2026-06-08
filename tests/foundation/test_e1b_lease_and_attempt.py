from __future__ import annotations

from datetime import datetime, timedelta, timezone
import unittest

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
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
from app.models.foundation_execution import WorkAttempt
from app.services.execution_persistence_service import (
    AttemptConflict,
    LeaseRejected,
    claim_attempt,
    create_attempt,
    start_attempt,
)
from support import phase2a_authority_database


def _request(key: str) -> RequestContext:
    principal = PrincipalContext(
        principal_id="wrapper",
        principal_type=PrincipalType.RUNTIME_WRAPPER,
        authentication_method=AuthenticationMethod.SERVICE_CREDENTIAL,
        tenant_id="ten_local",
        workspace_id="wsp_personal",
        permission_names=frozenset({"work_order.execute"}),
    )
    return RequestContext(
        scope=ScopeContext(principal, "ten_local", "wsp_personal"),
        origin=RequestOrigin.INTERNAL_WORKER,
        idempotency_key=key,
    )


class E1BLeaseAndAttemptTests(unittest.TestCase):
    def _attempt(self, session: Session, work_order_id: str) -> WorkAttempt:
        return create_attempt(
            session,
            _request("create"),
            work_order_id=work_order_id,
            runtime_adapter_id="builtin.vs001_echo_markdown",
            runtime_adapter_version="sha256:" + ("a" * 64),
            runtime_config_snapshot={"executor": "controlled_builtin"},
        )

    def test_wrong_token_generation_and_stale_lease_fail_closed(self) -> None:
        with phase2a_authority_database() as (database, work_order_id):
            engine = create_engine(f"sqlite:///{database}")
            session = Session(engine)
            try:
                attempt = self._attempt(session, work_order_id)
                session.commit()
                claim = claim_attempt(
                    session,
                    _request("claim"),
                    attempt_id=attempt.attempt_id,
                    lease_owner="wrapper",
                    lease_duration=timedelta(minutes=5),
                    expected_row_version=1,
                    now=datetime(2026, 6, 9, tzinfo=timezone.utc),
                )
                session.commit()
                cases = (
                    ("00" * 32, 1, datetime(2026, 6, 9, 0, 1, tzinfo=timezone.utc)),
                    (claim.lease_token, 2, datetime(2026, 6, 9, 0, 1, tzinfo=timezone.utc)),
                    (claim.lease_token, 1, datetime(2026, 6, 9, 0, 6, tzinfo=timezone.utc)),
                )
                for token, generation, now in cases:
                    with self.assertRaises(LeaseRejected):
                        start_attempt(
                            session,
                            _request("start"),
                            attempt_id=attempt.attempt_id,
                            lease_token=token,
                            lease_generation=generation,
                            expected_row_version=2,
                            runtime_session_id="run",
                            invocation_authenticity={"registry_selected": True},
                            now=now,
                        )
                    session.rollback()
            finally:
                session.close()
                engine.dispose()

    def test_active_attempt_and_attempt_number_constraints_are_distinct(self) -> None:
        with phase2a_authority_database() as (database, work_order_id):
            engine = create_engine(f"sqlite:///{database}")
            session = Session(engine)
            try:
                first = self._attempt(session, work_order_id)
                second = self._attempt(session, work_order_id)
                session.commit()
                claim_attempt(
                    session,
                    _request("claim-first"),
                    attempt_id=first.attempt_id,
                    lease_owner="first",
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
                        _request("claim-second"),
                        attempt_id=second.attempt_id,
                        lease_owner="second",
                        lease_duration=timedelta(minutes=5),
                        expected_row_version=1,
                    )
                session.rollback()

                with self.assertRaises(IntegrityError):
                    session.execute(
                        text(
                            "INSERT INTO work_attempts"
                            " (attempt_id, tenant_id, workspace_id, scope_key,"
                            " work_order_id, attempt_number, trigger_reason, state,"
                            " row_version, runtime_adapter_id, runtime_adapter_version,"
                            " runtime_config_snapshot_json, lease_generation,"
                            " invocation_authenticity_json, allowed_read_refs_json,"
                            " allowed_write_refs_json, created_by)"
                            " SELECT :attempt_id, tenant_id, workspace_id, scope_key,"
                            " work_order_id, attempt_number, trigger_reason, 'created',"
                            " 1, runtime_adapter_id, runtime_adapter_version,"
                            " runtime_config_snapshot_json, 0, '{}', '[]', '[]',"
                            " created_by FROM work_attempts WHERE attempt_id=:source"
                        ),
                        {"attempt_id": "att_duplicate", "source": first.attempt_id},
                    )
                    session.flush()
                session.rollback()
            finally:
                session.close()
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
