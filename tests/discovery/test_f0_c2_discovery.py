from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

import yaml


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts/f0_c2_discovery.py"


def load_discovery():
    spec = importlib.util.spec_from_file_location("f0_c2_discovery", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load discovery module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class F0C2DiscoveryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.discovery = load_discovery()

    def _fixture(self, root: Path) -> tuple[Path, Path]:
        database = root / "fixture.db"
        queue = root / "queue"
        (queue / "done").mkdir(parents=True)
        (queue / "outbox").mkdir()
        schema = """
        CREATE TABLE work_orders (
            work_order_id TEXT PRIMARY KEY, status TEXT, approval_required INTEGER,
            approval_id TEXT, attempt_count INTEGER, assigned_agent TEXT,
            runtime_id TEXT, output_path TEXT, evidence_path TEXT, error TEXT,
            result_summary TEXT, artifacts_json TEXT, execution_log_json TEXT,
            created_at TEXT, assigned_at TEXT, completed_at TEXT,
            openclaw_dispatched_at TEXT, openclaw_claimed_at TEXT
        );
        CREATE TABLE tasks (id INTEGER PRIMARY KEY, status TEXT);
        CREATE TABLE task_pool (id INTEGER PRIMARY KEY, status TEXT);
        CREATE TABLE execution_requests (id INTEGER PRIMARY KEY, status TEXT);
        CREATE TABLE code_runtime_jobs (
            id INTEGER PRIMARY KEY, source_type TEXT, source_id TEXT, status TEXT
        );
        CREATE TABLE approvals (
            id INTEGER PRIMARY KEY, target_type TEXT, target_id TEXT, status TEXT
        );
        CREATE TABLE reviews (
            id INTEGER PRIMARY KEY, task_id INTEGER, result TEXT
        );
        CREATE TABLE artifacts (
            id TEXT PRIMARY KEY, run_id TEXT, artifact_status TEXT, data_source TEXT
        );
        CREATE TABLE execution_records (id TEXT PRIMARY KEY, result TEXT);
        CREATE TABLE asset_registry (id INTEGER PRIMARY KEY, status TEXT);
        CREATE TABLE runtime_registry (runtime_id TEXT PRIMARY KEY, status TEXT);
        """
        with sqlite3.connect(database) as connection:
            connection.executescript(schema)
            connection.executemany(
                """
                INSERT INTO work_orders VALUES
                (?, ?, 0, NULL, ?, ?, ?, ?, ?, ?, ?, NULL, NULL, ?, NULL, ?, NULL, NULL)
                """,
                [
                    (
                        "WO-COMPLETE-1",
                        "completed",
                        1,
                        "worker",
                        "local",
                        "output.txt",
                        "evidence.json",
                        None,
                        "legacy success",
                        "2026-01-01",
                        "2026-01-02",
                    ),
                    (
                        "WO-RUNNING-1",
                        "in_progress",
                        1,
                        None,
                        "openclaw",
                        None,
                        None,
                        None,
                        None,
                        "2026-01-01",
                        None,
                    ),
                    (
                        "WO-CREATED-1",
                        "created",
                        0,
                        None,
                        None,
                        None,
                        None,
                        None,
                        None,
                        "2026-01-01",
                        None,
                    ),
                ],
            )
            connection.execute("INSERT INTO tasks VALUES (1, 'completed')")
            connection.execute("INSERT INTO task_pool VALUES (1, 'review')")
            connection.execute("INSERT INTO execution_requests VALUES (1, 'verified_success')")
            connection.executemany(
                "INSERT INTO code_runtime_jobs VALUES (?, 'request', '29', ?)",
                [(1, "success"), (2, "running")],
            )
            connection.execute(
                "INSERT INTO approvals VALUES (1, 'task', '1', 'approved')"
            )
            connection.executemany(
                "INSERT INTO reviews VALUES (?, 1, ?)",
                [(1, "pass"), (2, "blocked")],
            )
            connection.execute(
                "INSERT INTO execution_records VALUES ('run-1', 'passed')"
            )
            connection.execute(
                "INSERT INTO artifacts VALUES ('artifact-1', 'run-1', 'validated', 'mock')"
            )
            connection.execute(
                "INSERT INTO runtime_registry VALUES ('local', 'available')"
            )
        (queue / "done/task.yaml").write_text(
            yaml.safe_dump(
                {
                    "work_id": "WQ-1",
                    "attempt_id": "WQ-1-A1",
                    "status": "waiting_review",
                }
            ),
            encoding="utf-8",
        )
        (queue / "outbox/result.json").write_text(
            json.dumps({"work_id": "WQ-1", "status": "done"}),
            encoding="utf-8",
        )
        return database, queue

    def test_completed_is_always_quarantined_not_done(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database, queue = self._fixture(Path(temporary_directory))
            report = self.discovery.build_report(
                database,
                queue,
                observed_at="2026-06-07T00:00:00.000000Z",
            )

        completed = report["systems"]["work_orders"][0]
        self.assertEqual("noncanonical_history", completed["classification"])
        self.assertEqual("waiting_review", completed["canonical_candidate_state"])
        self.assertEqual(
            "legacy_completed_review_required",
            completed["recommended_disposition"],
        )
        self.assertEqual(1, report["summary"]["legacy_completed_quarantine_count"])
        self.assertEqual(0, report["summary"]["legacy_completed_promoted_to_done_count"])

    def test_six_systems_and_conflicts_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database, queue = self._fixture(Path(temporary_directory))
            report = self.discovery.build_report(database, queue)

        self.assertEqual(
            set(self.discovery.SIX_SYSTEMS),
            set(report["summary"]["six_system_counts"]),
        )
        queue_task = next(
            record
            for record in report["systems"]["private_work_queue"]
            if record["relative_path"] == "done/task.yaml"
        )
        self.assertEqual("conflicting", queue_task["classification"])
        self.assertIn(
            "directory_state_conflicts_with_declared_status",
            queue_task["reason_codes"],
        )
        self.assertTrue(
            all(
                record["classification"] == "conflicting"
                for record in report["systems"]["code_runtime_jobs"]
            )
        )
        self.assertEqual(
            "conflicting",
            report["systems"]["task_pool"][0]["classification"],
        )

    def test_classification_hash_is_deterministic(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database, queue = self._fixture(Path(temporary_directory))
            first = self.discovery.build_report(
                database,
                queue,
                observed_at="2026-06-07T00:00:00.000000Z",
            )
            second = self.discovery.build_report(
                database,
                queue,
                observed_at="2026-06-08T00:00:00.000000Z",
            )

        self.assertEqual(first["classification_hash"], second["classification_hash"])
        self.assertEqual(
            first["source_manifest"]["combined_source_hash"],
            second["source_manifest"]["combined_source_hash"],
        )

    def test_source_change_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            database, queue = self._fixture(root)
            original = self.discovery.classify_private_queue

            def mutate_after_parse(queue_root):
                records = original(queue_root)
                (queue / "done/task.yaml").write_text("status: done\n", encoding="utf-8")
                return records

            self.discovery.classify_private_queue = mutate_after_parse
            try:
                with self.assertRaisesRegex(
                    self.discovery.SourceChanged,
                    "filesystem_queue_changed_during_discovery",
                ):
                    self.discovery.build_report(database, queue)
            finally:
                self.discovery.classify_private_queue = original

    def test_live_wal_or_shm_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            database, queue = self._fixture(root)
            Path(f"{database}-wal").write_bytes(b"uncheckpointed")
            with self.assertRaisesRegex(
                self.discovery.DiscoveryError,
                "live_sqlite_sidecars_require_separately_authorized_quiesced_copy",
            ):
                self.discovery.build_report(database, queue)

    def test_report_output_refuses_protected_trees(self) -> None:
        with self.assertRaises(self.discovery.ProtectedOutputRefused):
            self.discovery._assert_output_allowed(REPO_ROOT / "private/reports")
        with self.assertRaises(self.discovery.ProtectedOutputRefused):
            self.discovery._assert_output_allowed(REPO_ROOT / "backend/data/reports")

    def test_reports_write_only_to_explicit_output_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            database, queue = self._fixture(root)
            report = self.discovery.build_report(
                database,
                queue,
                observed_at="2026-06-07T00:00:00.000000Z",
            )
            output = root / "reports"
            targets = self.discovery.write_reports(report, output)

            self.assertEqual(
                {
                    "v0.47-F0-C2-source-manifest.json",
                    "v0.47-F0-C2-classification.json",
                    "v0.47-F0-C2-classification.md",
                },
                {path.name for path in targets},
            )
            self.assertTrue(all(path.parent == output.resolve() for path in targets))
            written_report = json.loads(
                (output / "v0.47-F0-C2-classification.json").read_text(
                    encoding="utf-8"
                )
            )
            self.assertEqual(
                report["classification_hash"],
                written_report["classification_hash"],
            )

    def test_filesystem_queue_symlink_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            database, queue = self._fixture(root)
            (queue / "done/escape.json").symlink_to(root / "outside.json")
            (root / "outside.json").write_text('{"status":"done"}', encoding="utf-8")
            with self.assertRaisesRegex(
                self.discovery.DiscoveryError,
                "filesystem_queue_symlink_refused",
            ):
                self.discovery.build_report(database, queue)

    def test_read_only_authorizer_rejects_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            database, _queue = self._fixture(Path(temporary_directory))
            with self.discovery.open_read_only_database(database) as connection:
                with self.assertRaises(sqlite3.DatabaseError):
                    connection.execute("UPDATE work_orders SET status='done'")


if __name__ == "__main__":
    unittest.main()
