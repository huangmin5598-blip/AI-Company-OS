from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from path_bootstrap import ensure_backend_path


ensure_backend_path()

from app.pilot.bootstrap import bootstrap_pilot_database  # noqa: E402
from app.pilot.database import PilotDatabase  # noqa: E402
from app.pilot.real_workbench import (  # noqa: E402
    ALLOWED_ASSIGNMENT_SLOTS,
    RealWorkbenchStore,
)


class RealWorkbenchDispatchTests(unittest.TestCase):
    def test_each_allowed_slot_can_be_assigned_without_execution(self) -> None:
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
                        "Dispatch all task slots manually.",
                    )
                    task_id = run["task_plan"][0]["task_id"]
                    original_hash = run["task_plan_hash"]
                    for slot in sorted(ALLOWED_ASSIGNMENT_SLOTS):
                        run = store.assign_task(
                            run["run_id"],
                            task_id,
                            slot,
                            f"Assign to {slot}.",
                        )
                        task = run["task_plan"][0]
                        self.assertEqual(slot, task["assigned_slot"])
                        self.assertIn(
                            task["assignment_status"],
                            {"assigned", "revised"},
                        )
                        self.assertEqual("planned", task["status"])
                        self.assertEqual(original_hash, run["task_plan_hash"])
                        self.assertFalse(run["governance"]["real_runtime_invoked"])
                        self.assertFalse(run["governance"]["scheduler_invoked"])
                        self.assertTrue(run["governance"]["manual_dispatch_only"])
            finally:
                database.dispose()

    def test_invalid_slot_and_cross_run_task_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = PilotDatabase.for_disposable_test(
                Path(temporary) / "vs001-pilot.db"
            )
            try:
                bootstrap_pilot_database(database)
                with database.command_session() as session:
                    store = RealWorkbenchStore(session)
                    first = store.create_run(
                        "spoken_agent_offer",
                        "Prepare one spoken-agent run.",
                    )
                    second = store.create_run(
                        "clip_matrix_agent",
                        "Prepare another clip-matrix run.",
                    )
                    task_id = first["task_plan"][0]["task_id"]
                    with self.assertRaisesRegex(
                        ValueError,
                        "real_workbench_assignment_slot_invalid",
                    ):
                        store.assign_task(first["run_id"], task_id, "real_executor")
                    with self.assertRaisesRegex(
                        LookupError,
                        "real_workbench_task_not_found",
                    ):
                        store.assign_task(
                            second["run_id"],
                            task_id,
                            "codex_slot",
                        )
            finally:
                database.dispose()

    def test_assignment_can_be_cleared(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = PilotDatabase.for_disposable_test(
                Path(temporary) / "vs001-pilot.db"
            )
            try:
                bootstrap_pilot_database(database)
                with database.command_session() as session:
                    store = RealWorkbenchStore(session)
                    run = store.create_run(
                        "clip_matrix_agent",
                        "Assign and clear a task.",
                    )
                    task_id = run["task_plan"][0]["task_id"]
                    assigned = store.assign_task(
                        run["run_id"],
                        task_id,
                        "claude_slot",
                        "Draft the clip matrix script.",
                    )
                    self.assertEqual(
                        "assigned",
                        assigned["task_plan"][0]["assignment_status"],
                    )
                    cleared = store.clear_task_assignment(run["run_id"], task_id)
                    task = cleared["task_plan"][0]
                    self.assertIsNone(task["assigned_slot"])
                    self.assertEqual("unassigned", task["assignment_status"])
                    self.assertEqual("", task["assignment_note"])
                    self.assertIsNone(task["assigned_by"])
                    self.assertIsNone(task["assigned_at"])
            finally:
                database.dispose()

    def test_assignment_survives_database_reopen(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "vs001-pilot.db"
            first_database = PilotDatabase.for_disposable_test(path)
            try:
                bootstrap_pilot_database(first_database)
                with first_database.command_session() as session:
                    store = RealWorkbenchStore(session)
                    run = store.create_run(
                        "idea_to_prd_pilot",
                        "Persist a manual assignment.",
                    )
                    run = store.assign_task(
                        run["run_id"],
                        run["task_plan"][0]["task_id"],
                        "manual_founder_slot",
                        "Founder keeps this task.",
                    )
                    run_id = run["run_id"]
            finally:
                first_database.dispose()

            reopened = PilotDatabase.for_disposable_test(path)
            try:
                with reopened.command_session() as session:
                    loaded = RealWorkbenchStore(session).get_run(run_id)
                task = loaded["task_plan"][0]
                self.assertEqual("manual_founder_slot", task["assigned_slot"])
                self.assertEqual("assigned", task["assignment_status"])
                self.assertEqual("local-founder", task["assigned_by"])
                self.assertEqual("Founder keeps this task.", task["assignment_note"])
            finally:
                reopened.dispose()


if __name__ == "__main__":
    unittest.main()
