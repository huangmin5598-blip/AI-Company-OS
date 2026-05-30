"""
Executor Factory — creates the right executor based on config + task card.

Feature flag:
  OPENCLAW_EXECUTOR_MODE = openclaw_native | local_llm | echo | auto

  auto mode: tries openclaw_agent, falls back to local_llm, then needs_review
"""
import os

from .base import TaskExecutor, ExecutionResult
from .echo_executor import EchoExecutor
from .local_llm_executor import LocalLLMExecutor
from .openclaw_agent_executor import OpenClawAgentExecutor


# Available executors
_EXECUTORS: list[TaskExecutor] = [
    OpenClawAgentExecutor(),
    LocalLLMExecutor(),
    EchoExecutor(),
]


def get_mode() -> str:
    """Get the configured executor mode from env or default."""
    return os.environ.get("OPENCLAW_EXECUTOR_MODE", "auto").strip().lower()


def get_executor(task_card: dict) -> TaskExecutor:
    """
    Select the best executor for the given task card based on mode.

    In auto mode, prefer OpenClaw agent with fallback.
    """
    mode = get_mode()
    task_type = task_card.get("task_type", "")

    # Direct mode selection
    if mode == "echo":
        return EchoExecutor()
    elif mode == "local_llm":
        return LocalLLMExecutor()
    elif mode == "openclaw_native":
        return OpenClawAgentExecutor()

    # auto mode: find the first executor that can handle the task
    # Priority: OpenClawAgent → LocalLLM → Echo
    for executor in _EXECUTORS:
        if executor.can_handle(task_card):
            return executor

    # Fallback: EchoExecutor (can handle echo_test)
    return EchoExecutor()


def execute_safe(task_card: dict) -> ExecutionResult:
    """
    Execute a task card with fallback chain.

    auto mode:
      1. Try OpenClawAgentExecutor
      2. If failed → try LocalLLMExecutor
      3. If failed → needs_review

    openclaw_native mode:
      1. Try OpenClawAgentExecutor
      2. If failed → needs_review

    local_llm / echo mode:
      1. Try the selected executor directly
    """
    mode = get_mode()
    task_type = task_card.get("task_type", "")

    # Echo tasks always use EchoExecutor (fast path)
    if task_type in ("echo_test", "echo"):
        return EchoExecutor().execute(task_card)

    if mode == "openclaw_native":
        # Try only OpenClaw agent
        result = OpenClawAgentExecutor().execute(task_card)
        if result.status == "failed" or (result.status == "needs_review" and not result.output_text):
            return result
        return result

    if mode == "local_llm":
        return LocalLLMExecutor().execute(task_card)

    # auto mode: try OpenClaw first, fallback to local_llm
    openclaw_result = OpenClawAgentExecutor().execute(task_card)

    # If OpenClaw succeeded, return it
    if openclaw_result.status == "completed":
        return openclaw_result

    # If OpenClaw failed but produced output, return with note
    if openclaw_result.output_text:
        return openclaw_result

    # Fallback to local LLM
    local_result = LocalLLMExecutor().execute(task_card)
    if local_result.status == "completed":
        # Note that this was a fallback
        local_result.result_summary = (
            f"[Fallback from OpenClaw] {local_result.result_summary}"
        )
        return local_result

    # Both failed
    return ExecutionResult(
        status="needs_review",
        result_summary=(
            f"OpenClaw agent failed, local LLM also failed. "
            f"OpenClaw: {openclaw_result.error_message or 'no output'} | "
            f"Local: {local_result.error_message or 'no output'}"
        ),
        output_text=openclaw_result.output_text or local_result.output_text,
        errors=[*openclaw_result.errors, *local_result.errors],
        error_message="Both OpenClaw and local LLM failed",
    )
