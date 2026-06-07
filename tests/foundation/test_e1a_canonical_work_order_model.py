from __future__ import annotations

import unittest

from path_bootstrap import ensure_backend_path

ensure_backend_path()

from app.models.base import Base
from app.models.foundation_base import FoundationBase


class E1ACanonicalWorkOrderModelTests(unittest.TestCase):
    def test_import_does_not_pollute_existing_metadata(self) -> None:
        legacy_before = set(Base.metadata.tables)
        foundation_before = set(FoundationBase.metadata.tables)

        from app.models.canonical_work_order import (
            CanonicalReadBase,
            CanonicalWorkOrder,
        )

        self.assertIs(CanonicalWorkOrder.__table__.metadata, CanonicalReadBase.metadata)
        self.assertIsNot(CanonicalReadBase.metadata, Base.metadata)
        self.assertIsNot(CanonicalReadBase.metadata, FoundationBase.metadata)
        self.assertEqual(legacy_before, set(Base.metadata.tables))
        self.assertEqual(foundation_before, set(FoundationBase.metadata.tables))

    def test_mapping_matches_existing_and_0003_columns(self) -> None:
        from app.models.canonical_work_order import CanonicalWorkOrder

        self.assertEqual("work_orders", CanonicalWorkOrder.__tablename__)
        self.assertTrue(
            {
                "work_order_id",
                "tenant_id",
                "workspace_id",
                "skill_id",
                "task_type",
                "input_context",
                "expected_output",
                "status",
                "canonical_state",
                "row_version",
                "created_at",
                "terminal_at",
            }.issubset(CanonicalWorkOrder.__table__.columns.keys())
        )


if __name__ == "__main__":
    unittest.main()
