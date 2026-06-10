from __future__ import annotations

import unittest

from sqlalchemy import select, text

from path_bootstrap import ensure_backend_path
from test_vuo import PilotAssetScenario


ensure_backend_path()

from app.models.foundation_execution import WorkApproval  # noqa: E402
from app.services.pilot_asset_service import create_asset_candidate  # noqa: E402


class Vs002AssetPromotionTests(unittest.TestCase):
    def test_review_and_asset_approval_are_separate_records_and_events(self) -> None:
        scenario = PilotAssetScenario()
        try:
            work_order_id, _executed, reviewed = scenario.candidate()
            asset_id = reviewed["assets"][0]["asset_id"]
            with scenario.database.command_session() as session:
                asset_approval = session.execute(
                    select(WorkApproval).where(
                        WorkApproval.target_type == "asset_candidate",
                        WorkApproval.target_id == asset_id,
                    )
                ).scalar_one()
                self.assertEqual("promote_to_asset", asset_approval.action)
                self.assertEqual("requested", asset_approval.decision)
                event_types = session.execute(
                    text(
                        "SELECT event_type FROM audit_events"
                        " WHERE work_order_id=:work_order_id"
                    ),
                    {"work_order_id": work_order_id},
                ).scalars().all()
                self.assertIn("work_order.review_passed", event_types)
                self.assertIn("asset.candidate_created", event_types)
                self.assertNotIn("asset.approved", event_types)

            scenario.gateway.approve_asset(
                scenario.request("separate-asset-approval"),
                asset_id,
            )
            with scenario.database.command_session() as session:
                event_types = session.execute(
                    text(
                        "SELECT event_type FROM audit_events"
                        " WHERE work_order_id=:work_order_id"
                    ),
                    {"work_order_id": work_order_id},
                ).scalars().all()
                self.assertIn("artifact.captured", event_types)
                self.assertIn("asset.candidate_created", event_types)
                self.assertIn("asset.approved", event_types)
                for event_type in (
                    "artifact.captured",
                    "asset.candidate_created",
                    "asset.approved",
                ):
                    self.assertEqual(1, event_types.count(event_type))
                packet_actions = set(
                    session.execute(
                        text(
                            "SELECT action_type FROM audit_packets"
                            " WHERE work_order_id=:work_order_id"
                        ),
                        {"work_order_id": work_order_id},
                    ).scalars()
                )
                self.assertTrue(
                    {
                        "artifact.captured",
                        "asset.candidate_created",
                        "asset.approved",
                    }.issubset(packet_actions)
                )
        finally:
            scenario.close()

    def test_native_promotion_records_are_not_used(self) -> None:
        scenario = PilotAssetScenario()
        try:
            _work_order_id, _executed, reviewed = scenario.candidate()
            scenario.gateway.approve_asset(
                scenario.request("no-native-promotion"),
                reviewed["assets"][0]["asset_id"],
            )
            with scenario.database.command_session() as session:
                self.assertEqual(
                    0,
                    session.execute(
                        text("SELECT COUNT(*) FROM promotion_records")
                    ).scalar_one(),
                )
        finally:
            scenario.close()

    def test_asset_approval_replays_without_duplicate_audit(self) -> None:
        scenario = PilotAssetScenario()
        try:
            _work_order_id, _executed, reviewed = scenario.candidate()
            asset_id = reviewed["assets"][0]["asset_id"]
            request = scenario.request("asset-approval-replay")
            first = scenario.gateway.approve_asset(request, asset_id)
            replay = scenario.gateway.approve_asset(request, asset_id)
            self.assertEqual(first["asset"]["asset_id"], replay["asset"]["asset_id"])
            with scenario.database.command_session() as session:
                self.assertEqual(
                    1,
                    session.execute(
                        text(
                            "SELECT COUNT(*) FROM audit_events"
                            " WHERE aggregate_type='asset'"
                            " AND aggregate_id=:asset_id"
                            " AND event_type='asset.approved'"
                        ),
                        {"asset_id": asset_id},
                    ).scalar_one(),
                )
        finally:
            scenario.close()

    def test_candidate_semantic_replay_does_not_duplicate_approval_or_audit(
        self,
    ) -> None:
        scenario = PilotAssetScenario()
        try:
            _work_order_id, _executed, reviewed = scenario.candidate()
            asset_id = reviewed["assets"][0]["asset_id"]
            candidate = scenario.gateway.get_asset(
                scenario.request("semantic-candidate-read"),
                asset_id,
            )
            review_id = candidate["asset"]["source_review_id"]
            with scenario.database.command_session() as session:
                replay = create_asset_candidate(
                    session,
                    scenario.request("semantic-candidate-new-key"),
                    review_id=review_id,
                    title="Same review, different idempotency key",
                )
                self.assertTrue(replay.replayed)
                self.assertEqual(asset_id, replay.asset_id)
                self.assertEqual(
                    1,
                    session.execute(
                        text(
                            "SELECT COUNT(*) FROM work_approvals"
                            " WHERE target_type='asset_candidate'"
                            " AND target_id=:asset_id"
                        ),
                        {"asset_id": asset_id},
                    ).scalar_one(),
                )
                self.assertEqual(
                    1,
                    session.execute(
                        text(
                            "SELECT COUNT(*) FROM audit_events"
                            " WHERE event_type='asset.candidate_created'"
                            " AND aggregate_id=:asset_id"
                        ),
                        {"asset_id": asset_id},
                    ).scalar_one(),
                )
        finally:
            scenario.close()


if __name__ == "__main__":
    unittest.main()
