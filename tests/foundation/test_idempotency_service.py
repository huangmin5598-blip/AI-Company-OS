from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from app.foundation.context import RequestContext, RequestOrigin, ScopeContext
from app.foundation.local_founder import resolve_local_founder
from app.models.base import Base
from app.models.foundation_audit import IdempotencyRecord
from app.models.foundation_identity import Tenant  # noqa: F401
from app.services.foundation_bootstrap import bootstrap_local_foundation
from app.services.idempotency_service import (
    IdempotencyConflict,
    begin_idempotent_command,
    complete_idempotent_command,
)
from support import make_sqlite_session


class IdempotencyServiceTests(unittest.TestCase):
    def test_scoped_replay_and_payload_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            engine, session = make_sqlite_session(
                Path(temporary_directory) / "idempotency.db"
            )
            try:
                Base.metadata.create_all(engine)
                bootstrap = bootstrap_local_foundation(session)
                session.commit()
                principal = resolve_local_founder(
                    client_host="127.0.0.1",
                    local_mode_enabled=True,
                    permission_names=bootstrap.permission_names,
                )
                request = RequestContext(
                    scope=ScopeContext(
                        principal,
                        bootstrap.tenant_id,
                        bootstrap.workspace_id,
                    ),
                    origin=RequestOrigin.API,
                    idempotency_key="request-1",
                )
                first = begin_idempotent_command(
                    session,
                    request,
                    command="work_order.create",
                    target_type="work_order",
                    target_id="wo_test",
                    request_payload={"value": 1},
                )
                complete_idempotent_command(
                    first.record,
                    response_ref="result://one",
                    response_payload={"ok": True},
                )
                session.commit()

                replay = begin_idempotent_command(
                    session,
                    request,
                    command="work_order.create",
                    target_type="work_order",
                    target_id="wo_test",
                    request_payload={"value": 1},
                )
                self.assertTrue(replay.replay)
                self.assertEqual(1, session.query(IdempotencyRecord).count())

                with self.assertRaises(IdempotencyConflict):
                    begin_idempotent_command(
                        session,
                        request,
                        command="work_order.create",
                        target_type="work_order",
                        target_id="wo_test",
                        request_payload={"value": 2},
                    )
            finally:
                session.close()
                engine.dispose()

    def test_same_raw_key_is_independent_across_scopes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            engine, session = make_sqlite_session(
                Path(temporary_directory) / "scope-idempotency.db"
            )
            try:
                Base.metadata.create_all(engine)
                local = bootstrap_local_foundation(session)
                from app.models.foundation_identity import Tenant, Workspace

                session.add(
                    Tenant(
                        tenant_id="ten_other",
                        name="Other",
                        slug="other",
                        status="active",
                        created_by="other",
                        updated_by="other",
                    )
                )
                session.add(
                    Workspace(
                        workspace_id="wsp_other",
                        tenant_id="ten_other",
                        name="Other",
                        slug="other",
                        status="active",
                        created_by="other",
                        updated_by="other",
                    )
                )
                session.flush()

                local_principal = resolve_local_founder(
                    client_host="127.0.0.1",
                    local_mode_enabled=True,
                    permission_names=local.permission_names,
                )
                from app.foundation.context import (
                    AuthenticationMethod,
                    PrincipalContext,
                    PrincipalType,
                )

                other_principal = PrincipalContext(
                    principal_id="other",
                    principal_type=PrincipalType.HUMAN,
                    authentication_method=AuthenticationMethod.SESSION,
                    tenant_id="ten_other",
                    workspace_id="wsp_other",
                )
                requests = [
                    RequestContext(
                        scope=ScopeContext(
                            local_principal,
                            local.tenant_id,
                            local.workspace_id,
                        ),
                        origin=RequestOrigin.API,
                        idempotency_key="same-key",
                    ),
                    RequestContext(
                        scope=ScopeContext(
                            other_principal,
                            "ten_other",
                            "wsp_other",
                        ),
                        origin=RequestOrigin.API,
                        idempotency_key="same-key",
                    ),
                ]
                for request in requests:
                    begin_idempotent_command(
                        session,
                        request,
                        command="work_order.create",
                        target_type="work_order",
                        target_id="wo_same",
                        request_payload={"value": 1},
                    )
                session.commit()
                self.assertEqual(2, session.query(IdempotencyRecord).count())
            finally:
                session.close()
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
