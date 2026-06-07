from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from sqlalchemy import select

from app.models.base import Base
from app.models.foundation_audit import AuditEvent  # noqa: F401
from app.models.foundation_identity import (
    FoundationUser,
    Membership,
    MembershipRole,
    Permission,
    Role,
    RolePermission,
    Tenant,
    Workspace,
)
from app.services.foundation_bootstrap import (
    PERMISSIONS,
    bootstrap_local_foundation,
)
from app.services.principal_service import (
    PrincipalResolutionDenied,
    resolve_membership_principal,
)
from app.foundation.context import AuthenticationMethod
from support import make_sqlite_session


class TenancyBootstrapTests(unittest.TestCase):
    def test_bootstrap_is_explicit_idempotent_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            engine, session = make_sqlite_session(
                Path(temporary_directory) / "foundation.db"
            )
            try:
                Base.metadata.create_all(engine)
                first = bootstrap_local_foundation(session)
                session.commit()
                second = bootstrap_local_foundation(session)
                session.commit()

                self.assertEqual(first, second)
                self.assertEqual(1, session.query(Tenant).count())
                self.assertEqual(1, session.query(Workspace).count())
                self.assertEqual(1, session.query(FoundationUser).count())
                self.assertEqual(1, session.query(Membership).count())
                self.assertEqual(5, session.query(Role).count())
                self.assertEqual(len(PERMISSIONS), session.query(Permission).count())
                self.assertGreater(session.query(RolePermission).count(), 0)
                self.assertEqual(1, session.query(MembershipRole).count())
                owner = session.execute(
                    select(Role).where(Role.name == "Owner")
                ).scalar_one()
                self.assertEqual("rol_owner", owner.role_id)

                principal = resolve_membership_principal(
                    session,
                    principal_name="local-founder",
                    tenant_id=first.tenant_id,
                    workspace_id=first.workspace_id,
                    authentication_method=AuthenticationMethod.LOCAL_LOOPBACK,
                    local_mode=True,
                )
                self.assertEqual(first.membership_id, principal.membership_id)
                self.assertEqual(frozenset({"Owner"}), principal.role_names)
                self.assertEqual(PERMISSIONS, set(principal.permission_names))

                with self.assertRaises(PrincipalResolutionDenied):
                    resolve_membership_principal(
                        session,
                        principal_name="local-founder",
                        tenant_id="ten_other",
                        workspace_id="wsp_other",
                        authentication_method=AuthenticationMethod.SESSION,
                    )
            finally:
                session.close()
                engine.dispose()


if __name__ == "__main__":
    unittest.main()
