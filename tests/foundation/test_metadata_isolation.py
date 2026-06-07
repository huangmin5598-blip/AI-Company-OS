from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from sqlalchemy import create_engine, inspect

from path_bootstrap import ensure_backend_path

ensure_backend_path()

import app.models  # noqa: F401
from app.models.base import Base
from app.models.foundation_audit import AuditEvent  # noqa: F401
from app.models.foundation_base import FoundationBase
from app.models.foundation_execution import WorkAttempt  # noqa: F401
from app.models.foundation_identity import Tenant  # noqa: F401


class MetadataIsolationTests(unittest.TestCase):
    def test_foundation_tables_are_not_registered_on_legacy_base(self) -> None:
        foundation_tables = {
            "tenants",
            "workspaces",
            "audit_events",
            "promotion_records",
            "work_attempts",
            "work_approvals",
            "work_reviews",
        }
        self.assertTrue(foundation_tables.issubset(FoundationBase.metadata.tables))
        self.assertTrue(foundation_tables.isdisjoint(Base.metadata.tables))

    def test_legacy_create_all_cannot_create_foundation_tables(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Path(temporary_directory) / "legacy-create-all.db"
            engine = create_engine(f"sqlite:///{database}")
            try:
                Base.metadata.create_all(engine)
                tables = set(inspect(engine).get_table_names())
            finally:
                engine.dispose()
        self.assertIn("work_orders", tables)
        self.assertTrue(
            {
                "tenants",
                "workspaces",
                "audit_events",
                "promotion_records",
                "work_attempts",
            }.isdisjoint(tables)
        )


if __name__ == "__main__":
    unittest.main()
