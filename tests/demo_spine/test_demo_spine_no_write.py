from __future__ import annotations

import sqlite3
import sys
import unittest

from path_bootstrap import ensure_backend_path


ensure_backend_path()

from app.pilot.database import OPERATIONAL_DB_PATH, sha256_file  # noqa: E402
from app.pilot.demo_spine import DemoSpineStore  # noqa: E402


FORBIDDEN_IMPORTS = {
    "app.main",
    "app.database",
    "app.runtime.registry",
    "app.runtime.seed_runtimes",
    "app.services.work_order_executor",
}


class DemoSpineNoWriteTests(unittest.TestCase):
    def test_demo_spine_does_not_touch_operational_database(self) -> None:
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

        store = DemoSpineStore()
        run = store.create_run(
            "clip_matrix_agent",
            "Design a pilot clip matrix without touching operational data.",
        )
        for _ in range(20):
            current = store.get_run(run["demo_run_id"])
            if current["status"] == "ready_for_decision":
                break
            store.advance_run(run["demo_run_id"])
        store.decide_run(run["demo_run_id"], "no_go")

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

    def test_demo_spine_imports_no_startup_or_runtime_modules(self) -> None:
        for module_name in FORBIDDEN_IMPORTS:
            sys.modules.pop(module_name, None)

        __import__("app.pilot.demo_scenarios")
        __import__("app.pilot.demo_spine")

        self.assertEqual(set(), FORBIDDEN_IMPORTS.intersection(sys.modules))


if __name__ == "__main__":
    unittest.main()
