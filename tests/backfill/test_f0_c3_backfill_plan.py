from __future__ import annotations

import importlib.util
import json
from pathlib import Path
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
    spec = importlib.util.spec_from_file_location("f0_c3_planner", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load F0-C3 planner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class F0C3BackfillPlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.planner = load_planner()
        cls.plan = cls.planner.build_plan(
            OPERATIONAL_DB,
            QUEUE_ROOT,
            CLASSIFICATION_REPORT,
            observed_at="2026-06-07T00:00:00.000000Z",
        )

    def test_count_conservation_and_default_scope(self) -> None:
        summary = self.plan["summary"]
        self.assertEqual(497, summary["source_work_order_count"])
        self.assertEqual(497, summary["planned_work_order_mapping_count"])
        self.assertEqual(497, summary["scope_backfill_count"])
        self.assertEqual(0, summary["tenant_null_after_proposed_backfill"])
        self.assertEqual(0, summary["workspace_null_after_proposed_backfill"])
        self.assertEqual(0, summary["cross_tenant_candidate_count"])
        self.assertTrue(
            all(
                mapping["scope_plan"]
                == {
                    "tenant_id": "ten_local",
                    "workspace_id": "wsp_personal",
                    "scope_key": "ten_local:wsp_personal",
                }
                for mapping in self.plan["work_order_mappings"]
            )
        )

    def test_all_legacy_completed_are_quarantined(self) -> None:
        completed = [
            mapping
            for mapping in self.plan["work_order_mappings"]
            if mapping["source_state"] == "completed"
        ]
        self.assertEqual(168, len(completed))
        self.assertTrue(
            all(
                mapping["proposed_fields"]["canonical_state"] == "waiting_review"
                and mapping["quarantine_reason"]
                == "legacy_completed_review_required"
                for mapping in completed
            )
        )
        self.assertEqual(
            0,
            self.plan["summary"]["direct_canonical_done_count"],
        )

    def test_unresolved_legacy_execution_states_are_not_inferred(self) -> None:
        unresolved = [
            mapping
            for mapping in self.plan["work_order_mappings"]
            if mapping["source_state"] in {"routed", "assigned", "in_progress"}
        ]
        self.assertEqual(263, len(unresolved))
        self.assertTrue(
            all(
                mapping["proposed_fields"]["canonical_state"] is None
                for mapping in unresolved
            )
        )
        unresolved_anomalies = [
            anomaly
            for anomaly in self.plan["reconciliation_anomalies"]
            if anomaly["anomaly_type"] == "canonical_state_unresolved"
        ]
        self.assertEqual(263, len(unresolved_anomalies))

    def test_plan_is_deterministic_and_bound_to_rt3(self) -> None:
        second = self.planner.build_plan(
            OPERATIONAL_DB,
            QUEUE_ROOT,
            CLASSIFICATION_REPORT,
            observed_at="2026-06-08T00:00:00.000000Z",
        )
        self.assertEqual(self.plan["plan_hash"], second["plan_hash"])
        self.assertEqual(
            self.plan["migration_batch"]["migration_batch_id"],
            second["migration_batch"]["migration_batch_id"],
        )
        accepted = json.loads(CLASSIFICATION_REPORT.read_text(encoding="utf-8"))
        self.assertEqual(
            accepted["classification_hash"],
            self.plan["source_binding"]["classification_hash"],
        )

    def test_tampered_classification_report_fails_closed(self) -> None:
        accepted = json.loads(CLASSIFICATION_REPORT.read_text(encoding="utf-8"))
        accepted["classification_hash"] = "sha256:" + ("0" * 64)
        with tempfile.TemporaryDirectory() as temporary_directory:
            report = Path(temporary_directory) / "tampered.json"
            report.write_text(json.dumps(accepted), encoding="utf-8")
            with self.assertRaisesRegex(
                self.planner.ClassificationReportMismatch,
                "classification_hash_mismatch",
            ):
                self.planner.build_plan(
                    OPERATIONAL_DB,
                    QUEUE_ROOT,
                    report,
                )

    def test_report_output_is_explicit_and_protected_paths_are_refused(self) -> None:
        with self.assertRaises(self.planner.ProtectedOutputRefused):
            self.planner.write_reports(self.plan, REPO_ROOT / "private/rt4")
        with self.assertRaises(self.planner.ProtectedOutputRefused):
            self.planner.write_reports(
                self.plan,
                REPO_ROOT / "backend/data/rt4",
            )
        with tempfile.TemporaryDirectory() as temporary_directory:
            output = Path(temporary_directory) / "reports"
            targets = self.planner.write_reports(self.plan, output)
            self.assertEqual(
                {
                    "v0.47-F0-C3-backfill-dry-run.json",
                    "v0.47-F0-C3-backfill-dry-run.md",
                    "v0.47-F0-C3-rollback-preview.json",
                },
                {path.name for path in targets},
            )

    def test_disposable_constraint_simulation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Path(temporary_directory) / "simulation.db"
            with sqlite3.connect(database) as connection:
                connection.executescript(
                    """
                    CREATE TABLE proposed_roots (
                        object_type TEXT NOT NULL,
                        object_id TEXT PRIMARY KEY,
                        tenant_id TEXT,
                        workspace_id TEXT
                    );
                    CREATE TABLE proposed_mappings (
                        mapping_id TEXT PRIMARY KEY,
                        source_key TEXT NOT NULL UNIQUE,
                        tenant_id TEXT NOT NULL,
                        workspace_id TEXT NOT NULL,
                        canonical_state TEXT,
                        CHECK (canonical_state IS NULL OR canonical_state IN (
                            'draft','blocked','waiting_review'
                        ))
                    );
                    CREATE TABLE proposed_anomalies (
                        anomaly_id TEXT PRIMARY KEY,
                        source_key TEXT NOT NULL,
                        status TEXT NOT NULL CHECK (status = 'open')
                    );
                    """
                )
                for root in self.plan["default_root_records"]:
                    fields = root["fields"]
                    connection.execute(
                        "INSERT INTO proposed_roots VALUES (?, ?, ?, ?)",
                        (
                            root["object_type"],
                            root["object_id"],
                            fields.get("tenant_id"),
                            fields.get("workspace_id"),
                        ),
                    )
                for mapping in self.plan["work_order_mappings"]:
                    connection.execute(
                        "INSERT INTO proposed_mappings VALUES (?, ?, ?, ?, ?)",
                        (
                            mapping["legacy_mapping_id"],
                            mapping["source_key"],
                            mapping["scope_plan"]["tenant_id"],
                            mapping["scope_plan"]["workspace_id"],
                            mapping["proposed_fields"]["canonical_state"],
                        ),
                    )
                for anomaly in self.plan["reconciliation_anomalies"]:
                    connection.execute(
                        "INSERT INTO proposed_anomalies VALUES (?, ?, ?)",
                        (
                            anomaly["anomaly_id"],
                            anomaly["source_key"],
                            anomaly["status"],
                        ),
                    )
                self.assertEqual(
                    497,
                    connection.execute(
                        "SELECT COUNT(*) FROM proposed_mappings"
                    ).fetchone()[0],
                )
                self.assertEqual(
                    0,
                    connection.execute(
                        """
                        SELECT COUNT(*) FROM proposed_mappings
                        WHERE tenant_id != 'ten_local'
                           OR workspace_id != 'wsp_personal'
                        """
                    ).fetchone()[0],
                )
                connection.rollback()


if __name__ == "__main__":
    unittest.main()
