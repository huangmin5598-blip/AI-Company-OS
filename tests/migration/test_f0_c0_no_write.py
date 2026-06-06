from __future__ import annotations

from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest

from conftest import (
    REPO_ROOT,
    assert_no_backend_startup_imports,
    guarded_state_snapshot,
    load_f0_env,
    prohibited_activity_traps,
)


class NoWriteHarnessTests(unittest.TestCase):
    def test_harness_preserves_all_guarded_state(self) -> None:
        before = guarded_state_snapshot()
        modules_before = set(sys.modules)
        harness = load_f0_env()

        with tempfile.TemporaryDirectory() as temporary_directory:
            temporary_root = Path(temporary_directory)
            database = temporary_root / "disposable.db"
            with sqlite3.connect(database) as connection:
                connection.execute("CREATE TABLE sample (id INTEGER PRIMARY KEY)")

            with prohibited_activity_traps() as attempts:
                manifest = harness.build_source_manifest(database)
                resolved = harness.assert_operational_db_bind_allowed(
                    f"sqlite:///{database}",
                    environ={},
                )
                self.assertEqual(database.resolve(), resolved)
                self.assertTrue(manifest["source_database"]["components"][0]["present"])

            self.assertEqual([], attempts)

        assert_no_backend_startup_imports()
        newly_loaded = set(sys.modules) - modules_before
        self.assertFalse(
            any(
                name.startswith(
                    (
                        "app.runtime",
                        "backend.app.runtime",
                        "app.services.work_order_executor",
                        "backend.app.services.work_order_executor",
                    )
                )
                for name in newly_loaded
            ),
            f"Runtime/executor module loaded: {sorted(newly_loaded)}",
        )

        after = guarded_state_snapshot()
        self.assertEqual(before, after)
        self.assertEqual(
            before["runtime_registry_digest"],
            after["runtime_registry_digest"],
        )
        self.assertEqual(
            before["work_orders_digest"],
            after["work_orders_digest"],
        )
        self.assertEqual(before["backend_data"], after["backend_data"])
        self.assertEqual(before["private"], after["private"])
        self.assertEqual(
            before["operational_manifest"],
            after["operational_manifest"],
        )
        self.assertEqual(before["git_status"], after["git_status"])


if __name__ == "__main__":
    unittest.main()
