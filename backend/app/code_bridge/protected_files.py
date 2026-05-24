# @PRODUCT Code Bridge — v0.9
"""Protected files policy — pre-check and post-check."""
import fnmatch
import json
import os
import re
from typing import Optional

PROTECTED_PATTERNS = [
    ".env", ".env.*", "*.db", "*secret*", "*credential*",
    "*token*", "*deploy*", ".git/**", ".git/config",
    "docker-compose*.yml", "Dockerfile", "*migration*",
]

class ProtectedFileChecker:
    def __init__(self, repo_root: str):
        self.repo_root = os.path.abspath(repo_root)

    def _is_protected(self, file_path: str) -> bool:
        rel = os.path.relpath(file_path, self.repo_root)
        for pattern in PROTECTED_PATTERNS:
            if fnmatch.fnmatch(rel, pattern) or fnmatch.fnmatch(os.path.basename(rel), pattern):
                return True
        return False

    def pre_check(self, files_expected: list[str]) -> dict:
        violations = [f for f in files_expected if self._is_protected(f)]
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "checked_files": files_expected,
        }

    def post_check(self, patch_diff: str, files_changed: list[str]) -> dict:
        violations = []
        # Check files_changed list
        for f in files_changed:
            if self._is_protected(f):
                violations.append(f)
        # Check patch diff for any referenced protected paths
        diff_files = re.findall(r'^\+\+\+ b/(.+)$', patch_diff, re.MULTILINE)
        for f in diff_files:
            if self._is_protected(f) and f not in violations:
                violations.append(f)
        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "checked_files": list(dict.fromkeys(files_changed + diff_files)),
        }

    def check_manifest(self, manifest: dict) -> dict:
        violations = []
        for entry in manifest.get("files", []):
            path = entry.get("path", "")
            if self._is_protected(path):
                violations.append(path)
        return {
            "passed": len(violations) == 0,
            "violations": violations,
        }
