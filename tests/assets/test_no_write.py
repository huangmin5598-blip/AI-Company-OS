from __future__ import annotations

import sqlite3
from pathlib import Path
import tempfile
import unittest

from path_bootstrap import ensure_backend_path


ensure_backend_path()

from app.pilot.bootstrap import bootstrap_pilot_database  # noqa: E402
from app.pilot.database import OPERATIONAL_DB_PATH, PilotDatabase, sha256_file  # noqa: E402
from app.pilot.database import PilotBoundaryViolation  # noqa: E402
from app.pilot.gateway import PilotCommandGateway  # noqa: E402


class Vs002NoWriteTests(unittest.TestCase):
    def test_asset_schema_component_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "vs001-pilot.db"
            database = PilotDatabase.for_disposable_test(path)
            try:
                bootstrap_pilot_database(database)
                with sqlite3.connect(path) as connection:
                    connection.execute(
                        "UPDATE pilot_schema_components SET version='tampered'"
                        " WHERE component='assets'"
                    )
                    connection.commit()
                with self.assertRaisesRegex(
                    PilotBoundaryViolation,
                    "pilot_asset_schema_version_invalid",
                ):
                    with database.command_session():
                        pass
            finally:
                database.dispose()

    def test_assets_flow_never_stamps_or_writes_operational_database(self) -> None:
        before = sha256_file(OPERATIONAL_DB_PATH)
        with sqlite3.connect(
            f"{OPERATIONAL_DB_PATH.as_uri()}?mode=ro&immutable=1",
            uri=True,
        ) as connection:
            before_counts = (
                connection.execute("SELECT COUNT(*) FROM work_orders").fetchone()[0],
                connection.execute(
                    "SELECT COUNT(*) FROM work_orders WHERE status='completed'"
                ).fetchone()[0],
                connection.execute(
                    "SELECT COUNT(*) FROM runtime_registry"
                ).fetchone()[0],
            )
        with tempfile.TemporaryDirectory() as temporary:
            database = PilotDatabase.for_disposable_test(
                Path(temporary) / "vs001-pilot.db"
            )
            try:
                bootstrap_pilot_database(database)
                gateway = PilotCommandGateway(database)
                with gateway.database.command_session() as session:
                    self.assertEqual(
                        "pilot_non_authoritative",
                        session.execute(
                            __import__("sqlalchemy").text(
                                "SELECT authority FROM pilot_marker"
                            )
                        ).scalar_one(),
                    )
            finally:
                database.dispose()
        self.assertEqual(before, sha256_file(OPERATIONAL_DB_PATH))
        with sqlite3.connect(
            f"{OPERATIONAL_DB_PATH.as_uri()}?mode=ro&immutable=1",
            uri=True,
        ) as connection:
            self.assertEqual(
                0,
                connection.execute(
                    "SELECT COUNT(*) FROM sqlite_master"
                    " WHERE type='table' AND name='alembic_version'"
                ).fetchone()[0],
            )
            self.assertEqual(
                before_counts,
                (
                    connection.execute(
                        "SELECT COUNT(*) FROM work_orders"
                    ).fetchone()[0],
                    connection.execute(
                        "SELECT COUNT(*) FROM work_orders"
                        " WHERE status='completed'"
                    ).fetchone()[0],
                    connection.execute(
                        "SELECT COUNT(*) FROM runtime_registry"
                    ).fetchone()[0],
                ),
            )


if __name__ == "__main__":
    unittest.main()
