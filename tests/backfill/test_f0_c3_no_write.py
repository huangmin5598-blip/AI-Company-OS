from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest import mock
import urllib.request


REPO_ROOT = Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts/f0_c3_backfill_dry_run.py"
OPERATIONAL_DB = REPO_ROOT / "backend/data/ai_company_os.db"
QUEUE_ROOT = REPO_ROOT / "private/work-queue"
CLASSIFICATION_REPORT = (
    REPO_ROOT / "reports/migration/v0.47-F0-C2-classification.json"
)
PRIVATE_ROOT = REPO_ROOT / "private"
BACKEND_DATA_ROOT = REPO_ROOT / "backend/data"


def load_planner():
    spec = importlib.util.spec_from_file_location("f0_c3_no_write", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load F0-C3 planner")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_manifest(root: Path) -> list[tuple[str, int, int, str]]:
    return [
        (
            path.relative_to(root).as_posix(),
            path.stat().st_size,
            path.stat().st_mtime_ns,
            sha256_file(path),
        )
        for path in sorted(root.rglob("*"), key=lambda item: item.as_posix())
        if path.is_file()
    ]


class F0C3NoWriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.planner = load_planner()

    def test_operational_dry_run_preserves_all_protected_state(self) -> None:
        database_before = sha256_file(OPERATIONAL_DB)
        backend_data_before = tree_manifest(BACKEND_DATA_ROOT)
        private_before = tree_manifest(PRIVATE_ROOT)
        modules_before = set(sys.modules)
        with (
            mock.patch.object(threading.Thread, "start") as thread_start,
            mock.patch.object(subprocess, "Popen") as process_start,
            mock.patch.object(socket, "socket") as socket_start,
            mock.patch.object(urllib.request, "urlopen") as urlopen,
            tempfile.TemporaryDirectory() as temporary_directory,
        ):
            plan = self.planner.build_plan(
                OPERATIONAL_DB,
                QUEUE_ROOT,
                CLASSIFICATION_REPORT,
                observed_at="2026-06-07T00:00:00.000000Z",
            )
            self.planner.write_reports(
                plan,
                Path(temporary_directory) / "reports",
            )
            thread_start.assert_not_called()
            process_start.assert_not_called()
            socket_start.assert_not_called()
            urlopen.assert_not_called()

        self.assertEqual(database_before, sha256_file(OPERATIONAL_DB))
        self.assertEqual(backend_data_before, tree_manifest(BACKEND_DATA_ROOT))
        self.assertEqual(private_before, tree_manifest(PRIVATE_ROOT))
        forbidden_modules = {
            "app.main",
            "app.database",
            "app.runtime.registry",
            "app.runtime.seed_runtimes",
            "app.services.work_order_executor",
        }
        self.assertFalse(forbidden_modules.intersection(set(sys.modules) - modules_before))
        self.assertEqual(0, plan["summary"]["source_rows_rewritten"])
        self.assertEqual(0, plan["summary"]["canonical_rows_inserted"])
        self.assertEqual(0, plan["summary"]["root_rows_inserted"])
        self.assertEqual(0, plan["summary"]["migration_rows_inserted"])


if __name__ == "__main__":
    unittest.main()
