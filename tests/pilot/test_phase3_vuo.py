from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from sqlalchemy import text

from path_bootstrap import ensure_backend_path


ensure_backend_path()

from app.pilot.bootstrap import bootstrap_pilot_database  # noqa: E402
from app.pilot.database import (  # noqa: E402
    OPERATIONAL_DB_PATH,
    PilotDatabase,
    sha256_file,
)
from app.pilot.gateway import PilotCommandGateway  # noqa: E402


class Phase3ValidatedUserOutcomeTests(unittest.TestCase):
    def test_truthful_local_loop_reaches_done_only_after_review(self) -> None:
        operational_before = sha256_file(OPERATIONAL_DB_PATH)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            database = PilotDatabase.for_disposable_test(
                root / "vs001-pilot.db"
            )
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
                    request("vuo-create"),
                    skill_id="vs001.echo-markdown",
                    task_type="render_markdown",
                    input_context="Review remains authoritative.",
                    expected_output="One reviewed Markdown result.",
                )
                work_order_id = created["data"]["work_order_id"]
                self.assertEqual("draft", created["data"]["canonical_state"])

                requested = gateway.request_approval(
                    request("vuo-request"),
                    work_order_id,
                )
                self.assertEqual(
                    "waiting_approval",
                    requested["data"]["canonical_state"],
                )

                approved = gateway.approve(
                    request("vuo-approve"),
                    work_order_id,
                )
                self.assertEqual("queued", approved["data"]["canonical_state"])

                executed = gateway.execute(
                    request("vuo-execute"),
                    work_order_id,
                    heading="Truthful local execution",
                    body="Review remains authoritative.",
                    scratch_parent=root,
                )
                self.assertEqual(
                    "waiting_review",
                    executed["data"]["canonical_state"],
                )
                self.assertIn(
                    "# Truthful local execution",
                    executed["execution"]["result_markdown"],
                )
                self.assertEqual(
                    "requested",
                    executed["latest_review"]["state"],
                )

                reviewed = gateway.review(
                    request("vuo-review"),
                    work_order_id,
                )
                self.assertEqual("done", reviewed["data"]["canonical_state"])
                self.assertEqual("passed", reviewed["latest_review"]["state"])
                self.assertEqual(
                    "local-founder",
                    reviewed["latest_approval"]["decided_by"],
                )

                with database.command_session() as session:
                    self.assertEqual(
                        1,
                        session.execute(
                            text(
                                "SELECT COUNT(*) FROM work_approvals"
                                " WHERE target_id=:work_order_id"
                            ),
                            {"work_order_id": work_order_id},
                        ).scalar_one(),
                    )
                    self.assertEqual(
                        1,
                        session.execute(
                            text(
                                "SELECT COUNT(*) FROM work_reviews"
                                " WHERE work_order_id=:work_order_id"
                            ),
                            {"work_order_id": work_order_id},
                        ).scalar_one(),
                    )
                    event_types = set(
                        session.execute(
                            text(
                                "SELECT event_type FROM audit_events"
                                " WHERE work_order_id=:work_order_id"
                            ),
                            {"work_order_id": work_order_id},
                        ).scalars()
                    )
                    self.assertIn(
                        "work_order.approval_approved",
                        event_types,
                    )
                    self.assertIn("work_order.review_passed", event_types)
            finally:
                database.dispose()
        self.assertEqual(operational_before, sha256_file(OPERATIONAL_DB_PATH))


if __name__ == "__main__":
    unittest.main()
