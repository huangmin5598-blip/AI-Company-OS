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
        # Read real README.md to generate a valid patch (passes git apply --check)
        import os
        readme_path = os.path.join(workdir, "README.md")
        readme_lines = []
        if os.path.exists(readme_path):
            with open(readme_path) as f:
                readme_lines = f.readlines()

        last_line_num = len(readme_lines)
        mock_line = "<!-- v0.9.1.2 mock test marker -->\n"
        new_diff = (
            "--- a/README.md\n"
            "+++ b/README.md\n"
            f"@@ -{last_line_num},0 +{last_line_num + 1},1 @@\n"
            f"+{mock_line.rstrip()}\n"
        )

        mock_spec = {
            "plan_summary": plan.plan_summary,
            "risk": "low",
            "impact": "README.md only. No code changes. Low risk.",
            "files": [
                {"path": "README.md", "change": f"Append 1 mock marker line at end of file"}
            ],
            "diff": new_diff,
        }
        raw_json = __import__("json").dumps(mock_spec, indent=2, ensure_ascii=False)

        return PatchResult(
            patch_diff=new_diff,
            files_changed=["README.md"],
            diff_summary=f"[MOCK] Added 1 line to README.md (v0.9.1.2 schema-compliant)",
            raw_output=raw_json,
        )

    async def health_check(self) -> HealthResult:
        return HealthResult(
            online=True,
            runtime_type=self.runtime_type,
            version="0.0.0-mock",
            capabilities=self.get_capabilities(),
        )
