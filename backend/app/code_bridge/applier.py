# @PRODUCT Code Bridge — v0.9
"""Apply/Rollback with path safety validation."""
import json
import os
import shutil
from typing import Optional

STAGING_BASE = ".ai-company-os/staging"

class PathSafetyError(Exception):
    pass

def safe_path_join(repo_root: str, relative_path: str) -> str:
    """Prevent path traversal attacks."""
    # Reject absolute paths
    if os.path.isabs(relative_path):
        raise PathSafetyError(f"Absolute path not allowed: {relative_path}")
    # Reject ..
    normalized = os.path.normpath(relative_path)
    if normalized.startswith("..") or ".." in normalized.split(os.sep):
        raise PathSafetyError(f"Path traversal detected: {relative_path}")
    # Must resolve inside repo_root
    joined = os.path.abspath(os.path.join(repo_root, normalized))
    if not joined.startswith(os.path.abspath(repo_root) + os.sep) and joined != os.path.abspath(repo_root):
        raise PathSafetyError(f"Path outside repo root: {relative_path}")
    # Reject .git paths
    if ".git" in normalized.split(os.sep):
        raise PathSafetyError(f".git path not allowed: {relative_path}")
    return joined

class CodeApplier:
    def __init__(self, repo_root: str):
        self.repo_root = repo_root

    def _staging_dir(self, request_id: int) -> str:
        return os.path.join(self.repo_root, STAGING_BASE, str(request_id))

    async def apply(self, request_id: int) -> dict:
        staging = self._staging_dir(request_id)
        manifest_path = os.path.join(staging, "rollback_manifest.json")
        mod_dir = os.path.join(staging, "modified_files")
        orig_dir = os.path.join(staging, "original_files")

        if not os.path.exists(mod_dir):
            raise RuntimeError(f"No modified_files found in staging/{request_id}")

        manifest = {"files": [], "created_at": __import__("datetime").datetime.utcnow().isoformat()}
        applied_files = []

        for root, dirs, files in os.walk(mod_dir):
            for f in files:
                rel_path = os.path.relpath(os.path.join(root, f), mod_dir)
                safe_path = safe_path_join(self.repo_root, rel_path)

                # Save original reference
                orig_path = os.path.join(orig_dir, rel_path) if os.path.exists(os.path.join(orig_dir, rel_path)) else safe_path
                manifest["files"].append({
                    "path": rel_path,
                    "original": os.path.relpath(orig_path, self.repo_root) if os.path.exists(orig_path) else rel_path,
                    "staging": os.path.relpath(os.path.join(root, f), self.repo_root),
                })

                # Copy from modified_files to actual directory
                os.makedirs(os.path.dirname(safe_path), exist_ok=True)
                shutil.copy2(os.path.join(root, f), safe_path)
                applied_files.append(rel_path)

        # Write manifest
        with open(manifest_path, "w") as mf:
            json.dump(manifest, mf, indent=2)

        return {
            "applied_files": applied_files,
            "manifest_path": manifest_path,
            "count": len(applied_files),
        }

    async def rollback(self, request_id: int) -> dict:
        staging = self._staging_dir(request_id)
        manifest_path = os.path.join(staging, "rollback_manifest.json")

        if not os.path.exists(manifest_path):
            raise RuntimeError(f"No rollback_manifest found for request {request_id}")

        with open(manifest_path) as f:
            manifest = json.load(f)

        rolled_back = []
        for entry in manifest.get("files", []):
            rel_path = entry["path"]
            safe_path = safe_path_join(self.repo_root, rel_path)

            # Original file path
            orig_rel = entry["original"]
            orig_full = os.path.join(self.repo_root, orig_rel) if not os.path.isabs(orig_rel) else os.path.join(self.repo_root, rel_path)

            if os.path.exists(orig_full):
                os.makedirs(os.path.dirname(safe_path), exist_ok=True)
                shutil.copy2(orig_full, safe_path)
                rolled_back.append(rel_path)

        return {
            "rolled_back_files": rolled_back,
            "count": len(rolled_back),
        }
