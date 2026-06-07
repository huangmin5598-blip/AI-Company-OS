from __future__ import annotations

from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock

from app.models.base import Base
from app.models.foundation_audit import AuditEvent  # noqa: F401
from app.models.foundation_identity import Tenant  # noqa: F401
from support import (
    make_sqlite_session,
    protected_snapshot,
)


class RT1NoWriteTests(unittest.TestCase):
    def test_foundation_imports_and_disposable_schema_preserve_protected_state(self) -> None:
        before = protected_snapshot()
        modules_before = set(sys.modules)
        with tempfile.TemporaryDirectory() as temporary_directory:
            database = Path(temporary_directory) / "disposable.db"
            engine, session = make_sqlite_session(database)
            try:
                Base.metadata.create_all(engine)
                self.assertGreater(
                    len(
                        sqlite3.connect(database)
                        .execute(
                            "SELECT name FROM sqlite_master WHERE type='table'"
                        )
                        .fetchall()
                    ),
                    0,
                )
            finally:
                session.close()
                engine.dispose()

        forbidden_modules = {
            "app.main",
            "app.database",
            "app.runtime.registry",
            "app.runtime.seed_runtimes",
            "app.services.work_order_executor",
        }
        self.assertFalse(forbidden_modules.intersection(set(sys.modules) - modules_before))
        self.assertEqual(before, protected_snapshot())

    def test_foundation_path_attempts_no_runtime_network_thread_or_subprocess(self) -> None:
        before = protected_snapshot()
        with (
            mock.patch("threading.Thread.start") as thread_start,
            mock.patch("subprocess.Popen") as process_start,
            mock.patch("socket.socket") as socket_start,
            mock.patch("urllib.request.urlopen") as urlopen,
        ):
            with tempfile.TemporaryDirectory() as temporary_directory:
                database = Path(temporary_directory) / "guarded.db"
                engine, session = make_sqlite_session(database)
                try:
                    Base.metadata.create_all(engine)
                finally:
                    session.close()
                    engine.dispose()

            thread_start.assert_not_called()
            process_start.assert_not_called()
            socket_start.assert_not_called()
            urlopen.assert_not_called()

        self.assertEqual(before, protected_snapshot())


if __name__ == "__main__":
    unittest.main()
