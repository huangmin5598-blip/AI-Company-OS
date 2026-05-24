# @PRODUCT Code-Capable Runtime — v0.9
"""Claude Code adapter — experimental shape only.

Claude Code CLI's non-interactive mode (-p) is unreliable on this machine
(timeout/hang issues). This adapter provides adapter shape + capability discovery
but does NOT implement full plan/patch/check workflows.

V0.9: adapter shape only, enabled=0, experimental.
Full integration deferred to v0.9.1+ when Claude Code -p mode is stable.
"""

from .base import (
    CodeCapableAdapter,
    PlanResult,
    PatchResult,
    HealthResult,
)


class ClaudeCodeAdapter(CodeCapableAdapter):
    """Experimental Claude Code adapter — shape only, not production-ready."""

    def __init__(self, runtime_id: str = "claude-code", display_name: str = "Claude Code (Experimental)"):
        super().__init__(runtime_id, display_name)

    @property
    def runtime_type(self) -> str:
        return "claude_code"

    async def generate_plan(self, problem: str, context: dict) -> PlanResult:
        raise NotImplementedError(
            "Claude Code adapter is experimental and does not support plan generation in v0.9."
        )

    async def generate_patch(self, plan: PlanResult, workdir: str) -> PatchResult:
        raise NotImplementedError(
            "Claude Code adapter is experimental and does not support patch generation in v0.9."
        )

    async def health_check(self) -> HealthResult:
        """Quick check if claude CLI exists."""
        import asyncio
        try:
            proc = await asyncio.create_subprocess_exec(
                "claude", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=5)
            version = stdout.decode("utf-8", errors="replace").strip() if stdout else ""
            return HealthResult(
                online=True,
                runtime_type=self.runtime_type,
                version=version,
                capabilities=self.get_capabilities(),
            )
        except Exception as e:
            return HealthResult(
                online=False,
                runtime_type=self.runtime_type,
                error=str(e),
                capabilities=[],
            )
