from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from app.foundation.scope_static import (
    scan_repository_paths,
    scan_repository_source,
)
from support import REPO_ROOT


class ScopeStaticTests(unittest.TestCase):
    def test_current_repository_tree_passes(self) -> None:
        paths = (REPO_ROOT / "backend/app/repositories").glob("*.py")
        self.assertEqual([], scan_repository_paths(paths))

    def test_unscoped_repository_method_is_rejected(self) -> None:
        source = """
class BrokenRepository:
    def get_by_id(self, object_id):
        return object_id
"""
        violations = scan_repository_source(source)
        self.assertEqual(
            {
                "missing_scope_argument",
                "repository_must_inherit_scoped_base",
            },
            {violation.code for violation in violations},
        )

    def test_direct_session_factory_import_is_rejected(self) -> None:
        source = "from app.database import get_sync_session\n"
        violations = scan_repository_source(source)
        self.assertEqual("unscoped_session_factory", violations[0].code)

    def test_scoped_repository_subclass_is_accepted(self) -> None:
        source = """
class WorkOrderRepository(ScopedRepository):
    def get_by_id(self, scope, object_id):
        return super().get_by_id(scope, object_id)
"""
        self.assertEqual([], scan_repository_source(source))


if __name__ == "__main__":
    unittest.main()
