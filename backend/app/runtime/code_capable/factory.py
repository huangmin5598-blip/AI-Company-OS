# @PRODUCT Code-Capable Runtime — v0.9.1.2
"""Factory for creating Code-Capable Runtime adapters.

v0.9.1.2 fix: Removed module-level _USE_MOCK (evaluated at import time).
get_code_runtime now reads CODE_RUNTIME env var at call time AND
is async-aware (no asyncio.run() in async context).
"""
import os
from typing import Optional

from .base import CodeCapableAdapter
from .mock_adapter import MockCodexAdapter


def _use_mock() -> bool:
    """Determine if we should use the mock adapter at call time (not import time)."""
    return os.environ.get("CODE_RUNTIME", "mock") != "real"


async def get_code_runtime(runtime_type: str) -> Optional[CodeCapableAdapter]:
    """Get a Code-Capable Runtime adapter by type.

    Async because health_check() is async. Uses await instead of asyncio.run()
    to avoid 'cannot be called from a running event loop' errors.
    """
    if runtime_type == "codex":
        if _use_mock():
            return MockCodexAdapter()
        from .codex_adapter import CodexAdapter
        adapter = CodexAdapter()
        health = await adapter.health_check()
        if health.online:
            return adapter
        return MockCodexAdapter()

    elif runtime_type == "claude-code":
        from .claude_adapter import ClaudeCodeAdapter
        return ClaudeCodeAdapter()

    return None


async def get_all_code_runtimes() -> list[CodeCapableAdapter]:
    """Get all available Code-Capable Runtime adapters."""
    runtimes = []
    codex = await get_code_runtime("codex")
    if codex:
        runtimes.append(codex)
    claude = await get_code_runtime("claude-code")
    if claude:
        runtimes.append(claude)
    return runtimes
