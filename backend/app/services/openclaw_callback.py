# @PRODUCT Service — v0.13 OpenClaw Callback Handler
"""
OpenClaw Callback — handles POST /api/v1/work-orders/{wo_id}/openclaw-callback.

Responsibilities:
  1. API key authentication
  2. Callback body validation
  3. Idempotency (don't overwrite completed WO unless force=true)
  4. State transition validation
  5. Backfill Work Order with results
  6. Update execution_log_json with callback event
"""
import json
import os
from datetime import datetime
from typing import Optional


# Load API key from config or env
DEFAULT_API_KEY = os.environ.get("OPENCLAW_CALLBACK_API_KEY", "oc-test-key-change-me")

# Allowed state transitions for callbacks (old_status -> allowed_new_statuses)
ALLOWED_TRANSITIONS = {
    "in_progress": ["completed", "failed", "needs_review"],
    "openclaw_dispatched": ["completed", "failed", "needs_review"],
    "completed": ["completed"],  # idempotent — same status
    "failed": ["completed", "failed"],  # retry allowed
    "needs_review": ["completed", "failed"],
}

# Required fields in the callback request body
REQUIRED_CALLBACK_FIELDS = ["status"]

# Allowed callback statuses
VALID_CALLBACK_STATUSES = ["completed", "failed", "needs_review"]


def validate_api_key(request_api_key: str) -> bool:
    """
    Validate the API key from the request header.

    Compares against OPENCLAW_CALLBACK_API_KEY env var or default.
    Returns True if valid.
    """
    configured_key = os.environ.get("OPENCLAW_CALLBACK_API_KEY", DEFAULT_API_KEY)
    return request_api_key == configured_key


def validate_callback_body(body: dict) -> list[str]:
    """
    Validate the callback request body.

    Returns list of error messages (empty = valid).
    """
    errors = []
    for field in REQUIRED_CALLBACK_FIELDS:
        if field not in body:
            errors.append(f"Missing required field: '{field}'")

    status = body.get("status", "")
    if status and status not in VALID_CALLBACK_STATUSES:
        errors.append(
            f"Invalid status '{status}'. Must be one of: {', '.join(VALID_CALLBACK_STATUSES)}"
        )

    return errors


def check_idempotent(wo_dict: dict, new_status: str, force: bool = False) -> Optional[str]:
    """
    Check if the callback can proceed based on current WO status.

    Returns:
        None if OK (callback can proceed)
        str error message if callback should be rejected
    """
    current_status = wo_dict.get("status", "")
    allowed_statuses = ALLOWED_TRANSITIONS.get(current_status, [])

    if current_status == "completed" and new_status == "completed":
        # Idempotent: same status, accept
        return None

    if current_status == "completed" and not force:
        return (
            f"Work order is already '{current_status}'. "
            f"Use force=true to overwrite."
        )

    if new_status not in allowed_statuses:
        return (
            f"Cannot transition from '{current_status}' to '{new_status}'. "
            f"Allowed transitions from '{current_status}': {', '.join(allowed_statuses) or 'none'}"
        )

    return None


def build_execution_log_entry(
    wo_id: str,
    status: str,
    body: dict,
    result_source: str = "callback",
) -> dict:
    """
    Build an execution log entry for the callback event.
    """
    return {
        "event": f"openclaw_{status}_via_callback",
        "work_order_id": wo_id,
        "result_source": result_source,
        "status": status,
        "confidence": body.get("confidence"),
        "result_summary": body.get("result_summary", ""),
        "unresolved_questions": body.get("unresolved_questions", []),
        "recommended_follow_up": body.get("recommended_follow_up", ""),
        "metadata": body.get("metadata", {}),
        "completed_at": body.get("completed_at", datetime.utcnow().isoformat() + "Z"),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


def apply_callback_to_work_order(
    wo_dict: dict,
    body: dict,
    force: bool = False,
) -> dict:
    """
    Apply callback results to a work order dict.

    Returns updated wo_dict with new fields.
    Also returns the execution log entry for database persistence.

    Returns:
        {
            "wo_updates": {...},      # Fields to update on the WO
            "execution_log_entry": {...},
            "artifacts": [...],       # From callback body
        }
    """
    status = body.get("status", "completed")
    now = datetime.utcnow()

    # Build the updates dict
    wo_updates = {
        "status": status,
        "result_summary": body.get("result_summary", wo_dict.get("result_summary", "")),
        "output_path": body.get("output_path", wo_dict.get("output_path", "")),
        "artifacts_json": json.dumps(body.get("artifacts", []), ensure_ascii=False),
        "completed_at": now,
    }

    # Set OpenClaw-specific timestamps
    if "openclaw_dispatched_at" in wo_dict and not wo_dict.get("openclaw_dispatched_at"):
        wo_updates["openclaw_dispatched_at"] = now
    if not wo_dict.get("openclaw_claimed_at"):
        wo_updates["openclaw_claimed_at"] = now
    if status in ("completed", "failed"):
        wo_updates["openclaw_dispatched_at"] = body.get(
            "dispatched_at",
            wo_dict.get("openclaw_dispatched_at", now),
        )
        wo_updates["openclaw_claimed_at"] = body.get(
            "claimed_at",
            wo_dict.get("openclaw_claimed_at", now),
        )
    if status == "failed":
        wo_updates["error"] = body.get("error", body.get("result_summary", ""))

    # Build execution log
    log_entry = build_execution_log_entry(
        wo_id=wo_dict.get("work_order_id", ""),
        status=status,
        body=body,
    )

    artifacts = body.get("artifacts", [])

    return {
        "wo_updates": wo_updates,
        "execution_log_entry": log_entry,
        "artifacts": artifacts,
    }
