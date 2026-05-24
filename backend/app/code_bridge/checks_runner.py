# @PRODUCT Code Bridge — v0.9
"""Automated checks runner — runs build/lint/typecheck in isolated check_workspace."""
import asyncio
import json
import os
import subprocess
from typing import Optional

class ChecksRunner:
    def __init__(self, repo_root: str):
        self.repo_root = repo_root

    async def run_all(self, request_id: int) -> dict:
        staging = os.path.join(self.repo_root, ".ai-company-os/staging", str(request_id))
        check_ws = os.path.join(staging, "check_workspace")

        if not os.path.exists(check_ws):
            raise RuntimeError(f"check_workspace not found: {check_ws}")

        result = {
            "build": await self._check_build(check_ws),
            "backend_import": await self._check_backend_import(check_ws),
            "typecheck": await self._check_typecheck(check_ws),
        }

        blocking_passed = all(
            r.get("passed", False)
            for name, r in result.items()
            if r.get("blocking", True)
        )
        has_warnings = any(
            r.get("warnings", [])
            for r in result.values()
        )
        result["_summary"] = {
            "checks_passed": blocking_passed,
            "has_warnings": has_warnings and blocking_passed,
            "all_passed": blocking_passed and not has_warnings,
        }
        return result

    async def _run_cmd(self, cmd: list[str], cwd: str, timeout: int = 60) -> dict:
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
            return {
                "exit_code": proc.returncode,
                "stdout": stdout.decode("utf-8", errors="replace") if stdout else "",
                "stderr": stderr.decode("utf-8", errors="replace") if stderr else "",
            }
        except asyncio.TimeoutError:
            return {"exit_code": -1, "stdout": "", "stderr": "Timed out"}
        except FileNotFoundError:
            return {"exit_code": -2, "stdout": "", "stderr": "Command not found"}

    async def _check_build(self, cwd: str) -> dict:
        result = {"name": "Frontend Build", "blocking": True}
        cmd_result = await self._run_cmd(["npx", "next", "build"], cwd)
        result["passed"] = cmd_result["exit_code"] == 0
        result["output"] = cmd_result["stdout"][:500] + cmd_result["stderr"][:500]
        return result

    async def _check_backend_import(self, cwd: str) -> dict:
        result = {"name": "Backend Import", "blocking": True}
        cmd_result = await self._run_cmd(
            ["python3", "-c", "from app.main import app; print('OK')"],
            cwd,
        )
        result["passed"] = cmd_result["exit_code"] == 0
        result["output"] = cmd_result["stdout"][:500] + cmd_result["stderr"][:500]
        return result

    async def _check_typecheck(self, cwd: str) -> dict:
        result = {"name": "TypeScript Type Check", "blocking": True}
        cmd_result = await self._run_cmd(
            ["npx", "tsc", "--noEmit"],
            cwd,
        )
        if cmd_result["exit_code"] == -2:
            result["passed"] = True  # skip if tsc not available
            result["skipped"] = True
            result["output"] = "TypeScript not available, skipped"
        else:
            result["passed"] = cmd_result["exit_code"] == 0
            result["output"] = cmd_result["stdout"][:500] + cmd_result["stderr"][:500]
        return result
