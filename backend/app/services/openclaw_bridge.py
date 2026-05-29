# @PRODUCT Service — v0.10 OpenClaw Bridge (最小版)
"""
OpenClaw Bridge — 生成 task card 并写入目录，轮询结果。

架构：
  WorkOrderExecutor → OpenClawBridge → task card JSON → ~/.openclaw/ceo-tasks/
                                    ← poll ~/.openclaw/ceo-results/ ← OpenClaw Agent

降级策略：
  如果 OpenClaw 未运行或目录不可写，生成 card 但不发送，不阻塞 CEO 流程。
"""
import json
import os
import time
import uuid
from pathlib import Path
from typing import Optional


# 默认路径（可与 config.py 同步）
DEFAULT_TASKS_DIR = os.path.expanduser("~/.openclaw/ceo-tasks/")
DEFAULT_RESULTS_DIR = os.path.expanduser("~/.openclaw/ceo-results/")


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


class OpenClawBridge:
    """
    最小版 OpenClaw Bridge。

    生成 task card → 写入 ceo-tasks/ 目录 → 轮询 ceo-results/ 获取结果。
    """

    def __init__(
        self,
        tasks_dir: str = DEFAULT_TASKS_DIR,
        results_dir: str = DEFAULT_RESULTS_DIR,
    ):
        self.tasks_dir = tasks_dir
        self.results_dir = results_dir
        self._ready = False

    @property
    def is_ready(self) -> bool:
        """Check if both directories are writable."""
        if not self._ready:
            self._ready = (
                _ensure_dir(self.tasks_dir) and _ensure_dir(self.results_dir)
            )
        return self._ready

    def create_task_card(self, work_order: "WorkOrder") -> dict:
        """
        为 Work Order 生成 task card JSON 并写入 ceo-tasks/ 目录。

        Args:
            work_order: WorkOrder ORM 对象或 to_dict() 后的字典

        Returns:
            {
                "card_path": str,        # 写入的完整路径
                "card_id": str,          # task card ID
                "status": "created",
                "fallback": bool,        # True 表示降级（目录不可写）
            }

            或 {"error": str, "status": "failed"}
        """
        # Get work order ID
        wo_id = (
            work_order.work_order_id
            if hasattr(work_order, "work_order_id")
            else work_order.get("work_order_id", "")
        )

        card_id = f"CEO-TASK-{uuid.uuid4().hex[:8].upper()}"

        card = {
            "task_id": wo_id,
            "card_id": card_id,
            "source": "ai-company-os-ceo",
            "goal": (
                work_order.expected_output
                if hasattr(work_order, "expected_output")
                else work_order.get("expected_output", "")
            ),
            "context": (
                work_order.input_context
                if hasattr(work_order, "input_context")
                else work_order.get("input_context", "")
            ),
            "report_back_path": os.path.join(
                self.results_dir, f"{wo_id}.json"
            ),
            "task_type": (
                work_order.task_type
                if hasattr(work_order, "task_type")
                else work_order.get("task_type", "")
            ),
            "skill_id": (
                work_order.skill_id
                if hasattr(work_order, "skill_id")
                else work_order.get("skill_id", "")
            ),
            "risk_level": (
                work_order.risk_level
                if hasattr(work_order, "risk_level")
                else work_order.get("risk_level", "low")
            ),
            "created_at": str(time.time()),
        }

        if not self.is_ready:
            return {
                "status": "created",
                "card_id": card_id,
                "card_path": "",
                "fallback": True,
                "message": "OpenClaw directories not writable — card generated but not saved",
                "card": card,
            }

        card_path = os.path.join(self.tasks_dir, f"{wo_id}.json")
        try:
            Path(card_path).write_text(
                json.dumps(card, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            return {
                "status": "created",
                "card_id": card_id,
                "card_path": card_path,
                "fallback": False,
            }
        except OSError as e:
            return {
                "status": "failed",
                "error": f"Failed to write task card: {e}",
                "card_id": card_id,
                "fallback": True,
                "card": card,
            }

    def poll_result(
        self, work_order_id: str, timeout: int = 300, poll_interval: int = 5
    ) -> dict:
        """
        轮询结果路径直到超时或找到结果。

        Args:
            work_order_id: Work Order ID
            timeout: 最大等待秒数（默认 300s = 5min）
            poll_interval: 轮询间隔秒数

        Returns:
            {"status": "completed", "result": {...}} 或
            {"status": "timeout", "message": "..."} 或
            {"status": "not_available", "message": "..."}
        """
        result_path = os.path.join(self.results_dir, f"{work_order_id}.json")

        if not self.is_ready:
            return {
                "status": "not_available",
                "message": "OpenClaw results directory not writable — cannot poll",
            }

        start = time.time()
        while time.time() - start < timeout:
            if os.path.exists(result_path):
                try:
                    result = json.loads(Path(result_path).read_text(encoding="utf-8"))
                    return {"status": "completed", "result": result}
                except (json.JSONDecodeError, OSError) as e:
                    return {"status": "error", "error": str(e)}
            time.sleep(poll_interval)

        return {
            "status": "timeout",
            "message": f"Result not found after {timeout}s polling",
        }

    def get_available_tasks(self) -> list[dict]:
        """List all pending task cards in ceo-tasks/ directory."""
        if not os.path.isdir(self.tasks_dir):
            return []
        cards = []
        for fname in sorted(os.listdir(self.tasks_dir)):
            if fname.endswith(".json"):
                try:
                    data = json.loads(
                        Path(os.path.join(self.tasks_dir, fname)).read_text(
                            encoding="utf-8"
                        )
                    )
                    cards.append(data)
                except (json.JSONDecodeError, OSError):
                    pass
        return cards
