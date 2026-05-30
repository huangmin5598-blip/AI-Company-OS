"""
LocalLLMExecutor — executes tasks using local Ollama LLM.

Fallback executor when OpenClaw agent is unavailable.
Uses deepseek-r1:8b via Ollama HTTP API.
"""
import json
import os
import urllib.request
from datetime import datetime, timezone

from .base import TaskExecutor, ExecutionResult


OLLAMA_URL = "http://localhost:11434/api/generate"
DEFAULT_MODEL = "deepseek-r1:8b"
LLM_TIMEOUT = 60


def _call_ollama(prompt: str, model: str = DEFAULT_MODEL) -> dict:
    """Call Ollama generate API. Returns parsed JSON response."""
    body = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7},
    }).encode()

    req = urllib.request.Request(OLLAMA_URL, data=body, method="POST")
    req.add_header("Content-Type", "application/json")

    try:
        with urllib.request.urlopen(req, timeout=LLM_TIMEOUT) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        return {"error": str(e)}


class LocalLLMExecutor(TaskExecutor):
    name = "local_llm"
    executor_type = "local_llm"
    native_openclaw = False
    runtime_backend = "ollama"

    def can_handle(self, task_card: dict) -> bool:
        task_type = task_card.get("task_type", "")
        # Can handle any task that's not echo
        return task_type not in ("echo_test", "echo")

    def _build_prompt(self, task_card: dict) -> str:
        goal = task_card.get("goal", "")
        context = task_card.get("context", "")
        expected_output = task_card.get("expected_output", "")
        task_type = task_card.get("task_type", "")

        lines = [
            f"You are an AI assistant executing a task for AI Company OS.",
            f"",
            f"## Task Type: {task_type}",
            f"## Goal",
            f"{goal}",
            f"",
        ]
        if context:
            lines.extend([f"## Context", f"{context}", f""])
        if expected_output:
            lines.extend([f"## Expected Output", f"Generate: {expected_output}", f""])

        lines.extend([
            f"## Instructions",
            f"1. Read the task goal and context carefully.",
            f"2. Execute the task thoroughly.",
            f"3. Format the output clearly in markdown.",
            f"4. Output ONLY the result content — no extra commentary.",
        ])
        return "\n".join(lines)

    def execute(self, task_card: dict) -> ExecutionResult:
        started_at = datetime.now(timezone.utc).isoformat()

        prompt = self._build_prompt(task_card)
        report_back_path = task_card.get("report_back_path", "")
        expected_output = task_card.get("expected_output", "output.md")

        ollama_result = _call_ollama(prompt)

        if "error" in ollama_result:
            finished_at = datetime.now(timezone.utc).isoformat()
            return ExecutionResult(
                status="needs_review",
                result_summary=f"Local LLM unavailable: {ollama_result['error'][:100]}",
                output_text="",
                executor_type=self.executor_type,
                executor_name=self.name,
                native_openclaw=self.native_openclaw,
                runtime_backend=self.runtime_backend,
                model_name=DEFAULT_MODEL,
                errors=[ollama_result["error"]],
                error_message=ollama_result["error"],
                started_at=started_at,
                finished_at=finished_at,
            )

        output_text = ollama_result.get("response", "")
        model_name = ollama_result.get("model", DEFAULT_MODEL)
        token_usage = {
            "input_tokens": ollama_result.get("prompt_eval_count", 0),
            "output_tokens": ollama_result.get("eval_count", 0),
            "total_tokens": (ollama_result.get("prompt_eval_count", 0)
                             + ollama_result.get("eval_count", 0)),
        }
        finished_at = datetime.now(timezone.utc).isoformat()
        duration = (
            datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
            - datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        ).total_seconds() * 1000

        # Write output file
        artifacts = []
        if report_back_path and output_text:
            try:
                os.makedirs(report_back_path, exist_ok=True)
                output_file = os.path.join(report_back_path, expected_output)
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(output_text)
                artifacts.append({
                    "name": expected_output,
                    "path": output_file,
                    "type": "markdown",
                })
            except OSError as e:
                pass

        return ExecutionResult(
            status="completed",
            result_summary=f"Local LLM task completed via {model_name}",
            output_text=output_text,
            executor_type=self.executor_type,
            executor_name=self.name,
            native_openclaw=self.native_openclaw,
            runtime_backend=self.runtime_backend,
            model_name=model_name,
            token_usage=token_usage,
            artifacts=artifacts,
            duration_ms=int(duration),
            started_at=started_at,
            finished_at=finished_at,
        )
