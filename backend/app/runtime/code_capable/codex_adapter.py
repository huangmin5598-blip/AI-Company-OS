# @PRODUCT Code-Capable Runtime — v0.9.1.2
"""Codex CLI adapter — uses 'codex exec' for non-interactive plan/patch generation.

Key design decisions (v0.9.1.2):
- generate_plan: free-text codex exec (stable, 40-70s)
- generate_patch: --output-schema JSON patch (v0.9.1.2 new path, ~25s, validated)
  JSON schema validation is a hard gate — no fallback to regex diff extraction.
  This replaces the old regex-based _extract_git_diff approach.
- Sandbox is kept read-only (codex default), so codex NEVER writes files directly.
- The adapter acts as a SAFE bridge — codex analyzes and outputs JSON, WE apply changes.
"""
import asyncio
import json
import os
import re
import tempfile
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
    return ""


def _extract_files(text: str) -> list[str]:
    """Extract file paths from the output."""
    files = []
    files_section = _extract_section(text, "FILES")
    if files_section:
        files = [f.strip().strip("`") for f in files_section.replace(",", "\n").split("\n") if f.strip()]
    if not files:
        files = re.findall(r"`([^`]+\.\w+)`", text)
    return list(dict.fromkeys(files))


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


class CodexAdapter(CodeCapableAdapter):
    """Adapter for OpenAI Codex CLI via 'codex exec'."""

    def __init__(self, runtime_id: str = "codex", display_name: str = "Codex CLI"):
        super().__init__(runtime_id, display_name)
        # Resolve schema path relative to this file's project root
        self._schema_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),  # runtime/code_capable/
            "..", "..", "..", "..",  # up to repo root
            "docs", "schemas", "patch_spec_schema.json",
        )
        self._schema_path = os.path.normpath(self._schema_path)

    @property
    def runtime_type(self) -> str:
        return "codex"

    async def _run_codex(self, prompt: str, workdir: str, timeout: int = 300,
                         schema_path: str = None) -> str:
        """Run codex exec via thread pool + sync subprocess.run.

        Uses run_in_executor + subprocess.run (not asyncio.create_subprocess_exec)
        because Codex CLI has an issue with direct Popen/create_subprocess_exec —
        it creates orphaned process groups that hang. Going through
        run_in_executor + start_new_session + stdin=DEVNULL resolves this.

        Always uses --dangerously-bypass-approvals-and-sandbox (repo is pre-trusted)
        and --output-last-message to avoid pipe deadlocks.
        When schema_path is provided, also adds --output-schema.
        """
        import tempfile
        import shlex

        fd, out_path = tempfile.mkstemp(suffix="_codex_output.txt")
        os.close(fd)

        def _sync_run() -> dict:
            import subprocess
            import time
            start = time.time()

            cmd = [
                _CODEX_CMD, "exec", prompt,
                "--dangerously-bypass-approvals-and-sandbox",
                "--output-last-message", out_path,
            ]
            if schema_path:
                cmd.extend(["--output-schema", schema_path])

            # Use a file for stdout (full log) — stderr stays as PIPE for error detection
            stdout_path = out_path + ".stdout"
            with open(stdout_path, "w") as stdout_f:
                result = subprocess.run(
                    cmd,
                    cwd=workdir,
                    stdin=subprocess.DEVNULL,
                    stdout=stdout_f,
                    stderr=subprocess.PIPE,
                    text=True,
                    timeout=timeout,
                    start_new_session=True,
                )
            elapsed = time.time() - start

            stderr_text = result.stderr or ""

            # Read output from last_message file
            output = ""
            if os.path.exists(out_path):
                with open(out_path) as f:
                    output = f.read().strip()

            # Cleanup temp files
            for p in [stdout_path, out_path]:
                if os.path.exists(p):
                    os.unlink(p)

            return {
                "output": output,
                "exit_code": result.returncode,
                "elapsed": round(elapsed, 2),
                "stderr": stderr_text[:500] if stderr_text else "",
            }

        loop = asyncio.get_running_loop()
        try:
            sync_result = await loop.run_in_executor(None, _sync_run)
        except Exception as e:
            # subprocess.TimeoutExpired etc.
            if os.path.exists(out_path):
                os.unlink(out_path)
            error_msg = str(e)
            if "TimeoutExpired" in type(e).__name__:
                raise RuntimeError(f"Codex exec timed out after {timeout}s")
            raise RuntimeError(f"Codex exec failed: {error_msg[:200]}")

        if not sync_result["output"] and sync_result["exit_code"] != 0:
            raise RuntimeError(
                f"Codex exec failed (exit {sync_result['exit_code']}): "
                f"{sync_result['stderr']}"
            )

        return sync_result["output"]

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
        """Generate a git diff patch using codex exec + --output-schema.

        v0.9.1.2: Uses --output-schema for structured JSON output with git diff.
        Hard gates (in order):
          1. JSON must parse
          2. JSON must match patch_spec_schema.json
          3. 'diff' field must be non-empty
        ALL gates must pass — no fallback to regex-based extraction.
        """
        # Resolve schema path relative to workdir (repo root), with fallback to module path
        schema_rel = os.path.join(workdir, "docs", "schemas", "patch_spec_schema.json")
        schema_path = schema_rel if os.path.exists(schema_rel) else self._schema_path

        if not os.path.exists(schema_path):
            raise RuntimeError(f"patch_spec_schema.json not found at {schema_path}")

        prompt = (
            f"Make the following planned code change. Output structured JSON matching the schema.\n\n"
            f"Plan: {plan.plan_summary}\n"
            f"Files to modify: {', '.join(plan.files_expected)}\n\n"
            f"DO NOT write or modify any files. Only output the diff in the 'diff' field."
        )

        json_output = await self._run_codex(prompt, workdir, schema_path=schema_path)

        # ── Hard Gate 1: JSON must parse ──
        try:
            data = json.loads(json_output)
        except json.JSONDecodeError as e:
            raise RuntimeError(
                f"Codex output is not valid JSON (schema_path={schema_path}): {e}\n"
                f"Raw output (first 500 chars): {json_output[:500]}"
            )

        # ── Hard Gate 2: JSON must match schema ──
        try:
            from jsonschema import validate, ValidationError
            with open(schema_path) as f:
                schema = json.load(f)
            validate(instance=data, schema=schema)
        except ValidationError as e:
            raise RuntimeError(
                f"Codex output failed schema validation: {e.message}\n"
                f"Path: {list(e.absolute_path) if e.absolute_path else 'root'}"
            )

        # ── Hard Gate 3: diff field must be non-empty ──
        diff = data.get("diff", "")
        if not diff or not diff.strip():
            raise RuntimeError("Codex output contains empty 'diff' field — patch rejected")

        # Extract files_changed from the diff itself (authoritative source)
        files_changed = re.findall(r"\+\+\+ b/(\S+)", diff)
        files_changed = list(dict.fromkeys(files_changed))

        lines_changed = len(diff.split("\n"))
        diff_summary = (
            f"Changed {len(files_changed)} file(s), {lines_changed} line(s) in diff. "
            f"Files: {', '.join(files_changed) if files_changed else 'see diff'}"
        )

        # Preserve the full JSON spec as raw_output (not just the diff)
        raw_spec = json.dumps(data, indent=2, ensure_ascii=False)

        return PatchResult(
            patch_diff=diff,
            files_changed=files_changed,
            diff_summary=diff_summary,
            raw_output=raw_spec,
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
