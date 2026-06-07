from __future__ import annotations

from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect

from path_bootstrap import ensure_backend_path

ensure_backend_path()

from app.models.foundation_base import FoundationBase
from app.models.foundation_execution import WorkAttempt  # noqa: F401
from app.models.foundation_identity import Tenant  # noqa: F401
from app.models.foundation_audit import AuditEvent  # noqa: F401
from support import OPERATIONAL_DB, REPO_ROOT, load_f0_env


RT2_TABLES = {
    "migration_batches",
    "promotion_records",
    "work_attempts",
    "work_approvals",
    "work_reviews",
    "legacy_mappings",
    "reconciliation_anomalies",
}
WORK_ORDER_SUPPORT_COLUMNS = {
    "tenant_id",
    "workspace_id",
    "created_by",
    "updated_by",
    "visibility",
    "canonical_state",
    "row_version",
    "parallel_attempts_allowed",
    "max_attempts",
    "canonicalized_at",
    "canonical_migration_batch_id",
    "legacy_status_snapshot",
    "terminal_at",
}


class RT2MigrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.harness = load_f0_env()

    def _config(self, database: Path) -> Config:
        configuration = Config(str(REPO_ROOT / "alembic.ini"))
        configuration.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
        return configuration

    def test_empty_database_upgrade_matches_foundation_models(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Path(temporary_directory) / "rt2-empty.db"
            command.upgrade(self._config(database), "head")
            engine = create_engine(f"sqlite:///{database}")
            try:
                database_inspector = inspect(engine)
                tables = set(database_inspector.get_table_names())
                self.assertTrue(RT2_TABLES.issubset(tables))
                self.assertNotIn("work_orders", tables)
                for table_name, table in FoundationBase.metadata.tables.items():
                    migrated = {
                        column["name"]
                        for column in database_inspector.get_columns(table_name)
                    }
                    self.assertEqual(
                        {column.name for column in table.columns},
                        migrated,
                        table_name,
                    )
            finally:
                engine.dispose()

    def test_operational_copy_gets_nullable_support_columns_only(self) -> None:
        before = self.harness.build_source_manifest(OPERATIONAL_DB)
        with tempfile.TemporaryDirectory() as temporary_directory:
            copied = Path(temporary_directory) / "operational-copy.db"
            shutil.copy2(OPERATIONAL_DB, copied)
            config = self._config(copied)
            with sqlite3.connect(copied) as connection:
                before_rows = connection.execute(
                    "SELECT work_order_id, status FROM work_orders "
                    "ORDER BY work_order_id"
                ).fetchall()
            command.stamp(config, "0001_baseline")
            command.upgrade(config, "head")
            with sqlite3.connect(copied) as connection:
                columns = {
                    row[1]: row[3]
                    for row in connection.execute("PRAGMA table_info(work_orders)")
                }
                count = connection.execute(
                    "SELECT COUNT(*) FROM work_orders"
                ).fetchone()[0]
            self.assertTrue(WORK_ORDER_SUPPORT_COLUMNS.issubset(columns))
            self.assertTrue(
                all(columns[column] == 0 for column in WORK_ORDER_SUPPORT_COLUMNS)
            )
            self.assertEqual(497, count)

            command.downgrade(config, "0002_identity_scope_audit")
            with sqlite3.connect(copied) as connection:
                downgraded_columns = {
                    row[1]
                    for row in connection.execute("PRAGMA table_info(work_orders)")
                }
                after_rows = connection.execute(
                    "SELECT work_order_id, status FROM work_orders "
                    "ORDER BY work_order_id"
                ).fetchall()
            self.assertTrue(
                WORK_ORDER_SUPPORT_COLUMNS.isdisjoint(downgraded_columns)
            )
            self.assertEqual(before_rows, after_rows)
        self.assertEqual(before, self.harness.build_source_manifest(OPERATIONAL_DB))

    def test_operational_database_remains_refused_at_head(self) -> None:
        before = self.harness.build_source_manifest(OPERATIONAL_DB)
        with self.assertRaisesRegex(Exception, "operational_db_bind_refused"):
            command.upgrade(self._config(OPERATIONAL_DB), "head")
        self.assertEqual(before, self.harness.build_source_manifest(OPERATIONAL_DB))

    def test_rt2_append_history_triggers_exist(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Path(temporary_directory) / "rt2-triggers.db"
            command.upgrade(self._config(database), "head")
            with sqlite3.connect(database) as connection:
                triggers = {
                    row[0]
                    for row in connection.execute(
                        "SELECT name FROM sqlite_master WHERE type='trigger'"
                    )
                }
            self.assertTrue(
                {
                    "promotion_records_no_update",
                    "promotion_records_no_delete",
                    "work_attempts_no_delete",
                    "work_attempts_terminal_no_update",
                    "work_approvals_no_delete",
                    "work_approvals_terminal_no_update",
                    "work_reviews_no_delete",
                    "work_reviews_terminal_no_update",
                    "legacy_mappings_no_update",
                    "legacy_mappings_no_delete",
                }.issubset(triggers)
            )

    def test_terminal_records_reject_rewrite_on_migrated_database(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Path(temporary_directory) / "rt2-immutable.db"
            command.upgrade(self._config(database), "head")
            with sqlite3.connect(database) as connection:
                connection.execute(
                    "INSERT INTO tenants "
                    "(tenant_id,name,slug,status,created_by,updated_by) "
                    "VALUES ('ten_test','Test','test','active','test','test')"
                )
                connection.execute(
                    "INSERT INTO workspaces "
                    "(workspace_id,tenant_id,name,slug,status,created_by,updated_by) "
                    "VALUES ('wsp_test','ten_test','Test','test','active','test','test')"
                )
                connection.execute(
                    "INSERT INTO work_attempts "
                    "(attempt_id,tenant_id,workspace_id,scope_key,work_order_id,"
                    "attempt_number,trigger_reason,state,row_version,"
                    "runtime_adapter_id,runtime_adapter_version,"
                    "runtime_config_snapshot_json,lease_generation,"
                    "invocation_authenticity_json,allowed_read_refs_json,"
                    "allowed_write_refs_json,created_by) "
                    "VALUES ('att_test','ten_test','wsp_test','ten_test:wsp_test',"
                    "'wo_test',1,'initial','succeeded',1,'local_script','p0',"
                    "'{}',0,'{}','[]','[]','test')"
                )
                connection.commit()
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(
                        "UPDATE work_attempts SET state='failed' "
                        "WHERE attempt_id='att_test'"
                    )
                connection.rollback()
                with self.assertRaises(sqlite3.IntegrityError):
                    connection.execute(
                        "DELETE FROM work_attempts WHERE attempt_id='att_test'"
                    )


if __name__ == "__main__":
    unittest.main()
