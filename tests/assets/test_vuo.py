from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from path_bootstrap import ensure_backend_path


ensure_backend_path()

from app.pilot.bootstrap import bootstrap_pilot_database  # noqa: E402
from app.pilot.database import PilotDatabase  # noqa: E402
from app.pilot.gateway import PilotCommandGateway  # noqa: E402


class PilotAssetScenario:
    def __init__(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.database = PilotDatabase.for_disposable_test(
            self.root / "vs001-pilot.db"
        )
        bootstrap_pilot_database(self.database)
        self.gateway = PilotCommandGateway(self.database)

    def close(self) -> None:
        self.database.dispose()
        self.temporary.cleanup()

    def request(self, key: str):
        return self.gateway.founder_request(
            client_host="127.0.0.1",
            forwarded_for=None,
            idempotency_key=key,
        )

    def execute(self):
        created = self.gateway.create_draft(
            self.request("vs002-create"),
            skill_id="vs001.echo-markdown",
            task_type="approved_output_to_asset",
            input_context="Persist reviewed output as a restricted Pilot Asset.",
            expected_output="One immutable Markdown Artifact.",
        )
        work_order_id = created["data"]["work_order_id"]
        self.gateway.request_approval(
            self.request("vs002-request"),
            work_order_id,
        )
        self.gateway.approve(self.request("vs002-approve"), work_order_id)
        executed = self.gateway.execute(
            self.request("vs002-execute"),
            work_order_id,
            heading="VS-002 Artifact",
            body="Approved output remains pilot non-authoritative.",
            scratch_parent=self.root,
        )
        return work_order_id, executed

    def candidate(self):
        work_order_id, executed = self.execute()
        reviewed = self.gateway.review(
            self.request("vs002-review"),
            work_order_id,
        )
        return work_order_id, executed, reviewed


class Vs002ValidatedOutcomeTests(unittest.TestCase):
    def test_review_then_separate_asset_approval_reaches_approved(self) -> None:
        scenario = PilotAssetScenario()
        try:
            work_order_id, executed, reviewed = scenario.candidate()
            self.assertEqual("waiting_review", executed["data"]["canonical_state"])
            self.assertNotIn("scratch_root", executed["execution"])
            self.assertNotIn("result_ref", executed["execution"])
            self.assertTrue(executed["execution"]["artifact_id"].startswith("art_"))
            self.assertEqual("done", reviewed["data"]["canonical_state"])
            self.assertEqual(1, len(reviewed["assets"]))
            self.assertEqual("candidate", reviewed["assets"][0]["status"])

            asset_id = reviewed["assets"][0]["asset_id"]
            candidate = scenario.gateway.get_asset(
                scenario.request("vs002-asset-read"),
                asset_id,
                include_content=True,
            )
            self.assertEqual("requested", candidate["approval"]["decision"])
            self.assertEqual("pilot_non_authoritative", candidate["asset"]["authority"])
            self.assertEqual("restricted", candidate["asset"]["visibility"])
            self.assertIsNone(candidate["asset"]["public_safe_ref"])
            self.assertIn("# VS-002 Artifact", candidate["content"]["text"])

            approved = scenario.gateway.approve_asset(
                scenario.request("vs002-asset-approve"),
                asset_id,
            )
            self.assertEqual("approved", approved["asset"]["status"])
            self.assertEqual("approved", approved["approval"]["decision"])
            self.assertEqual(
                work_order_id,
                approved["asset"]["source_work_order_id"],
            )
        finally:
            scenario.close()


if __name__ == "__main__":
    unittest.main()
