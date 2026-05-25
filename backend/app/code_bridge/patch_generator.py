# @PRODUCT Code Bridge — v0.9.1.2
"""Patch generator — calls Code-Capable Runtime to generate patch, creates staging and check_workspace.

v0.9.1.2 changes:
  - generate_patch now uses --output-schema (JSON structured output)
  - patch_spec.json written alongside patch.diff in staging
  - git apply --check is a hard gate before creating check_workspace
  - All evidence files (patch_spec.json, patch.diff, protected_file_check.json) are written to staging
"""
import asyncio
import json
import os
import shutil
from typing import Optional
from app.runtime.code_capable import PlanResult, PatchResult
from app.runtime.code_capable.factory import get_code_runtime

STAGING_BASE = ".ai-company-os/staging"


class PatchGenerator:
    def __init__(self, runtime_type: str = "codex"):
        self.runtime_type = runtime_type

    def _staging_dir(self, request_id: int, repo_root: str = "") -> str:
        if repo_root:
            return os.path.join(repo_root, STAGING_BASE, str(request_id))
        return os.path.join(os.getcwd(), STAGING_BASE, str(request_id))

    async def generate(self, request_id: int, plan: PlanResult, repo_root: str) -> PatchResult:
        adapter = await get_code_runtime(self.runtime_type)
        if adapter is None:
            raise RuntimeError(f"Code-Capable Runtime '{self.runtime_type}' is not available")

        staging_dir = self._staging_dir(request_id, repo_root)
        os.makedirs(staging_dir, exist_ok=True)

        # ── Step 1: Copy original files ──
        orig_dir = os.path.join(staging_dir, "original_files")
        for f in plan.files_expected:
            src = os.path.join(repo_root, f)
            if os.path.exists(src):
                dst = os.path.join(orig_dir, f)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)

        # ── Step 2: Generate patch from adapter (uses --output-schema in v0.9.1.2) ──
        patch_result = await adapter.generate_patch(plan, repo_root)

        # ── Step 3: Write patch diff to staging ──
        patch_path = os.path.join(staging_dir, "patch.diff")
        with open(patch_path, "w") as f:
            f.write(patch_result.patch_diff)

        # ── Step 4: Write patch_spec.json (structured JSON from adapter) ──
        patch_spec_path = os.path.join(staging_dir, "patch_spec.json")
        with open(patch_spec_path, "w") as f:
            f.write(patch_result.raw_output)

        # ── Step 5: git apply --check as HARD GATE ──
        # This runs on the actual repo root to verify the diff is valid
        import subprocess
        check_proc = await asyncio.create_subprocess_exec(
            "git", "apply", "--check", patch_path,
            cwd=repo_root,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        _, check_stderr = await check_proc.communicate()
        if check_proc.returncode != 0:
            err_msg = check_stderr.decode("utf-8", errors="replace") if check_stderr else "unknown error"
            raise RuntimeError(
                f"git apply --check failed for request {request_id}: {err_msg[:500]}"
            )

        # ── Step 6: Write plan artifacts ──
        with open(os.path.join(staging_dir, "plan_summary.md"), "w") as f:
            f.write(plan.plan_summary)

        # ── Step 7: Create isolated check workspace (skip heavy dirs) ──
        check_ws = os.path.join(staging_dir, "check_workspace")
        if os.path.exists(check_ws):
            shutil.rmtree(check_ws)

        def _ignore_patterns(path, names):
            """Skip node_modules, .next, __pycache__, .git, and other build artifacts."""
            ignored = set()
            skip_dirs = {
                "node_modules", ".next", "__pycache__", ".git",
                ".venv", "venv", "env", "dist", "build",
                ".hermes", ".ai-company-os",
            }
            skip_ext = {".pyc", ".pyo", ".so"}
            for name in names:
                full = os.path.join(path, name)
                if name in skip_dirs:
                    ignored.add(name)
                elif os.path.isfile(full) and os.path.splitext(name)[1] in skip_ext:
                    ignored.add(name)
                elif os.path.isdir(full) and name.startswith(".") and name not in (".vscode", ".github"):
                    ignored.add(name)
            return ignored

        shutil.copytree(repo_root, check_ws, symlinks=False,
                        ignore=_ignore_patterns,
                        ignore_dangling_symlinks=True)

        # Apply patch to check workspace
        apply_proc = await asyncio.create_subprocess_exec(
            "git", "apply", patch_path,
            cwd=check_ws,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        await apply_proc.wait()

        # ── Step 8: Extract modified files from check_workspace ──
        mod_dir = os.path.join(staging_dir, "modified_files")
        for f in patch_result.files_changed:
            src = os.path.join(check_ws, f)
            if os.path.exists(src):
                dst = os.path.join(mod_dir, f)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)

        return patch_result
