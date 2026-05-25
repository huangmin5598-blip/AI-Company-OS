# @PRODUCT Code-Capable Runtime — v0.9.1
"""Claude Code adapter — non-interactive plan generation with graceful fallback.

Uses `claude -p` (--print) for non-interactive plan generation. If the CLI
is unavailable or returns an API error, returns a PlanResult with an
unavailable message rather than raising.

V0.9: adapter shape only, enabled=0, experimental.
V0.9.1: added generate_plan() with graceful fallback on failure.
"""
import asyncio

from .base import (
    CodeCapableAdapter,
    PlanResult,
    PatchResult,
    HealthResult,
)

_CLAUDE_CMD = "claude"


class ClaudeCodeAdapter(CodeCapableAdapter):
    """Claude Code adapter — ACP-based plan generation with graceful fallback."""

    def __init__(self, runtime_id: str = "claude-code", display_name: str = "Claude Code (Experimental)"):
        super().__init__(runtime_id, display_name)

    @property
    def runtime_type(self) -> str:
        return "claude-code"

    async def generate_plan(self, problem: str, context: dict) -> PlanResult:
        """Generate a plan using Claude Code CLI in non-interactive mode.

        Uses `claude -p` (--print) for non-interactive output. If the CLI
        is unavailable or returns an error, returns a PlanResult with an
        unavailable/fallback message instead of raising.
        """
        workdir = context.get("workdir", ".")
        prompt = (
            f"Analyze this code change request and output a plan.\n\n"
            f"Problem: {problem}\n\n"
            f"Output exactly in this format:\n"
            f"PLAN_SUMMARY: (1-3 sentences describing what to change and how)\n"
            f"IMPACT: (which components/services are affected, risk assessment)\n"
            f"RISK: low/medium/high\n"
            f"FILES: (comma-separated list of file paths to modify)\n\n"
            f"Do NOT modify any files. Only read and analyze."
        )

        try:
            output = await self._run_claude(prompt, workdir)
            if not output or "API Error" in output:
                return self._unavailable_plan(problem, f"Claude API error: {output[:200] if output else 'no output'}")

            plan_summary = self._extract_section(output, "PLAN_SUMMARY") or output[:500]
            files = self._extract_files(output)
            risk = self._extract_risk(output)
            impact = self._extract_section(output, "IMPACT") or risk

            return PlanResult(
                plan_summary=plan_summary,
                impact_scope=impact,
                risk_level=risk,
                files_expected=files,
                raw_output=output,
            )
        except FileNotFoundError:
            return self._unavailable_plan(problem, "claude CLI not found on PATH")
        except Exception as e:
            return self._unavailable_plan(problem, str(e)[:200])

    async def _run_claude(self, prompt: str, workdir: str, timeout: int = 300) -> str:
        """Run claude -p in non-interactive mode and return stdout."""
        cmd = [_CLAUDE_CMD, "-p", prompt]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=workdir,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)

        stderr_text = stderr.decode("utf-8", errors="replace").strip() if stderr else ""
        output = stdout.decode("utf-8", errors="replace").strip() if stdout else ""

        # If there's an API error on stderr, include it in the output
        if proc.returncode != 0 and not output:
            return f"CLI error (exit {proc.returncode}): {stderr_text[:300]}"

        # API errors in stdout (API returns 400 in the output stream)
        if not output and stderr_text:
            return f"CLI error (exit {proc.returncode}): {stderr_text[:300]}"

        return output

    def _unavailable_plan(self, problem: str, reason: str) -> PlanResult:
        """Return a PlanResult indicating Claude Code is unavailable."""
        return PlanResult(
            plan_summary=(
                f"Claude Code is currently unavailable. "
                f"Cannot generate plan for: {problem[:100]}..."
            ),
            impact_scope="N/A — runtime unavailable",
            risk_level="low",
            files_expected=[],
            raw_output=f"UNAVAILABLE: {reason}",
        )

    @staticmethod
    def _extract_section(text: str, section: str) -> str:
        """Extract text after a section marker like 'PLAN_SUMMARY:'."""
        import re
        pattern = rf"{section}:\s*(.+?)(?:\n\w+_|\Z)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return ""

    @staticmethod
    def _extract_files(text: str) -> list[str]:
        """Extract file paths from the output."""
        import re
        files = []
        files_section = ClaudeCodeAdapter._extract_section(text, "FILES")
        if files_section:
            files = [f.strip().strip("`") for f in files_section.replace(",", "\n").split("\n") if f.strip()]
        if not files:
            files = re.findall(r"`([^`]+\.\w+)`", text)
        return list(dict.fromkeys(files))

    @staticmethod
    def _extract_risk(text: str) -> str:
        """Extract risk level from the output."""
        risk = ClaudeCodeAdapter._extract_section(text, "RISK")
        if risk:
            risk_lower = risk.lower()
            if "high" in risk_lower:
                return "high"
            if "medium" in risk_lower or "moderate" in risk_lower:
                return "medium"
            return "low"
        return "medium"

    async def generate_patch(self, plan: PlanResult, workdir: str) -> PatchResult:
        raise NotImplementedError(
            "Claude Code adapter is experimental and does not support patch generation in v0.9."
        )

    async def health_check(self) -> HealthResult:
        """Quick check if claude CLI exists."""
        try:
            from asyncio import create_subprocess_exec, wait_for, subprocess
            proc = await create_subprocess_exec(
                _CLAUDE_CMD, "--version",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, _ = await wait_for(proc.communicate(), timeout=10)
            version = stdout.decode("utf-8", errors="replace").strip() if stdout else ""
            return HealthResult(
                online=True,
                runtime_type=self.runtime_type,
                version=version,
                capabilities=await self.get_capabilities(),
            )
        except Exception as e:
            return HealthResult(
                online=False,
                runtime_type=self.runtime_type,
                error=str(e),
                capabilities=[],
            )

    async def get_capabilities(self) -> list[str]:
        """Return list of supported capabilities."""
        caps = ["code_plan", "code_patch"]
        try:
            await self.run_checks("")
        except NotImplementedError:
            pass
        else:
            caps.append("code_check")
        return caps
