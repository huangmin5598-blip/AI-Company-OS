from __future__ import annotations

import sqlite3
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from path_bootstrap import ensure_backend_path


ensure_backend_path()

from app.pilot.bootstrap import bootstrap_pilot_database  # noqa: E402
from app.pilot.database import (  # noqa: E402
    OPERATIONAL_DB_PATH,
    PILOT_AUTHORITY,
    PILOT_DB_PATH,
    PilotBoundaryViolation,
    PilotDatabase,
    assert_fixed_pilot_path,
    sha256_file,
)


class Phase3PilotBoundaryTests(unittest.TestCase):
    def test_bootstrap_creates_marker_and_only_empty_legacy_surfaces(self) -> None:
        operational_before = sha256_file(OPERATIONAL_DB_PATH)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "vs001-pilot.db"
            database = PilotDatabase.for_disposable_test(path)
            try:
                bootstrap_pilot_database(database)
                with database.command_session() as session:
                    marker = session.execute(
                        __import__("sqlalchemy").text(
                            "SELECT authority FROM pilot_marker"
                        )
                    ).scalar_one()
                    self.assertEqual(PILOT_AUTHORITY, marker)
                    self.assertEqual(
                        0,
                        session.execute(
                            __import__("sqlalchemy").text(
                                "SELECT COUNT(*) FROM work_orders"
                            )
                        ).scalar_one(),
                    )
                    self.assertEqual(
                        1,
                        session.execute(
                            __import__("sqlalchemy").text(
                                "SELECT COUNT(*) FROM runtime_registry"
                            )
                        ).scalar_one(),
                    )
            finally:
                database.dispose()
        self.assertEqual(operational_before, sha256_file(OPERATIONAL_DB_PATH))

    def test_marker_missing_or_changed_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "vs001-pilot.db"
            database = PilotDatabase.for_disposable_test(path)
            try:
                bootstrap_pilot_database(database)
                with sqlite3.connect(path) as connection:
                    connection.execute(
                        "UPDATE pilot_marker SET authority='operational'"
                    )
                    connection.commit()
                with self.assertRaisesRegex(
                    PilotBoundaryViolation,
                    "pilot_marker_authority_invalid",
                ):
                    with database.command_session():
                        pass
            finally:
                database.dispose()

    def test_attach_and_detach_are_physically_denied(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "vs001-pilot.db"
            database = PilotDatabase.for_disposable_test(path)
            try:
                bootstrap_pilot_database(database)
                with database.command_session() as session:
                    with self.assertRaises(Exception):
                        session.execute(
                            __import__("sqlalchemy").text(
                                "ATTACH DATABASE ':memory:' AS operational"
                            )
                        )
            finally:
                database.dispose()

    def test_production_path_is_fixed_and_aliases_are_rejected(self) -> None:
        self.assertEqual(PILOT_DB_PATH, assert_fixed_pilot_path(PILOT_DB_PATH))
        with self.assertRaisesRegex(
            PilotBoundaryViolation,
            "pilot_database_path_not_authorized",
        ):
            assert_fixed_pilot_path(
                PILOT_DB_PATH.parent / "../other/vs001-pilot.db"
            )
        with tempfile.TemporaryDirectory() as temporary:
            alias = Path(temporary) / "vs001-pilot.db"
            alias.symlink_to(OPERATIONAL_DB_PATH)
            with self.assertRaisesRegex(
                PilotBoundaryViolation,
                "test_pilot_symlink_forbidden",
            ):
                PilotDatabase.for_disposable_test(alias)

    def test_import_guard_rejects_forbidden_startup_modules(self) -> None:
        code = """
import sys, types
sys.modules['app.database'] = types.ModuleType('app.database')
import app.pilot
"""
        completed = subprocess.run(
            [sys.executable, "-c", code],
            cwd=Path(__file__).resolve().parents[2],
            env={
                "PYTHONPATH": "backend",
                "PATH": __import__("os").environ.get("PATH", ""),
            },
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertNotEqual(0, completed.returncode)
        self.assertIn(
            "pilot_forbidden_startup_module_loaded:app.database",
            completed.stderr,
        )


if __name__ == "__main__":
    unittest.main()
