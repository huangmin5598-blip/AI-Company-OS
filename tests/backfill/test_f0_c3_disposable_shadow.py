from __future__ import annotations

from alembic import command
from alembic.config import Config
import importlib.util
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts/f0_c3_backfill_dry_run.py"
OPERATIONAL_DB = REPO_ROOT / "backend/data/ai_company_os.db"
QUEUE_ROOT = REPO_ROOT / "private/work-queue"
CLASSIFICATION_REPORT = (
    REPO_ROOT / "reports/migration/v0.47-F0-C2-classification.json"
)


def load_planner():
    spec = importlib.util.spec_from_file_location("f0_c3_shadow", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load F0-C3 planner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class F0C3DisposableShadowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.planner = load_planner()
        cls.plan = cls.planner.build_plan(
            OPERATIONAL_DB,
            QUEUE_ROOT,
            CLASSIFICATION_REPORT,
            observed_at="2026-06-07T00:00:00.000000Z",
        )

    def test_shadow_backfill_simulation_rolls_back_on_disposable_copy(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            copy_path = Path(temporary_directory) / "operational-copy.db"
            shutil.copy2(OPERATIONAL_DB, copy_path)
            configuration = Config(str(REPO_ROOT / "alembic.ini"))
            configuration.set_main_option("script_location", str(REPO_ROOT / "alembic"))
            configuration.set_main_option("sqlalchemy.url", f"sqlite:///{copy_path}")
            command.upgrade(configuration, "head")

            connection = sqlite3.connect(copy_path)
            try:
                connection.execute("PRAGMA foreign_keys=ON")
                connection.execute("BEGIN")
                roots = {
                    root["object_type"]: root
                    for root in self.plan["default_root_records"]
                }
                tenant = roots["Tenant"]
                connection.execute(
                    """
                    INSERT INTO tenants
                    (tenant_id, name, slug, status, created_by, updated_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        tenant["object_id"],
                        tenant["fields"]["name"],
                        tenant["fields"]["slug"],
                        tenant["fields"]["status"],
                        tenant["fields"]["created_by"],
                        tenant["fields"]["updated_by"],
                    ),
                )
                workspace = roots["Workspace"]
                connection.execute(
                    """
                    INSERT INTO workspaces
                    (workspace_id, tenant_id, name, slug, status, created_by, updated_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        workspace["object_id"],
                        workspace["fields"]["tenant_id"],
                        workspace["fields"]["name"],
                        workspace["fields"]["slug"],
                        workspace["fields"]["status"],
                        workspace["fields"]["created_by"],
                        workspace["fields"]["updated_by"],
                    ),
                )
                user = roots["User"]
                connection.execute(
                    """
                    INSERT INTO users
                    (user_id, principal_name, display_name, status)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        user["object_id"],
                        user["fields"]["principal_name"],
                        user["fields"]["display_name"],
                        user["fields"]["status"],
                    ),
                )
                membership = roots["Membership"]
                connection.execute(
                    """
                    INSERT INTO memberships
                    (membership_id, tenant_id, workspace_id, user_id, scope_key, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        membership["object_id"],
                        membership["fields"]["tenant_id"],
                        membership["fields"]["workspace_id"],
                        membership["fields"]["user_id"],
                        membership["fields"]["scope_key"],
                        membership["fields"]["status"],
                    ),
                )
                batch = self.plan["migration_batch"]
                connection.execute(
                    """
                    INSERT INTO migration_batches
                    (migration_batch_id, source_manifest_hash, ruleset_version,
                     mode, status, counts_json, report_ref, created_by)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        batch["migration_batch_id"],
                        batch["source_manifest_hash"],
                        batch["ruleset_version"],
                        batch["mode"],
                        batch["status"],
                        json.dumps(self.plan["summary"], sort_keys=True),
                        "reports/migration/v0.47-F0-C3-backfill-dry-run.json",
                        batch["created_by"],
                    ),
                )
                for mapping in self.plan["work_order_mappings"]:
                    connection.execute(
                        """
                        INSERT INTO legacy_mappings
                        (legacy_mapping_id, source_system, source_type, source_key,
                         source_state, source_hash, canonical_object_type,
                         canonical_object_id, classification, mapping_rule,
                         migration_batch_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            mapping["legacy_mapping_id"],
                            mapping["source_system"],
                            mapping["source_type"],
                            mapping["source_key"],
                            mapping["source_state"],
                            mapping["source_hash"],
                            mapping["canonical_object_type"],
                            mapping["canonical_object_id"],
                            mapping["classification"],
                            mapping["mapping_rule"],
                            mapping["migration_batch_id"],
                        ),
                    )
                    fields = mapping["proposed_fields"]
                    connection.execute(
                        """
                        UPDATE work_orders
                        SET tenant_id=?, workspace_id=?, created_by=?, updated_by=?,
                            visibility=?, canonical_state=?, row_version=?,
                            parallel_attempts_allowed=?, max_attempts=?,
                            canonicalized_at=?, canonical_migration_batch_id=?,
                            legacy_status_snapshot=?, terminal_at=?
                        WHERE work_order_id=?
                        """,
                        (
                            fields["tenant_id"],
                            fields["workspace_id"],
                            fields["created_by"],
                            fields["updated_by"],
                            fields["visibility"],
                            fields["canonical_state"],
                            fields["row_version"],
                            fields["parallel_attempts_allowed"],
                            fields["max_attempts"],
                            fields["canonicalized_at"],
                            fields["canonical_migration_batch_id"],
                            fields["legacy_status_snapshot"],
                            fields["terminal_at"],
                            mapping["source_key"],
                        ),
                    )
                for anomaly in self.plan["reconciliation_anomalies"]:
                    connection.execute(
                        """
                        INSERT INTO reconciliation_anomalies
                        (anomaly_id, migration_batch_id, tenant_id, workspace_id,
                         source_system, source_type, source_key, anomaly_type,
                         severity, details_json, status)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            anomaly["anomaly_id"],
                            anomaly["migration_batch_id"],
                            anomaly["tenant_id"],
                            anomaly["workspace_id"],
                            anomaly["source_system"],
                            anomaly["source_type"],
                            anomaly["source_key"],
                            anomaly["anomaly_type"],
                            anomaly["severity"],
                            json.dumps(anomaly["details"], sort_keys=True),
                            anomaly["status"],
                        ),
                    )

                self.assertEqual(
                    497,
                    connection.execute(
                        "SELECT COUNT(*) FROM legacy_mappings"
                    ).fetchone()[0],
                )
                self.assertEqual(
                    438,
                    connection.execute(
                        "SELECT COUNT(*) FROM reconciliation_anomalies"
                    ).fetchone()[0],
                )
                self.assertEqual(
                    497,
                    connection.execute(
                        """
                        SELECT COUNT(*) FROM work_orders
                        WHERE tenant_id='ten_local'
                          AND workspace_id='wsp_personal'
                          AND row_version=1
                          AND parallel_attempts_allowed=0
                          AND legacy_status_snapshot=status
                        """
                    ).fetchone()[0],
                )
                self.assertEqual(
                    168,
                    connection.execute(
                        """
                        SELECT COUNT(*) FROM work_orders
                        WHERE status='completed'
                          AND canonical_state='waiting_review'
                        """
                    ).fetchone()[0],
                )
                self.assertEqual(
                    0,
                    connection.execute(
                        "SELECT COUNT(*) FROM work_orders WHERE canonical_state='done'"
                    ).fetchone()[0],
                )
                self.assertEqual(
                    263,
                    connection.execute(
                        "SELECT COUNT(*) FROM work_orders WHERE canonical_state IS NULL"
                    ).fetchone()[0],
                )
                connection.rollback()
                self.assertEqual(
                    0,
                    connection.execute(
                        "SELECT COUNT(*) FROM legacy_mappings"
                    ).fetchone()[0],
                )
                self.assertEqual(
                    497,
                    connection.execute(
                        "SELECT COUNT(*) FROM work_orders WHERE tenant_id IS NULL"
                    ).fetchone()[0],
                )
            finally:
                connection.close()


if __name__ == "__main__":
    unittest.main()
