# @PRODUCT Service — v0.13 OpenClaw Bridge (Real Callback MVP)
"""
OpenClaw Bridge v2 — Inbox/Outbox file protocol for task dispatch and result collection.

Architecture:
  AI Company OS writes task.json to inbox/
  OpenClaw reads inbox/ → moves to working/
  OpenClaw writes result.json + output files to artifacts/<WO-ID>/
  AI Company OS poll_results() reads artifacts/<WO-ID>/result.json

Directory structure:
  ~/.ai-company-os/openclaw/
    inbox/          ← AI Company OS writes task cards here
    working/        ← OpenClaw moves task cards here when claimed
  ~/.ai-company-os/artifacts/<WO-ID>/
    result.json     ← OpenClaw writes result manifest here
    output files...

Conventions:
  - poll_results() ONLY checks for result.json — never guesses based on arbitrary files
  - Without result.json, task is not considered complete
  - Malformed result.json → status = needs_review
"""
import json
import os
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


# Base directory
BASE_OPENCLAW_DIR = os.path.expanduser("~/.ai-company-os/openclaw/")
BASE_ARTIFACTS_DIR = os.path.expanduser("~/.ai-company-os/artifacts/")

# Subdirectories
INBOX_DIR = os.path.join(BASE_OPENCLAW_DIR, "inbox")
WORKING_DIR = os.path.join(BASE_OPENCLAW_DIR, "working")
LOGS_DIR = os.path.join(BASE_OPENCLAW_DIR, "logs")

# Required fields for a valid Result Manifest
REQUIRED_RESULT_FIELDS = {
    "work_order_id": str,
    "status": str,
    "result_summary": str,
}

# Allowed result statuses
VALID_RESULT_STATUSES = {"completed", "failed", "needs_review"}

# Default timeout for OpenClaw tasks (seconds)
DEFAULT_TIMEOUT = 300  # 5 min

# Polling interval (seconds)
DEFAULT_POLL_INTERVAL = 5


def _ensure_dir(path: str) -> bool:
    """Ensure directory exists and is writable. Returns True if ready."""
    try:
        os.makedirs(path, exist_ok=True)
        test_file = os.path.join(path, f".write_test_{uuid.uuid4().hex}.tmp")
        Path(test_file).write_text("ok")
        os.remove(test_file)
        return True
    except (OSError, PermissionError):
        return False


def _validate_result_manifest(data: dict) -> list[str]:
    """Validate a result manifest JSON. Returns list of error messages (empty = valid)."""
    errors = []
    for field, expected_type in REQUIRED_RESULT_FIELDS.items():
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif not isinstance(data[field], expected_type):
            errors.append(
                f"Field '{field}' should be {expected_type.__name__}, got {type(data[field]).__name__}"
            )
    if "status" in data and data["status"] not in VALID_RESULT_STATUSES:
        errors.append(
            f"Invalid status '{data['status']}'. Must be one of: {', '.join(sorted(VALID_RESULT_STATUSES))}"
        )
    return errors


def _artifact_dir(wo_id: str) -> str:
    """Get the artifacts directory for a given work order ID."""
    return os.path.join(BASE_ARTIFACTS_DIR, wo_id)


def _result_json_path(wo_id: str) -> str:
    """Get the path to result.json for a given work order ID."""
    return os.path.join(_artifact_dir(wo_id), "result.json")


def _task_card_path(wo_id: str, dir_path: str) -> str:
    """Get the path to a task card JSON file."""
    return os.path.join(dir_path, f"{wo_id}.task.json")


class OpenClawBridge:
    """
    v0.13 enhanced OpenClaw Bridge.

    Manages the full lifecycle of OpenClaw task dispatch and result collection
    via shared filesystem (Inbox/Outbox contract).
    """

    def __init__(self):
        self._ready = False

    @property
    def is_ready(self) -> bool:
        """Check if all required directories exist and are writable."""
        if not self._ready:
            self._ready = (
                _ensure_dir(INBOX_DIR)
                and _ensure_dir(WORKING_DIR)
                and _ensure_dir(LOGS_DIR)
                and _ensure_dir(BASE_ARTIFACTS_DIR)
            )
        return self._ready

    # ── Task Card Creation ──

    def create_task_card(self, work_order: any) -> dict:
        """
        Create an enhanced task card and write it to the inbox directory.

        The task card follows the full JSON schema defined in the v0.13 PRD:
        card_id, work_order_id, goal_session_id, product_line_id, task_type,
        goal, context, expected_output, allowed_actions, forbidden_actions,
        allowed_tools, report_back_path, timeout_seconds, risk_level,
        requires_human_review, created_at.

        Args:
            work_order: WorkOrder ORM object or to_dict() dictionary

        Returns:
            {
                "status": "dispatched_to_openclaw" | "created" (fallback) | "failed",
                "card_id": str,
                "card_path": str,
                "inbox_path": str,
                "execution_state": {...},
                "fallback": bool,
            }
        """
        wo_id = (
            work_order.work_order_id
            if hasattr(work_order, "work_order_id")
            else work_order.get("work_order_id", "")
        )
        if not wo_id:
            return {"status": "failed", "error": "No work_order_id provided"}

        card = self._build_task_card(work_order)
        card_path = _task_card_path(wo_id, INBOX_DIR)
        artifacts_dir = _artifact_dir(wo_id)

        if not self.is_ready:
            # Fallback: return card without writing
            return {
                "status": "created",
                "card_id": card["card_id"],
                "card_path": "",
                "inbox_path": INBOX_DIR,
                "execution_state": None,
                "fallback": True,
                "message": "OpenClaw directories not writable — card generated but not saved to inbox",
                "card": card,
            }

        try:
            # Ensure artifacts directory exists for results
            _ensure_dir(artifacts_dir)

            # Write task card to inbox
            Path(card_path).write_text(
                json.dumps(card, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            # Record execution state
            now_ts = datetime.utcnow().isoformat() + "Z"
            execution_state = {
                "dispatched_to_openclaw": now_ts,
                "claimed_by_openclaw": None,
                "running": None,
                "completed": None,
                "failed": None,
                "timeout": None,
                "needs_review": None,
            }

            return {
                "status": "dispatched_to_openclaw",
                "card_id": card["card_id"],
                "card_path": card_path,
                "inbox_path": INBOX_DIR,
                "execution_state": execution_state,
                "fallback": False,
            }
        except OSError as e:
            return {
                "status": "failed",
                "error": f"Failed to write task card: {e}",
                "card_id": card["card_id"],
                "fallback": True,
                "card": card,
            }

    def _build_task_card(self, work_order: any) -> dict:
        """Build the enhanced task card dict from a work order."""
        def _get(key, default=""):
            if hasattr(work_order, key):
                return getattr(work_order, key, default)
            return work_order.get(key, default)

        wo_id = _get("work_order_id")
        card_id = f"CEO-TASK-{uuid.uuid4().hex[:8].upper()}"
        artifacts_dir = _artifact_dir(wo_id)

        # Parse or build allowed/forbidden actions from the work order
        # These can come from skill_router routing info or be set directly
        allowed_actions = _get("allowed_actions", [])
        if isinstance(allowed_actions, str):
            try:
                allowed_actions = json.loads(allowed_actions)
            except (json.JSONDecodeError, TypeError):
                allowed_actions = ["read_faq", "write_response"]

        forbidden_actions = _get("forbidden_actions", [])
        if isinstance(forbidden_actions, str):
            try:
                forbidden_actions = json.loads(forbidden_actions)
            except (json.JSONDecodeError, TypeError):
                forbidden_actions = ["send_email", "deploy", "delete_file", "modify_code"]

        allowed_tools = _get("allowed_tools", [])
        if isinstance(allowed_tools, str):
            try:
                allowed_tools = json.loads(allowed_tools)
            except (json.JSONDecodeError, TypeError):
                allowed_tools = []

        risk_level = _get("risk_level", "low")
        requires_human_review = risk_level in ("medium", "high") or _get("requires_human_review", False)

        timeout_val = _get("timeout_seconds", DEFAULT_TIMEOUT)
        if not isinstance(timeout_val, (int, float)):
            try:
                timeout_val = int(timeout_val)
            except (ValueError, TypeError):
                timeout_val = DEFAULT_TIMEOUT

        return {
            "card_id": card_id,
            "work_order_id": wo_id,
            "goal_session_id": _get("goal_session_id", ""),
            "product_line_id": _get("product_line_id", ""),
            "skill_id": _get("skill_id", ""),
            "selected_agent": _get("assigned_agent", ""),
            "routing_reason": _get("route_reason", ""),
            "task_type": _get("task_type", ""),
            "goal": _get("expected_output", ""),
            "context": _get("input_context", ""),
            "expected_output": _get("expected_output", ""),
            "allowed_actions": allowed_actions,
            "forbidden_actions": forbidden_actions,
            "allowed_tools": allowed_tools,
            "report_back_path": artifacts_dir,
            "timeout_seconds": timeout_val,
            "risk_level": risk_level,
            "requires_human_review": requires_human_review,
            "source": "ai-company-os-ceo",
            "created_at": str(time.time()),
        }

    # ── Result Polling ──

    def poll_results(
        self,
        work_order_id: str,
        timeout: int = DEFAULT_TIMEOUT,
        poll_interval: int = DEFAULT_POLL_INTERVAL,
    ) -> dict:
        """
        Poll for OpenClaw results by checking artifacts/<WO-ID>/result.json.

        This is the ONLY way results are detected — never guesses based on
        arbitrary new files.

        Args:
            work_order_id: The Work Order ID
            timeout: Max seconds to wait
            poll_interval: Seconds between polls

        Returns:
            {
                "status": "completed" | "failed" | "timeout" | "needs_review" | "not_available",
                "result": {...},   # parsed result.json (if completed)
                "message": "...",  # human-readable
                "errors": [...],   # validation errors (if needs_review)
            }
        """
        if not self.is_ready:
            return {
                "status": "not_available",
                "message": "OpenClaw directories not ready — cannot poll",
            }

        result_path = _result_json_path(work_order_id)
        start = time.time()

        while time.time() - start < timeout:
            if os.path.exists(result_path):
                return self._process_result_file(result_path)

            # Also check if the task card is still in inbox (not claimed)
            inbox_card = _task_card_path(work_order_id, INBOX_DIR)
            working_card = _task_card_path(work_order_id, WORKING_DIR)

            if os.path.exists(inbox_card):
                # Task is still in inbox — OpenClaw hasn't picked it up yet
                pass
            elif os.path.exists(working_card):
                # Task is in working — OpenClaw is processing
                pass
            else:
                # Task card doesn't exist in either place — not dispatched?
                pass

            time.sleep(poll_interval)

        return {
            "status": "timeout",
            "message": f"Result not found after {timeout}s polling",
        }

    def _process_result_file(self, result_path: str) -> dict:
        """Process a result.json file. Returns structured result."""
        try:
            raw = Path(result_path).read_text(encoding="utf-8")
            result = json.loads(raw)
        except json.JSONDecodeError as e:
            return {
                "status": "needs_review",
                "message": f"Malformed result.json: invalid JSON — {e}",
                "errors": [f"JSON parse error: {e}"],
            }
        except OSError as e:
            return {
                "status": "needs_review",
                "message": f"Cannot read result.json: {e}",
                "errors": [f"IO error: {e}"],
            }

        # Validate required fields
        errors = _validate_result_manifest(result)
        if errors:
            return {
                "status": "needs_review",
                "message": f"Result manifest missing required fields",
                "errors": errors,
                "result": result,
            }

        result_status = result.get("status", "completed")
        if result_status == "completed":
            return {
                "status": "completed",
                "result": result,
                "message": result.get("result_summary", ""),
            }
        elif result_status == "failed":
            return {
                "status": "failed",
                "result": result,
                "message": result.get("result_summary", "Task failed"),
            }
        else:
            return {
                "status": "needs_review",
                "result": result,
                "message": f"Unexpected result status: {result_status}",
                "errors": [f"Unknown status: {result_status}"],
            }

    def poll_results_once(self, work_order_id: str) -> dict:
        """
        Single check for results — no blocking loop.

        Args:
            work_order_id: The Work Order ID

        Returns:
            Same as poll_results() but returns immediately.
            If no result found, returns {"status": "not_found"}.
        """
        result_path = _result_json_path(work_order_id)
        if not os.path.exists(result_path):
            return {"status": "not_found"}
        return self._process_result_file(result_path)

    # ── Inbox/Working Management ──

    def get_dispatched_tasks(self) -> list[dict]:
        """List all task cards currently in the inbox (dispatched but not claimed)."""
        return self._list_task_cards(INBOX_DIR)

    def get_claimed_tasks(self) -> list[dict]:
        """List all task cards currently in the working directory (claimed, in progress)."""
        return self._list_task_cards(WORKING_DIR)

    def get_all_tasks(self) -> dict:
        """Get all tasks across all states."""
        return {
            "dispatched": self.get_dispatched_tasks(),
            "claimed": self.get_claimed_tasks(),
            "inbox_dir": INBOX_DIR,
            "working_dir": WORKING_DIR,
        }

    def _list_task_cards(self, directory: str) -> list[dict]:
        """List all .task.json files in a directory."""
        if not os.path.isdir(directory):
            return []
        cards = []
        for fname in sorted(os.listdir(directory)):
            if fname.endswith(".task.json"):
                try:
                    data = json.loads(
                        Path(os.path.join(directory, fname)).read_text(encoding="utf-8")
                    )
                    cards.append(data)
                except (json.JSONDecodeError, OSError):
                    pass
        return cards

    # ── Claim Simulation (for testing) ──

    def simulate_claim(self, work_order_id: str) -> dict:
        """
        Simulate OpenClaw claiming a task by moving it from inbox to working.
        Used for testing the lifecycle.
        """
        inbox_path = _task_card_path(work_order_id, INBOX_DIR)
        working_path = _task_card_path(work_order_id, WORKING_DIR)

        if not os.path.exists(inbox_path):
            return {
                "status": "failed",
                "message": f"Task card for {work_order_id} not found in inbox",
            }

        try:
            _ensure_dir(WORKING_DIR)
            os.rename(inbox_path, working_path)
            return {
                "status": "claimed_by_openclaw",
                "claimed_at": datetime.utcnow().isoformat() + "Z",
                "working_path": working_path,
            }
        except OSError as e:
            return {"status": "failed", "error": str(e)}

    def simulate_unclaim(self, work_order_id: str) -> dict:
        """Move a task card back from working to inbox (for testing)."""
        inbox_path = _task_card_path(work_order_id, INBOX_DIR)
        working_path = _task_card_path(work_order_id, WORKING_DIR)

        if not os.path.exists(working_path):
            return {
                "status": "failed",
                "message": f"No task card for {work_order_id} in working directory",
            }

        try:
            _ensure_dir(INBOX_DIR)
            os.rename(working_path, inbox_path)
            return {"status": "returned_to_inbox"}
        except OSError as e:
            return {"status": "failed", "error": str(e)}

    # ── Status Checks ──

    def get_task_card_path(self, work_order_id: str) -> Optional[str]:
        """Find the task card for a work order ID in inbox or working."""
        inbox_path = _task_card_path(work_order_id, INBOX_DIR)
        if os.path.exists(inbox_path):
            return inbox_path
        working_path = _task_card_path(work_order_id, WORKING_DIR)
        if os.path.exists(working_path):
            return working_path
        return None

    def get_task_state(self, work_order_id: str) -> str:
        """
        Determine the state of a task based on file system state.

        Returns: "dispatched" | "claimed" | "completed" | "not_found"
        """
        if os.path.exists(_result_json_path(work_order_id)):
            return "completed"
        if os.path.exists(_task_card_path(work_order_id, WORKING_DIR)):
            return "claimed"
        if os.path.exists(_task_card_path(work_order_id, INBOX_DIR)):
            return "dispatched"
        return "not_found"

    def cleanup_task(self, work_order_id: str) -> dict:
        """
        Clean up all task artifacts for a work order (inbox, working, artifacts).
        Called after successful backfill.
        """
        cleaned = []
        paths_to_remove = [
            _task_card_path(work_order_id, INBOX_DIR),
            _task_card_path(work_order_id, WORKING_DIR),
        ]
        for p in paths_to_remove:
            if os.path.exists(p):
                try:
                    os.remove(p)
                    cleaned.append(p)
                except OSError:
                    pass
        return {
            "status": "cleaned" if cleaned else "nothing_to_clean",
            "removed_paths": cleaned,
        }

    # ── Compatibility with v0.10 API ──

    def get_available_tasks(self) -> list[dict]:
        """Alias for get_dispatched_tasks() — v0.10 compatibility."""
        return self.get_dispatched_tasks()

    def poll_result(self, work_order_id: str, timeout: int = 300, poll_interval: int = 5) -> dict:
        """Alias for poll_results() with old signature — v0.10 compatibility."""
        return self.poll_results(
            work_order_id=work_order_id,
            timeout=timeout,
            poll_interval=poll_interval,
        )
