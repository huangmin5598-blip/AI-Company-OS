from __future__ import annotations

import sqlite3
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from path_bootstrap import ensure_backend_path

ensure_backend_path()

from app.foundation.context import (
    AuthenticationMethod,
    PrincipalContext,
    PrincipalType,
    ScopeContext,
)
from app.repositories.canonical_work_order_read import (
    CanonicalWorkOrderReadRepository,
)
from app.repositories.scoped import ScopedReadRepository
from support import operational_copy_at_0003


def _scope(tenant_id: str, workspace_id: str) -> ScopeContext:
    principal = PrincipalContext(
        principal_id=f"principal-{tenant_id}",
        principal_type=PrincipalType.HUMAN,
        authentication_method=AuthenticationMethod.SESSION,
        tenant_id=tenant_id,
        workspace_id=workspace_id,
        permission_names=frozenset({"work_order.read"}),
    )
    return ScopeContext(principal, tenant_id, workspace_id)


class E1AWorkOrderReadRepositoryTests(unittest.TestCase):
    def test_repository_is_read_only_and_scope_before_lookup(self) -> None:
        with operational_copy_at_0003() as database:
            with sqlite3.connect(database) as connection:
                ids = [
                    row[0]
                    for row in connection.execute(
                        "SELECT work_order_id FROM work_orders ORDER BY work_order_id LIMIT 2"
                    )
                ]
                connection.execute(
                    "UPDATE work_orders SET tenant_id='ten_local',"
                    " workspace_id='wsp_personal', canonical_state='draft',"
                    " row_version=1 WHERE work_order_id=?",
                    (ids[0],),
                )
                connection.execute(
                    "UPDATE work_orders SET tenant_id='ten_other',"
                    " workspace_id='wsp_other', canonical_state='draft',"
                    " row_version=1 WHERE work_order_id=?",
                    (ids[1],),
                )
                connection.commit()

            engine = create_engine(f"sqlite:///{database}")
            session = Session(engine)
            try:
                repository = CanonicalWorkOrderReadRepository(session)
                self.assertIsInstance(repository, ScopedReadRepository)
                for mutator in ("add", "create", "update", "delete"):
                    self.assertFalse(hasattr(repository, mutator), mutator)

                local_scope = _scope("ten_local", "wsp_personal")
                self.assertEqual(
                    ids[0],
                    repository.get_by_id(local_scope, ids[0]).work_order_id,
                )
                self.assertIsNone(repository.get_by_id(local_scope, ids[1]))
                self.assertEqual(1, repository.count(local_scope))
                self.assertEqual(1, len(repository.list(local_scope)))
            finally:
                session.close()
                engine.dispose()

    def test_repository_requires_read_permission(self) -> None:
        with operational_copy_at_0003() as database:
            engine = create_engine(f"sqlite:///{database}")
            session = Session(engine)
            try:
                repository = CanonicalWorkOrderReadRepository(session)
                principal = PrincipalContext(
                    principal_id="no-read",
                    principal_type=PrincipalType.HUMAN,
                    authentication_method=AuthenticationMethod.SESSION,
                    tenant_id="ten_local",
                    workspace_id="wsp_personal",
                )
                scope = ScopeContext(principal, "ten_local", "wsp_personal")
                with self.assertRaises(PermissionError):
                    repository.count(scope)
            finally:
                session.close()
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
