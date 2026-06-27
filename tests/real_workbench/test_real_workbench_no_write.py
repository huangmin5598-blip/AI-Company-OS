from __future__ import annotations

import sqlite3
import sys
from pathlib import Path
import tempfile
import unittest

from path_bootstrap import ensure_backend_path


ensure_backend_path()

from app.pilot.bootstrap import bootstrap_pilot_database  # noqa: E402
from app.pilot.database import OPERATIONAL_DB_PATH, PilotDatabase, sha256_file  # noqa: E402
from app.pilot.real_workbench import RealWorkbenchStore  # noqa: E402


FORBIDDEN_IMPORTS = {
    "app.main",
    "app.database",
    "app.runtime.registry",
    "app.runtime.seed_runtimes",
    "app.services.work_order_executor",
}


class RealWorkbenchNoWriteTests(unittest.TestCase):
    def test_real_workbench_does_not_touch_operational_database(self) -> None:
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
                connection.execute(
                    "SELECT COUNT(*) FROM sqlite_master"
                    " WHERE type='table' AND name='alembic_version'"
                ).fetchone()[0],
            )

        with tempfile.TemporaryDirectory() as temporary:
            database = PilotDatabase.for_disposable_test(
                Path(temporary) / "vs001-pilot.db"
            )
            try:
                bootstrap_pilot_database(database)
                with database.command_session() as session:
                    store = RealWorkbenchStore(session)
                    run = store.create_run(
                        "idea_to_prd_pilot",
                        "Prepare a persistent real workbench run.",
                    )
                    store.assign_task(
                        run["run_id"],
                        run["task_plan"][0]["task_id"],
                        "codex_slot",
                        "Manual pilot dispatch only.",
                    )
                    store.list_runs()
            finally:
                database.dispose()

        self.assertEqual(before, sha256_file(OPERATIONAL_DB_PATH))
        with sqlite3.connect(
            f"{OPERATIONAL_DB_PATH.as_uri()}?mode=ro&immutable=1",
            uri=True,
        ) as connection:
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
                    connection.execute(
                        "SELECT COUNT(*) FROM sqlite_master"
                        " WHERE type='table' AND name='alembic_version'"
                    ).fetchone()[0],
                ),
            )

    def test_real_workbench_imports_no_startup_or_runtime_modules(self) -> None:
        for module_name in FORBIDDEN_IMPORTS:
            sys.modules.pop(module_name, None)

        __import__("app.pilot.real_workbench")

        self.assertEqual(set(), FORBIDDEN_IMPORTS.intersection(sys.modules))


if __name__ == "__main__":
    unittest.main()
