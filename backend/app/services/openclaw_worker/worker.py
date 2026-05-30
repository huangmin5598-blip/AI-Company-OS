# @PRODUCT Service — v0.14 OpenClaw Worker — Worker Logic
"""
OpenClaw Worker — shared logic for processing inbox tasks.

This module contains the core worker logic that can be used both by:
- bin/openclaw_worker.py (standalone CLI)
- Cron/scheduled jobs
- Programmatic calls from AI Company OS
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from app.services.openclaw_worker.executors.factory import execute_safe, get_mode
from app.services.openclaw_worker.executors.base import ExecutionResult

# Paths (same as OpenClawBridge)
BASE_OPENCLAW_DIR = os.path.expanduser("~/.ai-company-os/openclaw/")
OPENCLAW_INBOX = os.path.join(BASE_OPENCLAW_DIR, "inbox")
OPENCLAW_WORKING = os.path.join(BASE_OPENCLAW_DIR, "working")
BASE_ARTIFACTS_DIR = os.path.expanduser("~/.ai-company-os/artifacts")


def _now_iso() -> str:
    return datetime.utcnow().isoformat() + "Z"


def _artifact_dir(wo_id: str) -> str:
    return os.path.join(BASE_ARTIFACTS_DIR, wo_id)


def _ensure_dir(path: str) -> bool:
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError:
        return False


def find_pending_tasks() -> list[dict]:
    """
    Scan inbox/ for pending task cards.

    Returns a list of parsed task card dicts, sorted by creation time (oldest first).
    """
    if not os.path.isdir(OPENCLAW_INBOX):
        return []
    cards = []
    for fname in sorted(os.listdir(OPENCLAW_INBOX)):
        if not fname.endswith(".task.json"):
            continue
        fpath = os.path.join(OPENCLAW_INBOX, fname)
        try:
            card = json.loads(Path(fpath).read_text(encoding="utf-8"))
            wo_id = card.get("work_order_id", "")
            # Extract timestamp from filename (lexicographic sort = time order)
            cards.append({"path": fpath, "card": card, "work_order_id": wo_id})
        except (json.JSONDecodeError, OSError):
            pass
    return cards


def claim_task(card_info: dict) -> Optional[str]:
    """
    Claim a task by moving it from inbox/ to working/.

    Args:
        card_info: dict with 'path' and 'work_order_id'

    Returns:
        The working path if successful, None if failed.
    """
    inbox_path = card_info["path"]
    wo_id = card_info.get("work_order_id", "")
    working_path = os.path.join(OPENCLAW_WORKING, os.path.basename(inbox_path))

    if not os.path.exists(inbox_path):
        return None

    try:
        _ensure_dir(OPENCLAW_WORKING)
        os.rename(inbox_path, working_path)
        return working_path
    except OSError:
        return None


def process_task(card_info: dict, call_backend: bool = False, backend_url: str = "") -> dict:
    """
    Process a single task card: claim → execute → write result.json.

    Args:
        card_info: dict from find_pending_tasks()
        call_backend: If True, call the callback API after writing result.json
        backend_url: Base URL of the AI Company OS backend

    Returns:
        dict with keys: status, work_order_id, result_path, execution_result
    """
    wo_id = card_info["work_order_id"]
    card = card_info["card"]

    print(f"  Worker: Processing {wo_id} ({card.get('task_type', '?')})")

    # 1. Claim
    working_path = claim_task(card_info)
    if not working_path:
        return {
            "status": "failed",
            "work_order_id": wo_id,
            "error": "Failed to claim task (inbox card not found or not movable)",
        }
    print(f"  Worker: Claimed → working/")

    # 2. Execute (via executor factory)
    mode = get_mode()
    print(f"  Worker: Executing via {mode} mode...")
    result = execute_safe(card)
    result_manifest = result.to_manifest()
    print(f"  Worker: Executed → status={result_manifest['status']}, "
          f"confidence={result_manifest['confidence']}, "
          f"executor={result_manifest['executor_type']}")

    # 3. Write result.json
    artifacts_dir = _artifact_dir(wo_id)
    _ensure_dir(artifacts_dir)
    result_path = os.path.join(artifacts_dir, "result.json")

    # Add executor + routing metadata
    result_manifest["claimed_at"] = _now_iso()
    result_manifest["finished_at"] = _now_iso()

    # v0.15: Add routing metadata from task card
    result_manifest["skill_id"] = card.get("skill_id", "")
    result_manifest["selected_agent"] = card.get("selected_agent", "")
    result_manifest["routing_reason"] = card.get("routing_reason", "")

    Path(result_path).write_text(
        json.dumps(result_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"  Worker: result.json written → {result_path}")

    # 4. Optionally call callback API
    if call_backend and backend_url:
        try:
            import urllib.request
            callback_url = f"{backend_url}/api/v1/work-orders/{wo_id}/openclaw-callback"
            callback_body = {
                "status": result_manifest["status"],
                "result_summary": result_manifest["result_summary"],
                "output_path": artifacts_dir,
                "artifacts": result_manifest["artifacts"],
                "confidence": result_manifest["confidence"],
                "metadata": {
                    "runtime": "openclaw",
                    "worker": "openclaw-worker-lite",
                    "executor_type": result_manifest.get("executor_type", "unknown"),
                    "executor_name": result_manifest.get("executor_name", ""),
                    "native_openclaw": result_manifest.get("native_openclaw", False),
                    "openclaw_agent": result_manifest.get("openclaw_agent", ""),
                    "model_name": result_manifest.get("model_name", ""),
                    "model_provider": result_manifest.get("model_provider", ""),
                    "token_usage": result_manifest.get("token_usage", {}),
                    "duration_ms": result_manifest.get("duration_ms", 0),
                    "openclaw_run_id": result_manifest.get("openclaw_run_id", ""),
                    # v0.15: routing metadata
                    "skill_id": result_manifest.get("skill_id", ""),
                    "selected_agent": result_manifest.get("selected_agent", ""),
                    "routing_reason": result_manifest.get("routing_reason", ""),
                },
                "completed_at": _now_iso(),
                "api_key": os.environ.get("OPENCLAW_CALLBACK_API_KEY", "oc-test-key-change-me"),
            }
            body = json.dumps(callback_body).encode()
            req = urllib.request.Request(callback_url, data=body, method="POST")
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=10) as resp:
                cb_result = json.loads(resp.read().decode())
                print(f"  Worker: Callback API → {cb_result.get('status', '?')}")
        except Exception as e:
            print(f"  Worker: Callback API failed → {e}")

    return {
        "status": result_manifest["status"],
        "work_order_id": wo_id,
        "result_path": result_path,
        "execution_result": result_manifest,
    }


def process_all_pending(call_backend: bool = False, backend_url: str = "") -> list[dict]:
    """
    Process all pending tasks in inbox/.

    Returns list of process_task results.
    """
    pending = find_pending_tasks()
    if not pending:
        print("  Worker: No pending tasks in inbox")
        return []

    print(f"  Worker: Found {len(pending)} pending task(s)")
    results = []
    for card_info in pending:
        result = process_task(card_info, call_backend=call_backend, backend_url=backend_url)
        results.append(result)
    return results
