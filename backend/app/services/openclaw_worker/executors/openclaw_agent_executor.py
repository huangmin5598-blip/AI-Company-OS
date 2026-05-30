"""
OpenClawAgentExecutor — calls `openclaw agent --json` to execute tasks.

This is the REAL OpenClaw native execution path. It invokes OpenClaw agents
(which run on cloud models like MiniMax-M2.5) with full tool access
(Feishu, GitHub, Tavily, etc.) and returns structured JSON results.

Usage:
    openclaw agent --agent <name> --message "<prompt>" --json

Security:
  - Uses subprocess with arg array (no shell injection)
  - Timeout enforced
  - Non-JSON stdout → error
  - Non-zero exit code → error
"""
import json
import os
import subprocess
from datetime import datetime, timezone

from .base import TaskExecutor, ExecutionResult, extract_inferred_tools


# Agent mapping: task_type / capability → OpenClaw agent name
DEFAULT_AGENT_MAP = {
    "research": "research-agent",
    "research_summary": "research-agent",
    "file_analysis": "research-agent",
    "customer_response": "content-manager",
    "customer_support": "content-manager",
    "finance_analysis": "finance-analyst",
    "amazon_seller_analysis": "amazon-seller",
    "content_creation": "content-manager",
    "report_generation": "research-agent",
    "read_context_and_write_summary": "research-agent",
}

# Default agent when no mapping found
DEFAULT_AGENT = "main"

# Timeout for openclaw agent command (seconds)
OPENCLAW_TIMEOUT = 120

# Path to openclaw binary
OPENCLAW_BIN = "/opt/homebrew/bin/openclaw"


def _resolve_agent(task_card: dict) -> str:
    """Determine which OpenClaw agent to use for this task."""
    # 1. Task card can explicitly specify
    executor_config = task_card.get("executor_config", {})
    if isinstance(executor_config, dict):
        specified = executor_config.get("openclaw_agent", "")
        if specified:
            return specified

    # 2. Map by task_type
    task_type = task_card.get("task_type", "")
    if task_type in DEFAULT_AGENT_MAP:
        return DEFAULT_AGENT_MAP[task_type]

    # 3. Fallback to main
    return DEFAULT_AGENT


def _build_prompt(task_card: dict) -> str:
    """Build the message prompt for the OpenClaw agent."""
    goal = task_card.get("goal", "")
    context = task_card.get("context", "")
    expected_output = task_card.get("expected_output", "")
    task_type = task_card.get("task_type", "")
    allowed_actions = task_card.get("allowed_actions", [])
    forbidden_actions = task_card.get("forbidden_actions", [])

    lines = [
        f"You are executing a task for AI Company OS.",
        f"",
        f"## Task Type: {task_type}",
        f"## Goal",
        f"{goal}",
        f"",
    ]
    if context:
        lines.extend([f"## Context / Input", f"{context}", f""])
    if expected_output:
        lines.extend([f"## Expected Output", f"Produce: {expected_output}", f""])
    if allowed_actions:
        lines.extend([f"## Allowed Actions", f"Only do: {', '.join(allowed_actions)}", f""])
    if forbidden_actions:
        lines.extend([f"## Forbidden Actions", f"Never: {', '.join(forbidden_actions)}", f""])

    lines.extend([
        f"## Safety Rules",
        f"- You are executing in an isolated task context.",
        f"- Do not modify code, send emails, deploy, or make payments.",
        f"- Output ONLY the result content — no extra commentary.",
        f"- If the task is a customer response, produce a DRAFT only.",
    ])
    return "\n".join(lines)


class OpenClawAgentExecutor(TaskExecutor):
    name = "openclaw_agent"
    executor_type = "openclaw_agent"
    native_openclaw = True
    runtime_backend = "openclaw_cli"

    def can_handle(self, task_card: dict) -> bool:
        """Can handle any non-echo task (falls back to local_llm if openclaw fails)."""
        task_type = task_card.get("task_type", "")
        return task_type not in ("echo_test", "echo")

    def execute(self, task_card: dict) -> ExecutionResult:
        started_at = datetime.now(timezone.utc).isoformat()

        agent_name = _resolve_agent(task_card)
        prompt = _build_prompt(task_card)
        report_back_path = task_card.get("report_back_path", "")
        expected_output = task_card.get("expected_output", "output.md")

        # Build command with arg array (no shell injection)
        cmd = [
            OPENCLAW_BIN,
            "agent",
            "--agent", agent_name,
            "--message", prompt,
            "--json",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=OPENCLAW_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            finished_at = datetime.now(timezone.utc).isoformat()
            return ExecutionResult(
                status="failed",
                result_summary=f"OpenClaw agent '{agent_name}' timed out after {OPENCLAW_TIMEOUT}s",
                output_text="",
                executor_type=self.executor_type,
                executor_name=self.name,
                native_openclaw=self.native_openclaw,
                runtime_backend=self.runtime_backend,
                openclaw_agent=agent_name,
                errors=[f"Timeout: {OPENCLAW_TIMEOUT}s exceeded"],
                error_message=f"OpenClaw agent timed out",
                started_at=started_at,
                finished_at=finished_at,
            )
        except FileNotFoundError:
            finished_at = datetime.now(timezone.utc).isoformat()
            return ExecutionResult(
                status="needs_review",
                result_summary=f"OpenClaw CLI not found at {OPENCLAW_BIN}",
                output_text="",
                executor_type=self.executor_type,
                executor_name=self.name,
                native_openclaw=self.native_openclaw,
                runtime_backend=self.runtime_backend,
                openclaw_agent=agent_name,
                errors=[f"CLI not found: {OPENCLAW_BIN}"],
                error_message="OpenClaw CLI unavailable",
                started_at=started_at,
                finished_at=finished_at,
            )

        finished_at = datetime.now(timezone.utc).isoformat()
        duration = (
            datetime.fromisoformat(finished_at.replace("Z", "+00:00"))
            - datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        ).total_seconds() * 1000

        # Non-zero exit code
        if result.returncode != 0:
            stderr_short = (result.stderr or "")[:500]
            return ExecutionResult(
                status="failed",
                result_summary=f"OpenClaw agent '{agent_name}' exited with code {result.returncode}",
                output_text=result.stdout or "",
                executor_type=self.executor_type,
                executor_name=self.name,
                native_openclaw=self.native_openclaw,
                runtime_backend=self.runtime_backend,
                openclaw_agent=agent_name,
                errors=[f"Exit code: {result.returncode}", stderr_short],
                error_message=stderr_short,
                duration_ms=int(duration),
                started_at=started_at,
                finished_at=finished_at,
            )

        # Parse JSON output
        try:
            agent_result = json.loads(result.stdout)
        except (json.JSONDecodeError, ValueError) as e:
            return ExecutionResult(
                status="needs_review",
                result_summary=f"OpenClaw agent returned non-JSON output",
                output_text=result.stdout[:2000] or "",
                executor_type=self.executor_type,
                executor_name=self.name,
                native_openclaw=self.native_openclaw,
                runtime_backend=self.runtime_backend,
                openclaw_agent=agent_name,
                errors=[f"JSON parse error: {e}", result.stdout[:500]],
                error_message="Non-JSON response from OpenClaw agent",
                duration_ms=int(duration),
                started_at=started_at,
                finished_at=finished_at,
            )

        # Extract response text
        payloads = agent_result.get("result", {}).get("payloads", [])
        output_text = ""
        for p in payloads:
            text = p.get("text", "")
            if text:
                output_text += text + "\n"
        output_text = output_text.strip()

        # If no text from payloads, fall back to full agent response
        if not output_text:
            output_text = json.dumps(agent_result.get("result", {}), ensure_ascii=False, indent=2)

        # Extract metadata
        meta = agent_result.get("result", {}).get("meta", {})
        agent_meta = meta.get("agentMeta", {})
        usage = agent_meta.get("usage", {})
        status = agent_result.get("status", "unknown")

        # Map OpenClaw status
        if status == "ok":
            result_status = "completed"
        elif status == "error":
            result_status = "failed"
        else:
            result_status = "needs_review"

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

        run_id = agent_result.get("runId", "")

        # Extract tool evidence from agent output text (v0.14.2)
        inferred = extract_inferred_tools(output_text)
        tool_calls_detected = len(inferred) > 0
        tool_call_summary = ", ".join(inferred) if inferred else ""
        tool_call_evidence_source = "agent_output_text" if tool_calls_detected else ""

        return ExecutionResult(
            status=result_status,
            result_summary=f"OpenClaw agent '{agent_name}' completed ({agent_meta.get('model', '?')})",
            output_text=output_text,
            executor_type=self.executor_type,
            executor_name=self.name,
            native_openclaw=self.native_openclaw,
            runtime_backend=self.runtime_backend,
            openclaw_agent=agent_name,
            model_provider=agent_meta.get("provider", ""),
            model_name=agent_meta.get("model", ""),
            token_usage={
                "input_tokens": usage.get("input", 0),
                "output_tokens": usage.get("output", 0),
                "cache_read_tokens": usage.get("cacheRead", 0),
                "total_tokens": usage.get("total", 0),
            },
            duration_ms=int(duration),
            openclaw_run_id=run_id,
            openclaw_stop_reason=agent_result.get("result", {}).get("meta", {}).get("stopReason", ""),
            artifacts=artifacts,
            # Tool evidence (v0.14.2)
            tool_calls_detected=tool_calls_detected,
            tool_call_summary=tool_call_summary,
            inferred_tools=inferred,
            tool_call_evidence_source=tool_call_evidence_source,
            tool_trace_available=False,
            started_at=started_at,
            finished_at=finished_at,
        )
