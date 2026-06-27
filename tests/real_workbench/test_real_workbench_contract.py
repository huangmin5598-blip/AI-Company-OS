from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from path_bootstrap import ensure_backend_path


ensure_backend_path()

from app.pilot.bootstrap import bootstrap_pilot_database  # noqa: E402
from app.pilot.database import PILOT_AUTHORITY, PilotDatabase  # noqa: E402
from app.pilot.real_workbench import (  # noqa: E402
    REAL_WORKBENCH_MODE,
    REAL_WORKBENCH_SOURCE_PATH,
    RealWorkbenchStore,
)


class RealWorkbenchContractTests(unittest.TestCase):
    def test_templates_cover_three_initial_product_lines(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = PilotDatabase.for_disposable_test(
                Path(temporary) / "vs001-pilot.db"
            )
            try:
                bootstrap_pilot_database(database)
                with database.command_session() as session:
                    templates = RealWorkbenchStore(session).list_templates()
                self.assertEqual(
                    {
                        "idea_to_prd_pilot",
                        "spoken_agent_offer",
                        "clip_matrix_agent",
                    },
                    {template["product_line_id"] for template in templates},
                )
                for template in templates:
                    self.assertEqual(PILOT_AUTHORITY, template["authority"])
                    self.assertEqual(REAL_WORKBENCH_MODE, template["mode"])
                    self.assertEqual(4, template["task_count"])
            finally:
                database.dispose()

    def test_create_run_persists_planned_task_plan_without_executor_invocation(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = PilotDatabase.for_disposable_test(
                Path(temporary) / "vs001-pilot.db"
            )
            try:
                bootstrap_pilot_database(database)
                with database.command_session() as session:
                    run = RealWorkbenchStore(session).create_run(
                        "idea_to_prd_pilot",
                        "Turn a concrete founder idea into a first PRD.",
                    )

                self.assertEqual("planned", run["status"])
                self.assertEqual(PILOT_AUTHORITY, run["authority"])
                self.assertEqual(REAL_WORKBENCH_MODE, run["mode"])
                self.assertEqual(REAL_WORKBENCH_SOURCE_PATH, run["source_path"])
                self.assertEqual(4, len(run["task_plan"]))
                self.assertTrue(run["task_plan_hash"].startswith("sha256:"))
                self.assertTrue(run["governance"]["pilot_only"])
                self.assertFalse(run["governance"]["operational_authority"])
                self.assertFalse(run["governance"]["real_runtime_invoked"])
                self.assertFalse(run["governance"]["scheduler_invoked"])
                self.assertFalse(run["governance"]["worker_pool_invoked"])
                for task in run["task_plan"]:
                    self.assertEqual("planned", task["status"])
                    self.assertEqual(PILOT_AUTHORITY, task["authority"])
                    self.assertIn(
                        task["executor_slot"],
                        {
                            "ceo_agent_slot",
                            "codex_slot",
                            "claude_slot",
                            "local_script_slot",
                        },
                    )
            finally:
                database.dispose()

    def test_invalid_product_line_and_blank_goal_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = PilotDatabase.for_disposable_test(
                Path(temporary) / "vs001-pilot.db"
            )
            try:
                bootstrap_pilot_database(database)
                with database.command_session() as session:
                    store = RealWorkbenchStore(session)
                    with self.assertRaisesRegex(
                        LookupError,
                        "real_workbench_product_line_not_found",
                    ):
                        store.create_run("unknown", "goal")
                    with self.assertRaisesRegex(ValueError, "founder_goal_required"):
                        store.create_run("spoken_agent_offer", "   ")
            finally:
                database.dispose()

    def test_api_routes_create_list_and_get_persistent_runs(self) -> None:
        from app.pilot import app as pilot_app  # noqa: WPS433
        from app.pilot.gateway import PilotCommandGateway  # noqa: WPS433

        original_database = pilot_app.database
        original_gateway = pilot_app.gateway
        with tempfile.TemporaryDirectory() as temporary:
            database = PilotDatabase.for_disposable_test(
                Path(temporary) / "vs001-pilot.db"
            )
            pilot_app.database = database
            pilot_app.gateway = PilotCommandGateway(database)
            try:
                with TestClient(pilot_app.app) as client:
                    templates = client.get(
                        "/api/v1/vs001/real-workbench/templates"
                    )
                    self.assertEqual(200, templates.status_code)
                    self.assertEqual(3, len(templates.json()["templates"]))

                    created = client.post(
                        "/api/v1/vs001/real-workbench/runs",
                        json={
                            "product_line_id": "idea_to_prd_pilot",
                            "founder_goal": "Create a persistent API run.",
                        },
                    )
                    self.assertEqual(200, created.status_code)
                    run = created.json()

                    listed = client.get("/api/v1/vs001/real-workbench/runs")
                    self.assertEqual(200, listed.status_code)
                    self.assertEqual(
                        [run["run_id"]],
                        [item["run_id"] for item in listed.json()["runs"]],
                    )

                    fetched = client.get(
                        f"/api/v1/vs001/real-workbench/runs/{run['run_id']}"
                    )
                    self.assertEqual(200, fetched.status_code)
                    self.assertEqual(run["task_plan_hash"], fetched.json()["task_plan_hash"])
            finally:
                pilot_app.database = original_database
                pilot_app.gateway = original_gateway
                database.dispose()


if __name__ == "__main__":
    unittest.main()
