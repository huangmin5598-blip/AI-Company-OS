# @PRODUCT Code-Capable Runtime — v0.9
"""Factory for creating Code-Capable Runtime adapters.

Uses a two-tier strategy:
1. Try REAL adapter (codex exec) — if health_check passes, use it.
2. Fallback to MOCK adapter — if health_check fails.
"""
import os
from typing import Optional

from .base import CodeCapableAdapter
from .mock_adapter import MockCodexAdapter


# Force mock mode for testing. Set env CODE_RUNTIME=real to use actual Codex.
_USE_MOCK = os.environ.get("CODE_RUNTIME", "mock") != "real"


def get_code_runtime(runtime_type: str) -> Optional[CodeCapableAdapter]:
    """Get a Code-Capable Runtime adapter by type."""
    if runtime_type == "codex":
        if _USE_MOCK:
            return MockCodexAdapter()
        from .codex_adapter import CodexAdapter
        import asyncio
        adapter = CodexAdapter()
        health = asyncio.run(adapter.health_check())
        if health.online:
            return adapter
        return MockCodexAdapter()

    elif runtime_type == "claude_code":
        from .claude_adapter import ClaudeCodeAdapter
        return ClaudeCodeAdapter()

    return None


def get_all_code_runtimes() -> list[CodeCapableAdapter]:
    """Get all available Code-Capable Runtime adapters."""
    runtimes = []
    codex = get_code_runtime("codex")
    if codex:
        runtimes.append(codex)
    claude = get_code_runtime("claude_code")
    if claude:
        runtimes.append(claude)
    return runtimes
