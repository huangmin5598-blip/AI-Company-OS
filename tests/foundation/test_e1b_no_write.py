from __future__ import annotations

import socket
import subprocess
import threading
import unittest
from unittest import mock
import urllib.request

from path_bootstrap import ensure_backend_path

ensure_backend_path()

from app.services.canonical_execution_service import BUILTIN_RUNTIME_ID
from support import OPERATIONAL_DB, REPO_ROOT, load_f0_env, tree_manifest


class E1BNoWriteTests(unittest.TestCase):
    def test_phase2a_imports_preserve_protected_state_and_do_not_execute(self) -> None:
        harness = load_f0_env()
        before_db = harness.build_source_manifest(OPERATIONAL_DB)
        before_data = tree_manifest(REPO_ROOT / "backend/data")
        before_private = tree_manifest(REPO_ROOT / "private")

        with (
            mock.patch.object(threading.Thread, "start") as thread_start,
            mock.patch.object(subprocess, "Popen") as process_start,
            mock.patch.object(socket, "socket") as socket_start,
            mock.patch.object(urllib.request, "urlopen") as urlopen,
        ):
            self.assertEqual(
                "builtin.vs001_echo_markdown",
                BUILTIN_RUNTIME_ID,
            )
            thread_start.assert_not_called()
            process_start.assert_not_called()
            socket_start.assert_not_called()
            urlopen.assert_not_called()

        self.assertEqual(before_db, harness.build_source_manifest(OPERATIONAL_DB))
        self.assertEqual(before_data, tree_manifest(REPO_ROOT / "backend/data"))
        self.assertEqual(before_private, tree_manifest(REPO_ROOT / "private"))


if __name__ == "__main__":
    unittest.main()
