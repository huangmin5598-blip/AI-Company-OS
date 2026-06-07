from __future__ import annotations

import hashlib
import importlib.util
from pathlib import Path
import socket
import subprocess
import sys
import threading
import unittest
from unittest import mock
import urllib.request


REPO_ROOT = Path(__file__).resolve().parents[2]
OPERATIONAL_DB = REPO_ROOT / "backend/data/ai_company_os.db"
QUEUE_ROOT = REPO_ROOT / "private/work-queue"
PRIVATE_ROOT = REPO_ROOT / "private"
BACKEND_DATA_ROOT = REPO_ROOT / "backend/data"
MODULE_PATH = REPO_ROOT / "scripts/f0_c2_discovery.py"


def load_discovery():
    spec = importlib.util.spec_from_file_location("f0_c2_no_write", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("Unable to load discovery module")
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


class F0C2NoWriteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.discovery = load_discovery()

    def test_operational_discovery_preserves_database_and_private_queue(self) -> None:
        database_before = self.discovery.database_source_manifest(OPERATIONAL_DB)
        backend_data_before = tree_manifest(BACKEND_DATA_ROOT)
        private_before = tree_manifest(PRIVATE_ROOT)
        modules_before = set(sys.modules)
        with (
            mock.patch.object(threading.Thread, "start") as thread_start,
            mock.patch.object(subprocess, "Popen") as process_start,
            mock.patch.object(socket, "socket") as socket_start,
            mock.patch.object(urllib.request, "urlopen") as urlopen,
        ):
            report = self.discovery.build_report(
                OPERATIONAL_DB,
                QUEUE_ROOT,
                observed_at="2026-06-07T00:00:00.000000Z",
            )
            thread_start.assert_not_called()
            process_start.assert_not_called()
            socket_start.assert_not_called()
            urlopen.assert_not_called()

        self.assertEqual(database_before, self.discovery.database_source_manifest(OPERATIONAL_DB))
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
        self.assertEqual(497, report["summary"]["six_system_counts"]["work_orders"])
        self.assertEqual(168, report["summary"]["legacy_completed_count"])
        self.assertEqual(168, report["summary"]["legacy_completed_quarantine_count"])
        self.assertEqual(0, report["summary"]["source_rows_rewritten"])
        self.assertEqual(0, report["summary"]["legacy_completed_promoted_to_done_count"])


if __name__ == "__main__":
    unittest.main()
