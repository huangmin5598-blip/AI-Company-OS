from __future__ import annotations

from pathlib import Path
import socket
import subprocess
import sys
import threading
import unittest
from unittest import mock
import urllib.request

from path_bootstrap import ensure_backend_path

ensure_backend_path()

from app.models.canonical_work_order import CanonicalReadBase
from app.services.canonical_work_order_read_service import project_legacy
from support import OPERATIONAL_DB, REPO_ROOT, load_f0_env, tree_manifest


class E1ANoWriteTests(unittest.TestCase):
    def test_imports_and_projection_preserve_protected_state(self) -> None:
        harness = load_f0_env()
        before_db = harness.build_source_manifest(OPERATIONAL_DB)
        before_data = tree_manifest(REPO_ROOT / "backend/data")
        before_private = tree_manifest(REPO_ROOT / "private")
        modules_before = set(sys.modules)

        with (
            mock.patch.object(threading.Thread, "start") as thread_start,
            mock.patch.object(subprocess, "Popen") as process_start,
            mock.patch.object(socket, "socket") as socket_start,
            mock.patch.object(urllib.request, "urlopen") as urlopen,
        ):
            self.assertIn("work_orders", CanonicalReadBase.metadata.tables)
            with self.assertRaisesRegex(ValueError, "invalid_mode_b_rt3_evidence"):
                project_legacy({}, {}, {})
            thread_start.assert_not_called()
            process_start.assert_not_called()
            socket_start.assert_not_called()
            urlopen.assert_not_called()

        forbidden_modules = {
            "app.main",
            "app.database",
            "app.runtime.registry",
            "app.runtime.seed_runtimes",
            "app.services.work_order_executor",
        }
        self.assertFalse(forbidden_modules.intersection(set(sys.modules) - modules_before))
        self.assertEqual(before_db, harness.build_source_manifest(OPERATIONAL_DB))
        self.assertEqual(before_data, tree_manifest(REPO_ROOT / "backend/data"))
        self.assertEqual(before_private, tree_manifest(REPO_ROOT / "private"))


if __name__ == "__main__":
    unittest.main()
