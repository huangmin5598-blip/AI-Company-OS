from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from app.foundation.context import (
    AuthenticationMethod,
    PrincipalContext,
    PrincipalType,
    ScopeContext,
)
from app.models.base import Base
from app.models.foundation_audit import IdempotencyRecord
from app.models.foundation_identity import Tenant, Workspace  # noqa: F401
from app.repositories.scoped import RepositoryScopeError, ScopedRepository
from app.services.foundation_bootstrap import bootstrap_local_foundation
from support import make_sqlite_session


def _scope(tenant_id: str, workspace_id: str, permissions: set[str]) -> ScopeContext:
    principal = PrincipalContext(
        principal_id=f"principal-{tenant_id}",
        principal_type=PrincipalType.HUMAN,
        authentication_method=AuthenticationMethod.SESSION,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        permission_names=frozenset(permissions),
    )
    return ScopeContext(principal, tenant_id, workspace_id)


class ScopedRepositoryTests(unittest.TestCase):
    def test_scope_before_lookup_and_cross_tenant_non_disclosure(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            engine, session = make_sqlite_session(Path(temporary_directory) / "scope.db")
            try:
                Base.metadata.create_all(engine)
                bootstrap_local_foundation(session)
                session.add(
                    Tenant(
                        tenant_id="ten_other",
                        name="Other",
                        slug="other",
                        status="active",
                        created_by="test",
                        updated_by="test",
                    )
                )
                session.add(
                    Workspace(
                        workspace_id="wsp_other",
                        tenant_id="ten_other",
                        name="Other",
                        slug="other",
                        status="active",
                        created_by="test",
                        updated_by="test",
                    )
                )
                session.flush()
                local_record = IdempotencyRecord(
                    idempotency_record_id="idem_local",
                    tenant_id="ten_local",
                    workspace_id="wsp_personal",
                    scope_key="ten_local:wsp_personal",
                    actor_id="local-founder",
                    command="test",
                    target_type="test",
                    target_id="one",
                    idempotency_key="one",
                    request_payload_hash="sha256:one",
                    status="in_progress",
                    correlation_id="cor_one",
                )
                other_record = IdempotencyRecord(
                    idempotency_record_id="idem_other",
                    tenant_id="ten_other",
                    workspace_id="wsp_other",
                    scope_key="ten_other:wsp_other",
                    actor_id="other",
                    command="test",
                    target_type="test",
                    target_id="two",
                    idempotency_key="two",
                    request_payload_hash="sha256:two",
                    status="in_progress",
                    correlation_id="cor_two",
                )
                session.add_all([local_record, other_record])
                session.commit()

                repository = ScopedRepository(
                    session,
                    IdempotencyRecord,
                    id_attribute="idempotency_record_id",
                    read_permission="audit.read",
                    write_permission="work_order.create",
                )
                local_scope = _scope(
                    "ten_local",
                    "wsp_personal",
                    {"audit.read", "work_order.create"},
                )
                self.assertIsNotNone(repository.get_by_id(local_scope, "idem_local"))
                self.assertIsNone(repository.get_by_id(local_scope, "idem_other"))
                self.assertEqual(1, repository.count(local_scope))

                with self.assertRaises(RepositoryScopeError):
                    repository.add(local_scope, other_record)
            finally:
                session.close()
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
