from __future__ import annotations

from collections.abc import Mapping, Sequence
import unittest

from path_bootstrap import ensure_backend_path


ensure_backend_path()

from app.pilot.demo_spine import DemoSpineStore  # noqa: E402


FORBIDDEN_KEYS = {
    "storage_ref",
    "scratch_root",
    "scratch_path",
    "result_ref",
    "database_path",
    "operational_db_path",
}
FORBIDDEN_VALUE_FRAGMENTS = (
    "/Users/",
    "backend/data",
    "private/",
    ".ai-company-os/pilot/vs001-pilot.db",
)


def _walk(value):
    if isinstance(value, Mapping):
        for key, nested in value.items():
            yield ("key", str(key))
            yield from _walk(nested)
    elif isinstance(value, str):
        yield ("value", value)
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            yield from _walk(item)


class DemoSpinePublicBoundaryTests(unittest.TestCase):
    def test_envelopes_expose_no_private_paths_or_storage_refs(self) -> None:
        store = DemoSpineStore()
        run = store.create_run(
            "idea_to_prd_pilot",
            "Create one public-build-safe replay asset.",
        )
        for _ in range(20):
            current = store.get_run(run["demo_run_id"])
            if current["status"] == "ready_for_decision":
                break
            store.advance_run(run["demo_run_id"])
        envelope = store.decide_run(run["demo_run_id"], "go")

        for kind, item in _walk(envelope):
            if kind == "key":
                self.assertNotIn(item, FORBIDDEN_KEYS)
            if kind == "value":
                for fragment in FORBIDDEN_VALUE_FRAGMENTS:
                    self.assertNotIn(fragment, item)

    def test_demo_assets_remain_restricted_and_non_public_safe(self) -> None:
        store = DemoSpineStore()
        run = store.create_run(
            "spoken_agent_offer",
            "Produce a voice offer workbench asset.",
        )
        for _ in range(20):
            current = store.get_run(run["demo_run_id"])
            if current["status"] == "ready_for_decision":
                break
            store.advance_run(run["demo_run_id"])
        ready = store.get_run(run["demo_run_id"])
        asset = ready["final_asset"]
        self.assertIsNotNone(asset)
        self.assertEqual("pilot_non_authoritative", asset["authority"])
        self.assertEqual("restricted", asset["visibility"])
        self.assertFalse(asset["public_safe"])
        self.assertIn("Founder goal:", asset["content_markdown"])

    def test_demo_spine_never_claims_real_executor_invocation(self) -> None:
        store = DemoSpineStore()
        run = store.create_run(
            "clip_matrix_agent",
            "Prepare a replay without real executor calls.",
        )
        envelope = store.advance_run(run["demo_run_id"])
        self.assertFalse(envelope["governance"]["real_runtime_invoked"])
        self.assertFalse(envelope["governance"]["public_safe"])
        self.assertFalse(envelope["governance"]["operational_authority"])
        self.assertTrue(envelope["governance"]["pilot_only"])


if __name__ == "__main__":
    unittest.main()
