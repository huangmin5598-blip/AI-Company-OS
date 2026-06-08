from __future__ import annotations

import unittest

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
from app.repositories.canonical_work_order_command import (
    CanonicalCommandRejected,
    CanonicalWorkOrderCommandRepository,
)
from app.services.canonical_execution_service import (
    allocate_execution_attempt,
)
from support import phase2a_authority_database


def _request(
    tenant_id: str,
    workspace_id: str,
    permissions: set[str],
    *,
    key: str,
) -> RequestContext:
    principal = PrincipalContext(
        principal_id=f"principal-{tenant_id}",
        principal_type=PrincipalType.HUMAN,
        authentication_method=AuthenticationMethod.SESSION,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        permission_names=frozenset(permissions),
    )
    return RequestContext(
        scope=ScopeContext(principal, tenant_id, workspace_id),
        origin=RequestOrigin.API,
        idempotency_key=key,
    )


class E1BScopeAndAuthorityTests(unittest.TestCase):
    def test_cross_tenant_and_unresolved_rows_are_non_authoritative(self) -> None:
        with phase2a_authority_database() as (database, work_order_id):
            engine = create_engine(f"sqlite:///{database}")
            session = Session(engine)
            try:
                other = _request(
                    "ten_other",
                    "wsp_other",
                    {"work_order.read", "work_order.execute"},
                    key="other",
                )
                repository = CanonicalWorkOrderCommandRepository(session)
                with self.assertRaisesRegex(
                    CanonicalCommandRejected,
                    "canonical_work_order_not_found",
                ):
                    repository.require_canonical(other.scope, work_order_id)

                session.execute(
                    text(
                        "UPDATE work_orders SET canonical_state=NULL"
                        " WHERE work_order_id=:work_order_id"
                    ),
                    {"work_order_id": work_order_id},
                )
                session.commit()
                local = _request(
                    "ten_local",
                    "wsp_personal",
                    {"work_order.read", "work_order.execute"},
                    key="local",
                )
                with self.assertRaisesRegex(
                    CanonicalCommandRejected,
                    "canonical_work_order_unresolved",
                ):
                    repository.require_canonical(local.scope, work_order_id)
            finally:
                session.close()
                engine.dispose()

    def test_runtime_registry_selection_fails_closed(self) -> None:
        with phase2a_authority_database() as (database, work_order_id):
            engine = create_engine(f"sqlite:///{database}")
            session = Session(engine)
            try:
                session.execute(
                    text(
                        "UPDATE work_orders SET canonical_state='queued', row_version=3"
                        " WHERE work_order_id=:work_order_id"
                    ),
                    {"work_order_id": work_order_id},
                )
                session.commit()
                with self.assertRaisesRegex(
                    CanonicalCommandRejected,
                    "effective_execution_approval_required",
                ):
                    allocate_execution_attempt(
                        session,
                        _request(
                            "ten_local",
                            "wsp_personal",
                            {"work_order.read", "work_order.execute"},
                            key="missing-approval",
                        ),
                        work_order_id=work_order_id,
                        expected_work_order_version=3,
                    )
                session.rollback()
                session.execute(
                    text(
                        "UPDATE runtime_registry SET enabled=0"
                        " WHERE runtime_id='builtin.vs001_echo_markdown'"
                    )
                )
                session.execute(
                    text(
                        "INSERT INTO work_approvals"
                        " (approval_id, tenant_id, workspace_id, scope_key,"
                        " target_type, target_id, target_version, action,"
                        " risk_level, requested_by, requested_at, decision,"
                        " decided_by, decided_at, conditions_json, row_version)"
                        " VALUES ('apr_fixture', 'ten_local', 'wsp_personal',"
                        " 'ten_local:wsp_personal', 'work_order',"
                        " :work_order_id, '2', 'execute', 'low', 'operator',"
                        " CURRENT_TIMESTAMP, 'approved', 'reviewer',"
                        " CURRENT_TIMESTAMP, '[]', 2)"
                    ),
                    {"work_order_id": work_order_id},
                )
                session.commit()
                with self.assertRaises(ValueError):
                    allocate_execution_attempt(
                        session,
                        _request(
                            "ten_local",
                            "wsp_personal",
                            {"work_order.read", "work_order.execute"},
                            key="disabled-runtime",
                        ),
                        work_order_id=work_order_id,
                        expected_work_order_version=3,
                    )
                session.rollback()
            finally:
                session.close()
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
