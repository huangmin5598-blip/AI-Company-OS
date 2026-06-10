from __future__ import annotations

import json
from pathlib import Path
import shutil
import unittest
from unittest import mock

from sqlalchemy import text

from path_bootstrap import ensure_backend_path
from test_vuo import PilotAssetScenario


ensure_backend_path()

from app.models.foundation_execution import WorkReview  # noqa: E402


class Vs002ArtifactCaptureTests(unittest.TestCase):
    def test_review_freezes_real_artifact_and_reader_survives_scratch_removal(self) -> None:
        scenario = PilotAssetScenario()
        try:
            _work_order_id, executed, reviewed = scenario.candidate()
            artifact_id = executed["execution"]["artifact_id"]
            with scenario.database.command_session() as session:
                artifact = session.execute(
                    text(
                        "SELECT artifact_id, content_hash, content_text,"
                        " storage_ref FROM pilot_artifacts"
                        " WHERE artifact_id=:artifact_id"
                    ),
                    {"artifact_id": artifact_id},
                ).mappings().one()
                review = session.get(
                    WorkReview,
                    executed["latest_review"]["review_id"],
                )
                self.assertEqual([artifact_id], json.loads(review.artifact_ids_json))
                criteria = json.loads(review.criteria_snapshot_json)
                self.assertTrue(criteria["artifact_set_hash"].startswith("sha256:"))
                self.assertNotIn("scratch://", review.artifact_ids_json)
                self.assertTrue(artifact["storage_ref"].startswith("pilot-db://"))

            for path in scenario.root.iterdir():
                if path.is_dir():
                    shutil.rmtree(path)
            asset_id = reviewed["assets"][0]["asset_id"]
            reader = scenario.gateway.get_asset(
                scenario.request("reader-after-scratch-delete"),
                asset_id,
                include_content=True,
            )
            self.assertEqual(
                artifact["content_hash"],
                reader["content"]["content_hash"],
            )
            self.assertEqual(artifact["content_text"], reader["content"]["text"])
        finally:
            scenario.close()

    def test_artifact_and_review_roll_back_together_on_ingest_audit_failure(self) -> None:
        scenario = PilotAssetScenario()
        try:
            original = __import__(
                "app.services.canonical_execution_service",
                fromlist=["append_audit_event"],
            ).append_audit_event

            def fail_ingest(*args, **kwargs):
                if kwargs.get("event_type") == "work_order.ingest_attempt_result":
                    raise RuntimeError("forced_ingest_audit_failure")
                return original(*args, **kwargs)

            with (
                mock.patch(
                    "app.services.canonical_execution_service.append_audit_event",
                    side_effect=fail_ingest,
                ),
                self.assertRaisesRegex(
                    RuntimeError,
                    "forced_ingest_audit_failure",
                ),
            ):
                scenario.execute()

            with scenario.database.command_session() as session:
                self.assertEqual(
                    0,
                    session.execute(
                        text("SELECT COUNT(*) FROM pilot_artifacts")
                    ).scalar_one(),
                )
                self.assertEqual(
                    0,
                    session.execute(
                        text("SELECT COUNT(*) FROM work_reviews")
                    ).scalar_one(),
                )
        finally:
            scenario.close()

    def test_artifact_rows_are_database_immutable(self) -> None:
        scenario = PilotAssetScenario()
        try:
            _work_order_id, executed = scenario.execute()
            artifact_id = executed["execution"]["artifact_id"]
            with self.assertRaisesRegex(Exception, "pilot_artifacts_append_only"):
                with scenario.database.command_session() as session:
                    session.execute(
                        text(
                            "UPDATE pilot_artifacts SET content_text='changed'"
                            " WHERE artifact_id=:artifact_id"
                        ),
                        {"artifact_id": artifact_id},
                    )
            with self.assertRaisesRegex(Exception, "pilot_artifacts_append_only"):
                with scenario.database.command_session() as session:
                    session.execute(
                        text(
                            "DELETE FROM pilot_artifacts"
                            " WHERE artifact_id=:artifact_id"
                        ),
                        {"artifact_id": artifact_id},
                    )
        finally:
            scenario.close()


if __name__ == "__main__":
    unittest.main()
