# @PRODUCT Code-Capable Runtime — v0.9
"""Factory for creating Code-Capable Runtime adapters.

Uses a two-tier strategy:
1. Try REAL adapter (codex exec) — if health_check passes, use it.
2. Fallback to MOCK adapter — if health_check fails.
"""

from typing import Optional

from .base import CodeCapableAdapter
from .codex_adapter import CodexAdapter
from .claude_adapter import ClaudeCodeAdapter
from .mock_adapter import MockCodexAdapter


# Lazy-loaded singletons
_codex_adapter: Optional[CodeCapableAdapter] = None
_claude_adapter: Optional[CodeCapableAdapter] = None
_mock_adapter: Optional[CodeCapableAdapter] = None


async def get_code_runtime(runtime_type: str) -> Optional[CodeCapableAdapter]:
    """Get a Code-Capable Runtime adapter by type.

    Args:
        runtime_type: 'codex' or 'claude_code'

    Returns:
        Adapter instance, or None if unavailable.
    """
    global _codex_adapter, _claude_adapter

    if runtime_type == "codex":
        if _codex_adapter is None:
            adapter = CodexAdapter()
            health = await adapter.health_check()
            if health.online:
                _codex_adapter = adapter
            else:
                # Fallback to mock
                mock = await _get_mock_adapter()
                _codex_adapter = mock
        return _codex_adapter

    elif runtime_type == "claude_code":
        if _claude_adapter is None:
            adapter = ClaudeCodeAdapter()
            _claude_adapter = adapter
        return _claude_adapter

    return None


async def get_all_code_runtimes() -> list[CodeCapableAdapter]:
    """Get all available Code-Capable Runtime adapters."""
    runtimes = []
    codex = await get_code_runtime("codex")
    if codex:
        runtimes.append(codex)
    claude = await get_code_runtime("claude_code")
    if claude:
        runtimes.append(claude)
    return runtimes


async def _get_mock_adapter() -> MockCodexAdapter:
    """Get or create the singleton mock adapter."""
    global _mock_adapter
    if _mock_adapter is None:
        _mock_adapter = MockCodexAdapter()
    return _mock_adapter
