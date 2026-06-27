from __future__ import annotations

import unittest

from path_bootstrap import ensure_backend_path


ensure_backend_path()

from app.pilot.demo_scenarios import (  # noqa: E402
    DEMO_MODE,
    DEMO_SOURCE_PATH,
    OFFERS,
    PILOT_AUTHORITY,
)
from app.pilot.demo_spine import DemoSpineStore  # noqa: E402


def _advance_until_ready(store: DemoSpineStore, run_id: str) -> dict[str, object]:
    current = store.get_run(run_id)
    for _ in range(32):
        if current["status"] == "ready_for_decision":
            return current
        current = store.advance_run(run_id)
    raise AssertionError("demo run did not become ready")


class DemoSpineContractTests(unittest.TestCase):
    def test_three_public_safe_offer_streams_are_available(self) -> None:
        store = DemoSpineStore()
        offers = store.list_offers()
        self.assertEqual(3, len(offers))
        self.assertEqual(
            {
                "idea_to_prd_pilot",
                "spoken_agent_offer",
                "clip_matrix_agent",
            },
            {offer["offer_id"] for offer in offers},
        )

    def test_parallel_looking_runs_keep_independent_product_line_state(self) -> None:
        store = DemoSpineStore()
        runs = [
            store.create_run(
                offer.offer_id,
                f"Founder validation goal for {offer.display_name}",
            )
            for offer in OFFERS
        ]

        self.assertEqual(3, len(store.list_runs()))
        self.assertEqual(3, len({run["demo_run_id"] for run in runs}))
        for run in runs:
            self.assertEqual(PILOT_AUTHORITY, run["authority"])
            self.assertEqual(DEMO_MODE, run["mode"])
            self.assertEqual(DEMO_SOURCE_PATH, run["source_path"])
            self.assertEqual("planned", run["status"])
            self.assertEqual(4, len(run["tasks"]))
            self.assertEqual(
                {
                    "ceo_agent_slot",
                    "codex_slot",
                    "claude_slot",
                    "local_script_slot",
                },
                {task["executor_slot"] for task in run["tasks"]},
            )
            self.assertTrue(run["governance"]["pilot_only"])
            self.assertFalse(run["governance"]["operational_authority"])
            self.assertFalse(run["governance"]["real_runtime_invoked"])

        advanced = store.advance_run(runs[0]["demo_run_id"])
        untouched = store.get_run(runs[1]["demo_run_id"])
        self.assertEqual("queued", advanced["tasks"][0]["status"])
        self.assertEqual("planned", untouched["tasks"][0]["status"])

    def test_founder_go_no_go_requires_completed_replay_and_asset(self) -> None:
        store = DemoSpineStore()
        run = store.create_run(
            "idea_to_prd_pilot",
            "Prepare a PRD pilot for one concrete founder offer.",
        )

        with self.assertRaisesRegex(ValueError, "demo_run_not_ready_for_decision"):
            store.decide_run(run["demo_run_id"], "go")

        ready = _advance_until_ready(store, run["demo_run_id"])
        self.assertEqual("ready_for_decision", ready["status"])
        self.assertTrue(all(task["status"] == "done" for task in ready["tasks"]))
        self.assertIsNotNone(ready["final_asset"])
        self.assertEqual(
            "restricted",
            ready["final_asset"]["visibility"],
        )
        self.assertFalse(ready["final_asset"]["public_safe"])
        self.assertTrue(
            any(event["event_type"] == "asset.archived" for event in ready["replay"])
        )

        decided = store.decide_run(run["demo_run_id"], "go")
        self.assertEqual("go", decided["status"])
        self.assertEqual("go", decided["founder_decision"])
        with self.assertRaisesRegex(ValueError, "demo_run_already_decided"):
            store.advance_run(run["demo_run_id"])

    def test_invalid_offer_and_decision_fail_closed(self) -> None:
        store = DemoSpineStore()
        with self.assertRaisesRegex(LookupError, "demo_offer_not_found"):
            store.create_run("unknown_offer", "goal")
        run = store.create_run("spoken_agent_offer", "Package a spoken offer.")
        ready = _advance_until_ready(store, run["demo_run_id"])
        self.assertEqual("ready_for_decision", ready["status"])
        with self.assertRaisesRegex(ValueError, "invalid_founder_decision"):
            store.decide_run(run["demo_run_id"], "maybe")


if __name__ == "__main__":
    unittest.main()
