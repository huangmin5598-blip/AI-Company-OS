# @PRODUCT Code-Capable Runtime — v0.9
"""Mock adapter — returns preset responses for testing and development.

Used when the actual Codex/Claude Code CLI is unavailable.
"""

from .base import (
    CodeCapableAdapter,
    PlanResult,
    PatchResult,
    HealthResult,
)


class MockCodexAdapter(CodeCapableAdapter):
    """Mock adapter that returns preset responses."""

    def __init__(self, runtime_id: str = "codex-mock", display_name: str = "Codex (Mock)"):
        super().__init__(runtime_id, display_name)

    @property
    def runtime_type(self) -> str:
        return "codex"

    async def generate_plan(self, problem: str, context: dict) -> PlanResult:
        return PlanResult(
            plan_summary=(
                f"[MOCK] To address: {problem[:100]}... "
                "The planned change involves updating the README "
                "with additional documentation."
            ),
            impact_scope=(
                "README.md only. No code changes. Low risk."
            ),
            risk_level="low",
            files_expected=[
                "README.md",
            ],
            raw_output=f"[MOCK PLAN] Problem: {problem}",
        )

    async def generate_patch(self, plan: PlanResult, workdir: str) -> PatchResult:
        return PatchResult(
            patch_diff=(
                "--- a/README.md\n"
                "+++ b/README.md\n"
                "@@ -1,3 +1,5 @@\n"
                " # AI Company OS\n"
                "+\n"
                "+## Overview\n"
                "+AI Company OS is a system for managing AI agents in a company. (MOCK)\n"
            ),
            files_changed=["README.md"],
            diff_summary="[MOCK] Changed 1 file, 3 lines added.",
            raw_output="[MOCK PATCH]",
        )

    async def health_check(self) -> HealthResult:
        return HealthResult(
            online=True,
            runtime_type=self.runtime_type,
            version="0.0.0-mock",
            capabilities=self.get_capabilities(),
        )
