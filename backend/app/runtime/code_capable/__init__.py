# @PRODUCT Code-Capable Runtime — v0.9
"""Code-Capable Runtime Bridge — abstract interface for codex / claude_code adapters."""

from .base import (
    CodeCapableAdapter,
    PlanResult,
    PatchResult,
    CheckResult,
    HealthResult,
)
from .factory import get_code_runtime, get_all_code_runtimes

__all__ = [
    "CodeCapableAdapter",
    "PlanResult",
    "PatchResult",
    "CheckResult",
    "HealthResult",
    "get_code_runtime",
    "get_all_code_runtimes",
]
