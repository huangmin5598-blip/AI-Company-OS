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
                "The planned change involves adding input validation "
                "and updating the frontend component accordingly."
            ),
            impact_scope=(
                "Frontend component only. No API changes. "
                "Low risk, isolated modification."
            ),
            risk_level="low",
            files_expected=[
                "frontend/src/components/Example.tsx",
            ],
            raw_output=f"[MOCK PLAN] Problem: {problem}",
        )

    async def generate_patch(self, plan: PlanResult, workdir: str) -> PatchResult:
        return PatchResult(
            patch_diff=(
                "--- a/frontend/src/components/Example.tsx\n"
                "+++ b/frontend/src/components/Example.tsx\n"
                "@@ -1,5 +1,12 @@\n"
                " export default function Example() {\n"
                "-  return <div>Hello</div>;\n"
                "+  return (\n"
                "+    <div>\n"
                "+      Hello\n"
                "+      <button onClick={() => alert('Clicked!')}>Click me</button>\n"
                "+    </div>\n"
                "+  );\n"
                " }\n"
            ),
            files_changed=["frontend/src/components/Example.tsx"],
            diff_summary="[MOCK] Changed 1 file, 7 lines added.",
            raw_output="[MOCK PATCH]",
        )

    async def health_check(self) -> HealthResult:
        return HealthResult(
            online=True,
            runtime_type=self.runtime_type,
            version="0.0.0-mock",
            capabilities=self.get_capabilities(),
        )
