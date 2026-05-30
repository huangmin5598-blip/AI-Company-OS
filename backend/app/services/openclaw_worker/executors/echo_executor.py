"""
EchoExecutor — echo input context back as output.

Simplest executor. No LLM, no external calls. Used for testing the
inbox/outbox/callback protocol without any model dependency.
"""
import os
from datetime import datetime, timezone

from .base import TaskExecutor, ExecutionResult


class EchoExecutor(TaskExecutor):
    name = "echo"
    executor_type = "echo"
    native_openclaw = False
    runtime_backend = "rule_based"

    def can_handle(self, task_card: dict) -> bool:
        task_type = task_card.get("task_type", "")
        return task_type in ("echo_test", "echo")

    def execute(self, task_card: dict) -> ExecutionResult:
        started_at = datetime.now(timezone.utc).isoformat()

        goal = task_card.get("goal", "")
        context = task_card.get("context", "")
        expected_output = task_card.get("expected_output", "")
        report_back_path = task_card.get("report_back_path", "")

        # Build output
        output_lines = [
            f"# Echo Output",
            f"",
            f"**Task:** {task_card.get('work_order_id', '')}",
            f"**Goal:** {goal}",
            f"**Generated at:** {started_at}",
            f"",
            f"## Echo Response",
            f"",
            f"{context}",
        ]
        output_text = "\n".join(output_lines)

        # Write output file if path available
        artifacts = []
        if report_back_path:
            try:
                os.makedirs(report_back_path, exist_ok=True)
                output_file = os.path.join(report_back_path, expected_output or "echo_output.md")
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(output_text)
                artifacts.append({
                    "name": expected_output or "echo_output.md",
                    "path": output_file,
                    "type": "markdown",
                })
            except OSError as e:
                pass

        finished_at = datetime.now(timezone.utc).isoformat()
        duration = (
            datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
            - datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        ).total_seconds() * 1000

        return ExecutionResult(
            status="completed",
            result_summary=f"Echo task completed: echoed {len(context)} chars of context",
            output_text=output_text,
            executor_type=self.executor_type,
            executor_name=self.name,
            native_openclaw=self.native_openclaw,
            runtime_backend=self.runtime_backend,
            artifacts=artifacts,
            duration_ms=int(duration),
            started_at=started_at,
            finished_at=finished_at,
        )
