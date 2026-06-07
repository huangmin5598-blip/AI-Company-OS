"""Canonical WorkOrder state contract predicates.

These predicates describe state-machine legality only. They do not authorize
an actor, mutate an object, persist state, or create an Official OS Action.
"""

from __future__ import annotations

from enum import Enum


class WorkOrderState(str, Enum):
    DRAFT = "draft"
    WAITING_APPROVAL = "waiting_approval"
    QUEUED = "queued"
    RUNNING = "running"
    WAITING_REVIEW = "waiting_review"
    REVISION_REQUIRED = "revision_required"
    BLOCKED = "blocked"
    DONE = "done"
    FAILED = "failed"
    CANCELLED = "cancelled"


CANONICAL_STATES = frozenset(state.value for state in WorkOrderState)
TERMINAL_STATES = frozenset(
    {
        WorkOrderState.DONE.value,
        WorkOrderState.FAILED.value,
        WorkOrderState.CANCELLED.value,
    }
)
ACTIVE_ATTEMPT_STATES = frozenset(
    {"claimed", "running", "cancellation_requested"}
)
LEGACY_STATES = frozenset(
    {
        "assigned",
        "completed",
        "created",
        "in_progress",
        "requires_approval",
        "routed",
    }
)

LEGAL_TRANSITIONS = frozenset(
    {
        ("draft", "waiting_approval"),
        ("draft", "queued"),
        ("draft", "blocked"),
        ("draft", "cancelled"),
        ("waiting_approval", "queued"),
        ("waiting_approval", "draft"),
        ("waiting_approval", "cancelled"),
        ("queued", "running"),
        ("queued", "waiting_approval"),
        ("queued", "blocked"),
        ("queued", "cancelled"),
        ("running", "waiting_review"),
        ("waiting_review", "revision_required"),
        ("waiting_review", "done"),
        ("waiting_review", "failed"),
        ("waiting_review", "cancelled"),
        ("revision_required", "queued"),
        ("revision_required", "waiting_approval"),
        ("revision_required", "failed"),
        ("revision_required", "cancelled"),
        ("blocked", "draft"),
        ("blocked", "queued"),
        ("blocked", "waiting_approval"),
        ("blocked", "cancelled"),
    }
)


def _validated_state(value: WorkOrderState | str) -> str:
    normalized = value.value if isinstance(value, WorkOrderState) else value
    if normalized in LEGACY_STATES:
        raise ValueError(f"legacy_work_order_state:{normalized}")
    if normalized not in CANONICAL_STATES:
        raise ValueError(f"unknown_work_order_state:{normalized}")
    return normalized


def is_legal_transition(
    from_state: WorkOrderState | str,
    to_state: WorkOrderState | str,
) -> bool:
    return (_validated_state(from_state), _validated_state(to_state)) in LEGAL_TRANSITIONS


def is_terminal(state: WorkOrderState | str) -> bool:
    return _validated_state(state) in TERMINAL_STATES


__all__ = [
    "ACTIVE_ATTEMPT_STATES",
    "CANONICAL_STATES",
    "LEGAL_TRANSITIONS",
    "TERMINAL_STATES",
    "WorkOrderState",
    "is_legal_transition",
    "is_terminal",
]
