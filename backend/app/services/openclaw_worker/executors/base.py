"""
TaskExecutor Base -- interface + data classes for v0.14.2 executor abstraction.

All executors implement:
  def can_handle(task_card: dict) -> bool
  def execute(task_card: dict) -> ExecutionResult

ExecutionResult includes full provenance + tool evidence for Result Manifest.
"""
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional


# Known tool names used by OpenClaw agents (for inferred_tools extraction)
# OpenClaw CLI JSON does NOT return structured tool call traces.
# These are used to heuristically detect tool usage from agent output text.
KNOWN_TOOLS = {
    "tavily_search", "tavily_extract", "tavily_crawl", "tavily_map", "tavily_research",
    "web_search", "web_fetch",
    "read", "write", "edit", "exec", "process",
    "browser",
    "feishu_doc", "feishu_chat", "feishu_wiki", "feishu_drive",
    "feishu_bitable_get_meta", "feishu_bitable_list_fields",
    "feishu_bitable_list_records", "feishu_bitable_get_record",
    "feishu_bitable_create_record", "feishu_bitable_update_record",
    "memory_search", "memory_get",
    "sessions_list", "sessions_history", "sessions_send", "sessions_spawn",
    "subagents", "session_status",
    "cron", "message", "tts", "gateway", "canvas", "nodes",
}


def extract_inferred_tools(output_text: str) -> list[str]:
    """Extract tool names from agent output text (heuristic, not from CLI trace).

    OpenClaw CLI JSON does NOT return structured tool call traces.
    This method infers tool usage by pattern-matching known tool names
    in the agent's natural language response.

    Returns:
        List of inferred tool names mentioned in the output text.
    """
    if not output_text:
        return []
    text_lower = output_text.lower()
    found = set()
    for tool in KNOWN_TOOLS:
        if tool in text_lower:
            found.add(tool)
    return sorted(found)


@dataclass
class ExecutionResult:
    """Standard result across all executor types."""

    # Core result
    status: str  # "completed" | "failed" | "needs_review"
    result_summary: str
    output_text: str = ""

    # Provenance (v0.14.1)
    executor_type: str = "unknown"  # "echo" | "local_llm" | "openclaw_agent"
    executor_name: str = "UnknownExecutor"
    native_openclaw: bool = False
    runtime_backend: str = ""

    # OpenClaw-specific (when executor_type = openclaw_agent)
    openclaw_agent: str = ""
    model_provider: str = ""
    model_name: str = ""
    token_usage: Optional[dict] = None
    duration_ms: Optional[int] = None
    openclaw_run_id: str = ""
    openclaw_stop_reason: str = ""

    # Tool evidence (v0.14.2 -- inferred from agent output text, not structured CLI trace)
    # OpenClaw CLI JSON does NOT return structured tool call traces.
    tool_calls_detected: bool = False
    tool_call_summary: str = ""
    inferred_tools: list = field(default_factory=list)
    tool_call_evidence_source: str = ""
    tool_trace_available: bool = False

    # Artifacts
    artifacts: list = field(default_factory=list)

    # Errors
    errors: list = field(default_factory=list)
    error_message: str = ""

    # Timestamps
    started_at: str = ""
    finished_at: str = ""

    def __post_init__(self):
        if not self.started_at:
            self.started_at = datetime.now(timezone.utc).isoformat()
        if not self.finished_at:
            self.finished_at = datetime.now(timezone.utc).isoformat()

    def to_manifest(self) -> dict:
        """Convert to Result Manifest dict (ready for result.json)."""
        return {
            "status": self.status,
            "result_summary": self.result_summary,
            "output_text": self.output_text,
            "artifacts": self.artifacts,
            "errors": self.errors,
            "error_message": self.error_message,
            "confidence": 1.0 if self.status == "completed" and not self.errors else 0.0,
            "executor_type": self.executor_type,
            "executor_name": self.executor_name,
            "native_openclaw": self.native_openclaw,
            "runtime_backend": self.runtime_backend,
            "openclaw_agent": self.openclaw_agent,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "token_usage": self.token_usage or {},
            "duration_ms": self.duration_ms,
            "openclaw_run_id": self.openclaw_run_id,
            "openclaw_stop_reason": self.openclaw_stop_reason,
            # Tool evidence (v0.14.2)
            "tool_calls_detected": self.tool_calls_detected,
            "tool_call_summary": self.tool_call_summary,
            "inferred_tools": self.inferred_tools,
            "tool_call_evidence_source": self.tool_call_evidence_source,
            "tool_trace_available": self.tool_trace_available,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
        }


class TaskExecutor:
    """Base class for all task executors."""

    name = "base"
    executor_type = "unknown"
    native_openclaw = False
    runtime_backend = ""

    def can_handle(self, task_card: dict) -> bool:
        """Return True if this executor can handle the given task card."""
        raise NotImplementedError

    def execute(self, task_card: dict) -> ExecutionResult:
        """Execute the task and return result."""
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}: {self.name}>"
