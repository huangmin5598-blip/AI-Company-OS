# @PRODUCT Code-Capable Runtime — v0.9
"""Codex CLI adapter — uses 'codex exec' for non-interactive plan/patch generation.

Key design decisions:
- Sandbox is kept read-only (codex default), so codex NEVER writes files directly.
- We capture stdout and extract plan/patch from the structured output.
- The adapter acts as a SAFE bridge — codex analyzes and outputs text, WE apply changes.
"""

import asyncio
import re
from typing import Optional

from .base import (
    CodeCapableAdapter,
    PlanResult,
    PatchResult,
    HealthResult,
)


_CODEX_CMD = "codex"


def _clean_output(text: str) -> str:
    """Remove token usage lines and codex metadata from stdout."""
    lines = text.split("\n")
    cleaned = [l for l in lines if not l.startswith("tokens used") and "codex" not in l[:20]]
    return "\n".join(cleaned).strip()


def _extract_section(text: str, section: str) -> str:
    """Extract text after a section marker like 'PLAN_SUMMARY:'."""
    pattern = rf"{section}:\s*(.+?)(?:\n\w+_|\Z)"
    match = re.search(pattern, text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: look for markdown headings
    return ""


def _extract_files(text: str) -> list[str]:
    """Extract file paths from the output."""
    files = []
    # Look for FILES: section
    files_section = _extract_section(text, "FILES")
    if files_section:
        files = [f.strip().strip("`") for f in files_section.replace(",", "\n").split("\n") if f.strip()]
    # Fallback: look for file paths in backticks
    if not files:
        files = re.findall(r"`([^`]+\.\w+)`", text)
    return list(dict.fromkeys(files))  # dedup preserving order


def _extract_risk(text: str) -> str:
    """Extract risk level from the output."""
    risk = _extract_section(text, "RISK")
    if risk:
        risk_lower = risk.lower()
        if "high" in risk_lower:
            return "high"
        if "medium" in risk_lower or "moderate" in risk_lower:
            return "medium"
        return "low"
    return "medium"


def _extract_git_diff(text: str) -> tuple[str, str]:
    """Extract git diff and diff summary from codex output.

    Returns (patch_diff, diff_summary).
    """
    # Look for git diff block
    diff_match = re.search(
        r"```diff\n(.*?)```", text, re.DOTALL
    )
    patch_diff = diff_match.group(1).strip() if diff_match else ""

    # Build a natural language summary
    lines_changed = len(patch_diff.split("\n")) if patch_diff else 0
    files_match = re.findall(r"\+\+\+ b/(\S+)", patch_diff)
    files_changed = list(dict.fromkeys(files_match))
    summary = (
        f"Changed {len(files_changed)} file(s), {lines_changed} line(s) in diff. "
        f"Files: {', '.join(files_changed) if files_changed else 'see diff'}"
    )
    return patch_diff, summary


class CodexAdapter(CodeCapableAdapter):
    """Adapter for OpenAI Codex CLI via 'codex exec'."""

    def __init__(self, runtime_id: str = "codex", display_name: str = "Codex CLI"):
        super().__init__(runtime_id, display_name)

    @property
    def runtime_type(self) -> str:
        return "codex"

    async def _run_codex(self, prompt: str, workdir: str, timeout: int = 120) -> str:
        """Run codex exec with the given prompt and return stdout."""
        cmd = [_CODEX_CMD, "exec", prompt]
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=workdir,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError(f"Codex exec timed out after {timeout}s")

        output = stdout.decode("utf-8", errors="replace") if stdout else ""
        err = stderr.decode("utf-8", errors="replace") if stderr else ""

        if proc.returncode != 0 and not output:
            raise RuntimeError(f"Codex exec failed (exit {proc.returncode}): {err[:500]}")

        return _clean_output(output)

    async def generate_plan(self, problem: str, context: dict) -> PlanResult:
        """Generate a natural language plan using codex exec."""
        workdir = context.get("workdir", ".")
        prompt = (
            f"Read the relevant files in this repository. "
            f"Problem: {problem}\n\n"
            f"Output exactly in this format:\n"
            f"PLAN_SUMMARY: (1-3 sentences describing what to change and how)\n"
            f"IMPACT: (which components/services are affected, risk assessment)\n"
            f"RISK: low/medium/high\n"
            f"FILES: (comma-separated list of file paths to modify)\n\n"
            f"Do NOT modify any files. Only read and analyze."
        )

        output = await self._run_codex(prompt, workdir)

        plan_summary = _extract_section(output, "PLAN_SUMMARY") or _clean_output(output)[:500]
        files = _extract_files(output)
        risk = _extract_risk(output)
        impact = _extract_section(output, "IMPACT") or risk

        return PlanResult(
            plan_summary=plan_summary,
            impact_scope=impact,
            risk_level=risk,
            files_expected=files,
            raw_output=output,
        )

    async def generate_patch(self, plan: PlanResult, workdir: str) -> PatchResult:
        """Generate a git diff patch using codex exec based on an approved plan."""
        prompt = (
            f"Make the following planned code change. Output the COMPLETE modified file "
            f"contents and a git diff showing the change.\n\n"
            f"Plan: {plan.plan_summary}\n"
            f"Files to modify: {', '.join(plan.files_expected)}\n\n"
            f"Output format:\n"
            f"```diff\n"
            f"(full git diff here)\n"
            f"```\n\n"
            f"DO NOT write or modify any files. Only output the diff."
        )

        output = await self._run_codex(prompt, workdir)

        # Also read the file list from the plan
        files_from_plan = set(plan.files_expected)
        patch_diff, diff_summary = _extract_git_diff(output)

        # Determine actual changed files from the diff
        files_changed = list(files_from_plan)
        diff_files = re.findall(r"\+\+\+ b/(\S+)", patch_diff)
        if diff_files:
            files_changed = list(dict.fromkeys(diff_files))

        return PatchResult(
            patch_diff=patch_diff,
            files_changed=files_changed,
            diff_summary=diff_summary,
            raw_output=output,
        )

    async def health_check(self) -> HealthResult:
        """Check if codex CLI is available."""
        try:
            proc = await asyncio.create_subprocess_exec(
                _CODEX_CMD, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
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
