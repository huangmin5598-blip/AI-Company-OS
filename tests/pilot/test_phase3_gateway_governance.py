from __future__ import annotations

import ast
from pathlib import Path
import tempfile
import unittest

from path_bootstrap import ensure_backend_path


ensure_backend_path()

from app.foundation.local_founder import LocalFounderUnavailable  # noqa: E402
from app.pilot.bootstrap import bootstrap_pilot_database  # noqa: E402
from app.pilot.database import PilotDatabase  # noqa: E402
from app.pilot.gateway import PilotCommandGateway  # noqa: E402


class Phase3GatewayGovernanceTests(unittest.TestCase):
    def test_local_founder_remains_loopback_only(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            database = PilotDatabase.for_disposable_test(
                Path(temporary) / "vs001-pilot.db"
            )
            gateway = PilotCommandGateway(database)
            with self.assertRaisesRegex(
                LocalFounderUnavailable,
                "local_founder_loopback_required",
            ):
                gateway.founder_request(
                    client_host="10.0.0.5",
                    forwarded_for=None,
                    idempotency_key="remote",
                )
            with self.assertRaisesRegex(
                LocalFounderUnavailable,
                "local_founder_forwarded_request_denied",
            ):
                gateway.founder_request(
                    client_host="127.0.0.1",
                    forwarded_for="203.0.113.10",
                    idempotency_key="forwarded",
                )
            database.dispose()

    def test_pilot_router_can_only_reach_commands_through_gateway(self) -> None:
        root = Path(__file__).resolve().parents[2]
        source = (root / "backend/app/pilot/app.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                imports.add(node.module)
            elif isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
        self.assertNotIn("app.services.canonical_execution_service", imports)
        self.assertNotIn(
            "app.repositories.canonical_work_order_command",
            imports,
        )
        self.assertIn("app.pilot.gateway", imports)

    def test_ui_keeps_approve_and_review_as_separate_actions(self) -> None:
        root = Path(__file__).resolve().parents[2]
        page = (root / "frontend/src/app/vs001/page.tsx").read_text(
            encoding="utf-8"
        )
        self.assertIn("2. Approve", page)
        self.assertIn("4. Review Passed", page)
        self.assertNotIn("Auto-Review", page)
        self.assertIn(
            "Local Pilot / OS-Governed / Non-production / Not Operational Authority",
            page,
        )

    def test_gateway_rechecks_marker_before_each_command(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "vs001-pilot.db"
            database = PilotDatabase.for_disposable_test(path)
            try:
                bootstrap_pilot_database(database)
                gateway = PilotCommandGateway(database)
                request = gateway.founder_request(
                    client_host="127.0.0.1",
                    forwarded_for=None,
                    idempotency_key="create-marker-test",
                )
                with __import__("sqlite3").connect(path) as connection:
                    connection.execute("DELETE FROM pilot_marker")
                    connection.commit()
                with self.assertRaisesRegex(
                    RuntimeError,
                    "pilot_marker_authority_invalid",
                ):
                    gateway.create_draft(
                        request,
                        skill_id="vs001.echo-markdown",
                        task_type="render_markdown",
                        input_context="marker must be present",
                        expected_output="markdown",
                    )
            finally:
                database.dispose()

    def test_single_actor_exception_rejects_non_low_risk_approval(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "vs001-pilot.db"
            database = PilotDatabase.for_disposable_test(path)
            try:
                bootstrap_pilot_database(database)
                gateway = PilotCommandGateway(database)

                def request(key: str):
                    return gateway.founder_request(
                        client_host="127.0.0.1",
                        forwarded_for=None,
                        idempotency_key=key,
                    )

                created = gateway.create_draft(
                    request("risk-create"),
                    skill_id="vs001.echo-markdown",
                    task_type="render_markdown",
                    input_context="risk boundary",
                    expected_output="markdown",
                )
                work_order_id = created["data"]["work_order_id"]
                gateway.request_approval(
                    request("risk-request"),
                    work_order_id,
                )
                with database.command_session() as session:
                    session.execute(
                        __import__("sqlalchemy").text(
                            "UPDATE work_approvals SET risk_level='high'"
                            " WHERE target_id=:work_order_id"
                        ),
                        {"work_order_id": work_order_id},
                    )
                with self.assertRaisesRegex(
                    PermissionError,
                    "pilot_single_actor_approval_exception_not_applicable",
                ):
                    gateway.approve(
                        request("risk-approve"),
                        work_order_id,
                    )
            finally:
                database.dispose()


if __name__ == "__main__":
    unittest.main()
