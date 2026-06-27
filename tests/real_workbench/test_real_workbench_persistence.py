from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from path_bootstrap import ensure_backend_path


ensure_backend_path()

from app.pilot.bootstrap import bootstrap_pilot_database  # noqa: E402
from app.pilot.database import PilotDatabase  # noqa: E402
from app.pilot.real_workbench import REAL_WORKBENCH_SCHEMA_COMPONENT  # noqa: E402
from app.pilot.real_workbench import RealWorkbenchStore  # noqa: E402


class RealWorkbenchPersistenceTests(unittest.TestCase):
    def test_runs_survive_database_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "vs001-pilot.db"
            first_database = PilotDatabase.for_disposable_test(path)
            try:
                bootstrap_pilot_database(first_database)
                with first_database.command_session() as session:
                    created = RealWorkbenchStore(session).create_run(
                        "clip_matrix_agent",
                        "Plan a clip matrix workflow for the first pilot.",
                    )
                    run_id = created["run_id"]
                    task_plan_hash = created["task_plan_hash"]
            finally:
                first_database.dispose()

            reopened = PilotDatabase.for_disposable_test(path)
            try:
                with reopened.command_session() as session:
                    store = RealWorkbenchStore(session)
                    loaded = store.get_run(run_id)
                    listed = store.list_runs()
                self.assertEqual(run_id, loaded["run_id"])
                self.assertEqual(task_plan_hash, loaded["task_plan_hash"])
                self.assertEqual(4, len(loaded["task_plan"]))
                self.assertEqual([run_id], [run["run_id"] for run in listed])
            finally:
                reopened.dispose()

    def test_corrupted_task_plan_hash_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = PilotDatabase.for_disposable_test(
                Path(temporary) / "vs001-pilot.db"
            )
            try:
                bootstrap_pilot_database(database)
                with database.command_session() as session:
                    run = RealWorkbenchStore(session).create_run(
                        "spoken_agent_offer",
                        "Prepare a spoken agent pilot.",
                    )
                    session.execute(
                        __import__("sqlalchemy").text(
                            "UPDATE pilot_workbench_runs"
                            " SET task_plan_hash='sha256:tampered'"
                            " WHERE run_id=:run_id"
                        ),
                        {"run_id": run["run_id"]},
                    )
                with database.command_session() as session:
                    with self.assertRaisesRegex(
                        RuntimeError,
                        "real_workbench_task_plan_hash_mismatch",
                    ):
                        RealWorkbenchStore(session).get_run(run["run_id"])
            finally:
                database.dispose()

    def test_rs1a_pilot_schema_upgrades_to_manual_dispatch_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = PilotDatabase.for_disposable_test(
                Path(temporary) / "vs001-pilot.db"
            )
            try:
                bootstrap_pilot_database(database)
                with database.command_session() as session:
                    session.execute(
                        __import__("sqlalchemy").text(
                            "UPDATE pilot_schema_components SET version='rs1a-1'"
                            " WHERE component=:component"
                        ),
                        {"component": REAL_WORKBENCH_SCHEMA_COMPONENT},
                    )
            finally:
                database.dispose()

            reopened = PilotDatabase.for_disposable_test(
                Path(temporary) / "vs001-pilot.db"
            )
            try:
                bootstrap_pilot_database(reopened)
                with reopened.command_session() as session:
                    version = session.execute(
                        __import__("sqlalchemy").text(
                            "SELECT version FROM pilot_schema_components"
                            " WHERE component=:component"
                        ),
                        {"component": REAL_WORKBENCH_SCHEMA_COMPONENT},
                    ).scalar_one()
                    run = RealWorkbenchStore(session).create_run(
                        "spoken_agent_offer",
                        "Verify RS1-B manual dispatch columns.",
                    )
                self.assertEqual("rs1b-1", version)
                self.assertEqual(
                    "unassigned",
                    run["task_plan"][0]["assignment_status"],
                )
            finally:
                reopened.dispose()


if __name__ == "__main__":
    unittest.main()
