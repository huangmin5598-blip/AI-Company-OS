from __future__ import annotations

from datetime import datetime, timezone
import unittest

from app.foundation.authorization import AuthorizationDenied
from app.foundation.clock import format_utc, parse_utc
from app.foundation.context import ScopeContext
from app.foundation.identity import new_id
from app.foundation.local_founder import (
    LocalFounderUnavailable,
    resolve_local_founder,
)


class PrincipalContextTests(unittest.TestCase):
    def test_canonical_id_and_time(self) -> None:
        identifier = new_id("aud")
        self.assertRegex(identifier, r"^aud_[0-9a-f]{32}$")
        value = datetime(2026, 6, 7, 1, 2, 3, 456789, tzinfo=timezone.utc)
        serialized = format_utc(value)
        self.assertEqual("2026-06-07T01:02:03.456789Z", serialized)
        self.assertEqual(value, parse_utc(serialized))

    def test_local_founder_is_loopback_only(self) -> None:
        permissions = frozenset({"work_order.read"})
        principal = resolve_local_founder(
            client_host="127.0.0.1",
            local_mode_enabled=True,
            permission_names=permissions,
        )
        self.assertEqual("local-founder", principal.principal_id)
        self.assertTrue(principal.local_mode)

        with self.assertRaises(LocalFounderUnavailable):
            resolve_local_founder(
                client_host="10.0.0.4",
                local_mode_enabled=True,
                permission_names=permissions,
            )
        with self.assertRaises(LocalFounderUnavailable):
            resolve_local_founder(
                client_host="127.0.0.1",
                forwarded_for="198.51.100.4",
                local_mode_enabled=True,
                permission_names=permissions,
            )

    def test_scope_and_permissions_fail_closed(self) -> None:
        principal = resolve_local_founder(
            client_host="::1",
            local_mode_enabled=True,
            permission_names=frozenset({"work_order.read"}),
        )
        scope = ScopeContext(
            principal=principal,
            tenant_id=principal.tenant_id,
            workspace_id=principal.workspace_id,
        )
        scope.require("work_order.read")
        with self.assertRaises(AuthorizationDenied):
            scope.require("work_order.execute")
        with self.assertRaises(ValueError):
            ScopeContext(
                principal=principal,
                tenant_id="ten_other",
                workspace_id=principal.workspace_id,
            )


if __name__ == "__main__":
    unittest.main()
