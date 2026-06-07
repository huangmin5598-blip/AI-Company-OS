from __future__ import annotations

import sys
import unittest

from path_bootstrap import ensure_backend_path

ensure_backend_path()

from app.foundation.work_order_state import (
    ACTIVE_ATTEMPT_STATES,
    CANONICAL_STATES,
    LEGAL_TRANSITIONS,
    TERMINAL_STATES,
    is_legal_transition,
    is_terminal,
)


class E1AWorkOrderStateTests(unittest.TestCase):
    def test_canonical_states_match_s0_3(self) -> None:
        self.assertEqual(
            {
                "draft",
                "waiting_approval",
                "queued",
                "running",
                "waiting_review",
                "revision_required",
                "blocked",
                "done",
                "failed",
                "cancelled",
            },
            set(CANONICAL_STATES),
        )
        self.assertEqual({"done", "failed", "cancelled"}, set(TERMINAL_STATES))
        self.assertEqual(
            {"claimed", "running", "cancellation_requested"},
            set(ACTIVE_ATTEMPT_STATES),
        )

    def test_legal_and_illegal_transitions_are_predicates_only(self) -> None:
        before = frozenset(LEGAL_TRANSITIONS)
        self.assertTrue(is_legal_transition("queued", "running"))
        self.assertTrue(is_legal_transition("waiting_review", "done"))
        self.assertFalse(is_legal_transition("running", "done"))
        self.assertFalse(is_legal_transition("done", "draft"))
        self.assertEqual(before, LEGAL_TRANSITIONS)

    def test_legacy_and_unknown_states_are_rejected(self) -> None:
        for state in ("created", "routed", "assigned", "in_progress", "completed"):
            with self.subTest(state=state):
                with self.assertRaisesRegex(ValueError, "legacy_work_order_state"):
                    is_legal_transition(state, "draft")
        with self.assertRaisesRegex(ValueError, "unknown_work_order_state"):
            is_terminal("invented")

    def test_predicates_do_not_import_or_create_audit_events(self) -> None:
        modules_before = set(sys.modules)
        self.assertTrue(is_terminal("done"))
        self.assertNotIn(
            "app.models.foundation_audit",
            set(sys.modules) - modules_before,
        )


if __name__ == "__main__":
    unittest.main()
