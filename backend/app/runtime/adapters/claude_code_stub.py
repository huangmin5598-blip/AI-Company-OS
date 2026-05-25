# @PRODUCT Adapter — OS Core
"""Claude Code runtime adapter stub.

health_check runs `claude --version` to determine availability.
Capabilities reflect real Claude Code features even when not yet wired.
"""
import asyncio

from app.runtime.base_adapter import BaseRuntimeAdapter
from app.runtime.protocol import RuntimeStatus


class ClaudeCodeAdapterStub(BaseRuntimeAdapter):
    """Claude Code adapter — health-aware stub with realistic capabilities."""

    @property
    def runtime_type(self) -> str:
        return "claude-code"

    async def health_check(self) -> RuntimeStatus:
        """Run `claude --version` to check availability."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "claude", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
            version = stdout.decode("utf-8", errors="replace").strip() if stdout else ""
            if version:
                return RuntimeStatus.ONLINE
            return RuntimeStatus.OFFLINE
        except Exception:
            return RuntimeStatus.OFFLINE

    async def get_capabilities(self) -> list[dict]:
        return [
            {"name": "code_generation", "type": "code",
             "description": "代码生成 — Claude Code 非交互模式", "enabled": True},
            {"name": "code_review", "type": "quality",
             "description": "代码审查 — Claude Code CLI", "enabled": False},
            {"name": "pr_management", "type": "workflow",
             "description": "Pull Request 管理（未接入）", "enabled": False},
        ]


def create_adapter(reg: dict):
    return ClaudeCodeAdapterStub(reg["runtime_id"], reg["display_name"])
