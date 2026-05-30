#!/usr/bin/env python3
"""Tests for scripts/work_order_control.py approve-dispatch."""
import json
import subprocess
import sys
import os
from datetime import datetime

SCRIPT = os.path.join(os.path.dirname(__file__), "work_order_control.py")
BASE_URL = "http://localhost:8001/api/v1"


def _api_post(path: str, data: dict) -> dict:
    import urllib.request, urllib.error
    url = f"{BASE_URL}{path}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, method="POST", data=body,
                                  headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def _api_get(path: str) -> dict:
    import urllib.request
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, method="GET")
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())


def _run_approve(wo_id: str) -> tuple[int, str]:
    result = subprocess.run(
        [sys.executable, SCRIPT, "approve-dispatch", wo_id],
        capture_output=True, text=True, timeout=30,
        cwd=os.path.join(os.path.dirname(__file__), ".."),
    )
    return result.returncode, result.stdout + result.stderr


class TestApproveDispatch:
    """Integration tests for approve-dispatch command."""

    def test_happy_path(self):
        """Approve-dispatch on a valid created WO → success."""
        # Create test WO with routable task_type + approval_required
        wo = _api_post("/work-orders", {
            "task_type": "profit_health_report",
            "risk_level": "medium",
            "approval_required": True,
            "input_context": "test happy path",
        })
        wo_id = wo["work_order_id"]
        assert wo["status"] == "created"

        rc, output = _run_approve(wo_id)
        assert rc == 0, f"Expected 0, got {rc}\n{output}"
        assert "APPROVE-DISPATCH COMPLETE" in output
        assert "created → routed → in_progress" in output

        # Verify WO state
        updated = _api_get(f"/work-orders/{wo_id}")
        assert updated["status"] == "in_progress"
        assert updated["approved_for_dispatch_at"] is not None
        assert updated["approval_id"] is not None
        assert updated["skill_id"] == "finance_analysis"

    def test_already_processed_rejected(self):
        """Approve-dispatch on in_progress WO → rejected."""
        rc, output = _run_approve("WO-9BD33732")
        assert rc != 0
        assert "status is 'in_progress'" in output or "Already processed" in output

    def test_not_found_rejected(self):
        """Approve-dispatch on non-existent WO → rejected."""
        rc, output = _run_approve("WO-NONEXIST-999")
        assert rc != 0
        assert "not found" in output

    def test_no_approval_required_rejected(self):
        """Approve-dispatch on WO with approval_required=false → rejected."""
        wo = _api_post("/work-orders", {
            "task_type": "research_summary",
            "risk_level": "low",
            "approval_required": False,
            "input_context": "test no approval",
        })
        wo_id = wo["work_order_id"]

        rc, output = _run_approve(wo_id)
        assert rc != 0
        assert "does not require approval" in output

    def test_unknown_task_type_needs_review(self):
        """Approve-dispatch on WO with unmatchable task_type → route fails."""
        wo = _api_post("/work-orders", {
            "task_type": "unknown_type_xyz",
            "risk_level": "medium",
            "approval_required": True,
            "input_context": "test unknown task type",
        })
        wo_id = wo["work_order_id"]

        rc, output = _run_approve(wo_id)
        assert rc != 0
        assert "needs_review" in output or "no matching skill" in output or "No matching" in output

    def test_duplicate_approve_rejected(self):
        """Already-approved WO → rejected at step 2 (before route)."""
        wo = _api_post("/work-orders", {
            "task_type": "profit_health_report",
            "risk_level": "medium",
            "approval_required": True,
            "input_context": "test duplicate approve",
        })
        wo_id = wo["work_order_id"]

        # First approve should succeed
        rc1, out1 = _run_approve(wo_id)
        assert rc1 == 0, f"First approve failed:\n{out1}"

        # Second approve should fail
        rc2, out2 = _run_approve(wo_id)
        assert rc2 != 0
        assert "already approved" in out2 or "status is 'routed'" in out2 or "in_progress" in out2
