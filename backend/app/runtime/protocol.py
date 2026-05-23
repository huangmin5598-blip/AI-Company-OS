# @PRODUCT backend/app/runtime/protocol.py
"""
RuntimeAdapter Protocol — Abstract interface for AI runtime integration.

This protocol defines how AI Company OS interacts with any AI runtime
(Hermes, Codex, Claude Code, etc.) through a uniform adapter layer.

Purpose:
  - Decouple OS Core from specific runtime implementations
  - Enable multi-runtime support (v0.6+) without changing OS Core
  - Provide a testable interface for runtime behavior

Usage:
  class HermesAdapter(RuntimeAdapter):
      async def execute(self, session, command):
          # Hermes-specific implementation
          ...

See docs/architecture/PRODUCTIZATION-ARCHITECTURE.md for the four-layer model.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Protocol, Optional, runtime_checkable


# ── Enums ──────────────────────────────────────────────────────────────


class RuntimeCapability(str, Enum):
    """Capabilities a runtime may or may not support."""

    TASK_EXECUTION = "task_execution"          # Execute arbitrary tasks
    CODE_GENERATION = "code_generation"         # Write and run code
    WEB_BROWSING = "web_browsing"               # Browse the web
    FILE_OPERATIONS = "file_operations"          # Read/write files
    TOOL_USE = "tool_use"                       # Use external tools
    MEMORY_ACCESS = "memory_access"             # Access company memory
    MULTI_TURN = "multi_turn"                   # Support conversation state
    SKILL_LOADING = "skill_loading"             # Load custom skills


class RuntimeStatus(str, Enum):
    """Runtime health status."""

    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"  # Running but with errors or high latency
    UNKNOWN = "unknown"


# ── Data Types ─────────────────────────────────────────────────────────


class RuntimeSession:
    """
    A session represents a unit of work assigned to a runtime.

    Each session has a unique ID, a goal or task description, and may
    carry context (company memory, tool access, etc.).
    """

    def __init__(
        self,
        session_id: str,
        goal: str,
        context: Optional[dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
    ):
        self.session_id = session_id
        self.goal = goal
        self.context = context or {}
        self.created_at = created_at or datetime.utcnow()
        self.status: RuntimeStatus = RuntimeStatus.ONLINE

    def to_dict(self) -> dict[str, Any]:
        return {
            "session_id": self.session_id,
            "goal": self.goal,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
            "status": self.status.value,
        }


# ── Protocol ───────────────────────────────────────────────────────────


@runtime_checkable
class RuntimeAdapter(Protocol):
    """
    Protocol that every AI runtime adapter must implement.

    This is a structural typing protocol (PEP 544) — adapters don't need
    to inherit from this class, just implement the methods.
    """

    # ── Metadata ──

    @property
    def name(self) -> str:
        """Human-readable runtime name (e.g., 'hermes-local', 'codex')."""
        ...

    @property
    def runtime_type(self) -> str:
        """Runtime type identifier (e.g., 'hermes', 'codex', 'claude-code')."""
        ...

    # ── Lifecycle ──

    async def health_check(self) -> RuntimeStatus:
        """
        Check if the runtime is reachable and operational.

        Returns:
            RuntimeStatus: ONLINE, OFFLINE, DEGRADED, or UNKNOWN
        """
        ...

    async def get_capabilities(self) -> list[RuntimeCapability]:
        """
        Discover what this runtime can do.

        Returns:
            List of supported RuntimeCapability values.
        """
        ...

    # ── Execution ──

    async def create_session(
        self,
        goal: str,
        context: Optional[dict[str, Any]] = None,
    ) -> RuntimeSession:
        """
        Create a new execution session for a goal.

        Args:
            goal: The task or goal description.
            context: Optional context (memory references, tool config, etc.).

        Returns:
            A RuntimeSession with a unique session_id.
        """
        ...

    async def execute(
        self,
        session: RuntimeSession,
        command: str,
        timeout_seconds: int = 300,
    ) -> dict[str, Any]:
        """
        Execute a command within a session.

        Args:
            session: The active RuntimeSession.
            command: The command or instruction to execute.
            timeout_seconds: Maximum execution time before abort.

        Returns:
            dict with keys:
              - "status": "success" | "error" | "timeout" | "cancelled"
              - "output": str (execution result or error message)
              - "metadata": dict (tokens used, duration, etc.)
        """
        ...

    async def cancel_session(self, session_id: str) -> bool:
        """
        Cancel a running session.

        Args:
            session_id: The session to cancel.

        Returns:
            True if cancelled successfully, False if session not found.
        """
        ...

    # ── Cost Tracking ──

    async def get_cost(
        self,
        session_id: str,
    ) -> dict[str, Any]:
        """
        Get cost and token usage for a completed or running session.

        Returns:
            dict with keys:
              - "tokens_in": int
              - "tokens_out": int
              - "total_tokens": int
              - "estimated_cost_usd": float
              - "duration_seconds": float
        """
        ...


# ── Utility ────────────────────────────────────────────────────────────


def create_adapter_descriptor(adapter: RuntimeAdapter) -> dict[str, Any]:
    """
    Create a standardized descriptor for a runtime adapter.

    Used by the capability discovery system and the /routers/runs endpoints.
    """
    return {
        "name": adapter.name,
        "type": adapter.runtime_type,
        "status": RuntimeStatus.UNKNOWN.value,  # Updated after health check
        "capabilities": [],  # Updated after capability check
    }
