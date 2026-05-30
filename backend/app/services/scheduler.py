"""v0.17 — Scheduler: YAML-based Work Order scheduling and dedup.

Reads config/scheduled_work_orders.yaml, determines which tasks are due,
handles dedup (same scheduled_wo_id + same day = no duplicate unless --force).
"""

import os
import yaml
from datetime import datetime, date
from typing import Optional

from app.database import get_sync_session
from app.models.work_order import WorkOrder
from app.services.skill_registry import get_contract

_CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "config", "scheduled_work_orders.yaml")


# ── Data types ──


class ScheduledWorkOrder:
    """A single entry from scheduled_work_orders.yaml."""

    def __init__(self, raw: dict):
        self.id: str = raw["id"]
        self.label: str = raw.get("label", self.id)
        self.cadence: str = raw.get("cadence", "daily")
        self.time: str = raw.get("time", "09:00")
        self.day: Optional[str] = raw.get("day")  # monday-sunday for weekly
        self.task_type: str = raw["task_type"]
        self.skill_id: str = raw.get("skill_id", "")
        self.agent: str = raw.get("agent", "")
        self.risk_level: str = raw.get("risk_level", "low")
        self.execution_mode: str = raw.get("execution_mode", "direct_delegate")
        self.input_context: str = raw.get("input_context", "")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "cadence": self.cadence,
            "time": self.time,
            "day": self.day,
            "task_type": self.task_type,
            "skill_id": self.skill_id,
            "agent": self.agent,
            "risk_level": self.risk_level,
            "execution_mode": self.execution_mode,
            "input_context": self.input_context,
        }


# ── Loader ──


def load_scheduled_work_orders(force_reload: bool = False) -> list[ScheduledWorkOrder]:
    """Load scheduled work orders from YAML config.

    Returns:
        List of ScheduledWorkOrder objects. Empty list if YAML missing or invalid.
    """
    if not os.path.exists(_CONFIG_PATH):
        print(f"[scheduler] No config at {_CONFIG_PATH} — no scheduled tasks")
        return []

    try:
        with open(_CONFIG_PATH, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)
    except Exception as e:
        print(f"[scheduler] Failed to load {_CONFIG_PATH}: {e}")
        return []

    if not raw or "scheduled_work_orders" not in raw:
        print(f"[scheduler] Empty config at {_CONFIG_PATH}")
        return []

    orders = []
    for entry in raw["scheduled_work_orders"]:
        try:
            orders.append(ScheduledWorkOrder(entry))
        except (KeyError, TypeError) as e:
            print(f"[scheduler] Skipping invalid entry {entry.get('id', '?' )}: {e}")
    return orders


# ── Due check ──


def _is_due_today(scheduled: ScheduledWorkOrder, today: Optional[date] = None) -> bool:
    """Check if a scheduled task is due on today's date.

    Args:
        scheduled: The scheduled work order config.
        today: Date to check (default: today's local date).

    Returns:
        True if the task should trigger today.
    """
    if today is None:
        today = date.today()

    if scheduled.cadence == "daily":
        return True

    if scheduled.cadence == "weekly":
        if not scheduled.day:
            return False
        weekday_map = {
            "monday": 0, "tuesday": 1, "wednesday": 2,
            "thursday": 3, "friday": 4, "saturday": 5, "sunday": 6,
        }
        expected = weekday_map.get(scheduled.day.lower())
        if expected is None:
            return False
        return today.weekday() == expected

    if scheduled.cadence == "monthly":
        # Default to 1st of month; could add "day_of_month" field later
        return today.day == 1

    return False


# ── Dedup ──


def _dedup_key(scheduled_id: str, for_date: Optional[date] = None) -> str:
    """Generate a dedup key: scheduled_id + date string.

    Used to prevent duplicate Work Orders for the same scheduled task on the same day.
    """
    if for_date is None:
        for_date = date.today()
    return f"{scheduled_id}:{for_date.isoformat()}"


def already_ran_today(scheduled_id: str, for_date: Optional[date] = None) -> bool:
    """Check if a scheduled work order has already run today.

    Searches DB for any Work Order whose route_reason starts with
    'scheduled:{scheduled_id}:YYYY-MM-DD'.

    Args:
        scheduled_id: The scheduled work order ID.
        for_date: Date to check (default: today).

    Returns:
        True if a matching Work Order exists.
    """
    key = _dedup_key(scheduled_id, for_date)
    session = get_sync_session()
    try:
        existing = session.query(WorkOrder).filter(
            WorkOrder.route_reason.startswith(f"scheduled:{key}")
        ).first()
        return existing is not None
    finally:
        session.close()


def build_scheduled_reason(scheduled_id: str, for_date: Optional[date] = None) -> str:
    """Build the route_reason string for a scheduled Work Order.

    Format: "scheduled:{scheduled_id}:YYYY-MM-DD"
    """
    key = _dedup_key(scheduled_id, for_date)
    return f"scheduled:{key}"


# ── End-to-end runner helpers ──


def get_due_tasks(today: Optional[date] = None,
                  force: bool = False) -> list[ScheduledWorkOrder]:
    """Get all scheduled tasks that are due today and haven't run yet.

    Args:
        today: Date to check (default: today).
        force: If True, skip dedup check (allow re-running).

    Returns:
        List of ScheduledWorkOrders that should run now.
    """
    if today is None:
        today = date.today()

    all_tasks = load_scheduled_work_orders()
    due = []
    for task in all_tasks:
        if not _is_due_today(task, today):
            continue
        if not force and already_ran_today(task.id, today):
            print(f"[scheduler] ⏭  [{task.id}] already ran today — skipped (use --force to override)")
            continue
        due.append(task)
    return due
