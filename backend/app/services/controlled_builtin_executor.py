"""Controlled execution of one trusted builtin; this is not a sandbox."""

from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from typing import Mapping

from app.foundation.canonical_json import canonical_json_bytes
from app.foundation.context import ScopeContext
from app.foundation.execution_evidence import AttemptResultEvidence
from app.models.foundation_execution import WorkAttempt


REPO_ROOT = Path(__file__).resolve().parents[3]
BUILTIN_SCRIPT = (
    REPO_ROOT / "scripts/builtins/vs001_echo_markdown.py"
).resolve()
RUNTIME_ID = "builtin.vs001_echo_markdown"
ADAPTER_MODULE = "app.services.controlled_builtin_executor"
EXECUTOR_NAME = "controlled_builtin"
INPUT_REF = "scratch://input"
OUTPUT_REF = "scratch://output"
MAX_INPUT_BYTES = 64 * 1024
MAX_RESULT_BYTES = 256 * 1024
MAX_CAPTURE_BYTES = 64 * 1024
DEFAULT_TIMEOUT_SECONDS = 10.0
MAX_TIMEOUT_SECONDS = 30.0
SYSTEM_TEMP_ROOT = Path(tempfile.gettempdir()).resolve()

_FORBIDDEN_IMPORT_ROOTS = {
    "asyncio",
    "ctypes",
    "ftplib",
    "http",
    "importlib",
    "multiprocessing",
    "requests",
    "socket",
    "ssl",
    "subprocess",
    "threading",
    "urllib",
}
_FORBIDDEN_CALL_NAMES = {
    "compile",
    "eval",
    "exec",
    "__import__",
}


class ControlledBuiltinRejected(RuntimeError):
    """Raised when the fixed executor contract fails closed."""


def _sha256_bytes(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _canonical_config(attempt: WorkAttempt) -> dict[str, object]:
    try:
        config = json.loads(attempt.runtime_config_snapshot_json)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ControlledBuiltinRejected("invalid_runtime_config_snapshot") from exc
    if not isinstance(config, dict):
        raise ControlledBuiltinRejected("invalid_runtime_config_snapshot")
    return config


def _canonical_refs(value: str, field: str) -> list[str]:
    try:
        refs = json.loads(value)
    except (TypeError, json.JSONDecodeError) as exc:
        raise ControlledBuiltinRejected(f"invalid_{field}") from exc
    if not isinstance(refs, list) or not all(isinstance(ref, str) for ref in refs):
        raise ControlledBuiltinRejected(f"invalid_{field}")
    return refs


def _validate_builtin_source(path: Path) -> None:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (OSError, SyntaxError) as exc:
        raise ControlledBuiltinRejected("builtin_source_unreadable") from exc
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots = {alias.name.split(".", 1)[0] for alias in node.names}
            if roots & _FORBIDDEN_IMPORT_ROOTS:
                raise ControlledBuiltinRejected("builtin_network_capability_forbidden")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".", 1)[0]
            if root in _FORBIDDEN_IMPORT_ROOTS:
                raise ControlledBuiltinRejected("builtin_network_capability_forbidden")
        elif (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in _FORBIDDEN_CALL_NAMES
        ):
            raise ControlledBuiltinRejected("builtin_dynamic_execution_forbidden")


def _require_within(path: Path, root: Path, error: str) -> None:
    try:
        common = os.path.commonpath((str(path), str(root)))
    except ValueError as exc:
        raise ControlledBuiltinRejected(error) from exc
    if common != str(root):
        raise ControlledBuiltinRejected(error)


def _require_directory_chain_without_symlinks(path: Path, root: Path) -> None:
    current = path
    while True:
        if current.is_symlink():
            raise ControlledBuiltinRejected("scratch_symlink_forbidden")
        if current == root:
            return
        if current.parent == current:
            raise ControlledBuiltinRejected("scratch_root_outside_allowed_root")
        current = current.parent


@dataclass(frozen=True)
class ControlledBuiltinPreflight:
    attempt_id: str
    work_order_id: str
    tenant_id: str
    workspace_id: str
    script_path: str
    script_sha256: str
    scratch_root: str
    allowed_temp_root: str
    input_ref: str
    output_ref: str
    decision_hash: str

    @property
    def evidence_ref(self) -> str:
        return f"preflight://{self.attempt_id}/{self.decision_hash}"

    def payload(self) -> dict[str, str]:
        return {
            "attempt_id": self.attempt_id,
            "work_order_id": self.work_order_id,
            "tenant_id": self.tenant_id,
            "workspace_id": self.workspace_id,
            "script_path": self.script_path,
            "script_sha256": self.script_sha256,
            "scratch_root": self.scratch_root,
            "allowed_temp_root": self.allowed_temp_root,
            "input_ref": self.input_ref,
            "output_ref": self.output_ref,
        }


@dataclass(frozen=True)
class ControlledBuiltinRun:
    preflight_ref: str
    runtime_session_id: str
    evidence: AttemptResultEvidence


def preflight_controlled_builtin(
    attempt: WorkAttempt,
    scope: ScopeContext,
    *,
    scratch_root: Path,
    allowed_temp_root: Path,
) -> ControlledBuiltinPreflight:
    if attempt.state != "claimed":
        raise ControlledBuiltinRejected("preflight_requires_claimed_attempt")
    if (
        attempt.tenant_id != scope.tenant_id
        or attempt.workspace_id != scope.workspace_id
        or attempt.scope_key != scope.scope_key
    ):
        raise ControlledBuiltinRejected("preflight_scope_mismatch")
    if attempt.runtime_adapter_id != RUNTIME_ID:
        raise ControlledBuiltinRejected("preflight_runtime_id_mismatch")

    config = _canonical_config(attempt)
    expected_config = {
        "executor": EXECUTOR_NAME,
        "script_sha256": attempt.runtime_adapter_version,
        "scratch_only": True,
    }
    if config != expected_config:
        raise ControlledBuiltinRejected("preflight_runtime_config_mismatch")

    if not BUILTIN_SCRIPT.is_file() or BUILTIN_SCRIPT.is_symlink():
        raise ControlledBuiltinRejected("builtin_script_not_regular")
    _validate_builtin_source(BUILTIN_SCRIPT)
    actual_hash = _sha256_file(BUILTIN_SCRIPT)
    if actual_hash != attempt.runtime_adapter_version:
        raise ControlledBuiltinRejected("builtin_script_hash_mismatch")

    read_refs = _canonical_refs(
        attempt.allowed_read_refs_json,
        "allowed_read_refs",
    )
    write_refs = _canonical_refs(
        attempt.allowed_write_refs_json,
        "allowed_write_refs",
    )
    if read_refs != [INPUT_REF] or write_refs != [OUTPUT_REF]:
        raise ControlledBuiltinRejected("preflight_path_contract_mismatch")

    if scratch_root.is_symlink():
        raise ControlledBuiltinRejected("scratch_symlink_forbidden")
    allowed = allowed_temp_root.resolve(strict=True)
    scratch = scratch_root.resolve(strict=True)
    if not allowed.is_dir() or not scratch.is_dir() or scratch == allowed:
        raise ControlledBuiltinRejected("invalid_scratch_root")
    _require_within(
        allowed,
        SYSTEM_TEMP_ROOT,
        "allowed_root_outside_system_temp",
    )
    _require_within(scratch, allowed, "scratch_root_outside_allowed_root")
    _require_directory_chain_without_symlinks(scratch, allowed)
    if any(scratch.iterdir()):
        raise ControlledBuiltinRejected("scratch_root_not_empty")

    payload = {
        "attempt_id": attempt.attempt_id,
        "work_order_id": attempt.work_order_id,
        "tenant_id": attempt.tenant_id,
        "workspace_id": attempt.workspace_id,
        "script_path": str(BUILTIN_SCRIPT),
        "script_sha256": actual_hash,
        "scratch_root": str(scratch),
        "allowed_temp_root": str(allowed),
        "input_ref": INPUT_REF,
        "output_ref": OUTPUT_REF,
    }
    decision_hash = _sha256_bytes(canonical_json_bytes(payload))
    return ControlledBuiltinPreflight(**payload, decision_hash=decision_hash)


def _verify_preflight(preflight: ControlledBuiltinPreflight) -> Path:
    expected_hash = _sha256_bytes(canonical_json_bytes(preflight.payload()))
    if preflight.decision_hash != expected_hash:
        raise ControlledBuiltinRejected("preflight_decision_hash_mismatch")
    if Path(preflight.script_path).resolve() != BUILTIN_SCRIPT:
        raise ControlledBuiltinRejected("preflight_script_path_mismatch")
    if _sha256_file(BUILTIN_SCRIPT) != preflight.script_sha256:
        raise ControlledBuiltinRejected("builtin_script_changed_after_preflight")
    scratch = Path(preflight.scratch_root)
    allowed = Path(preflight.allowed_temp_root)
    if not allowed.is_dir() or allowed.is_symlink():
        raise ControlledBuiltinRejected("allowed_temp_root_changed_after_preflight")
    _require_within(
        allowed.resolve(),
        SYSTEM_TEMP_ROOT,
        "allowed_root_outside_system_temp",
    )
    _require_within(
        scratch.resolve(),
        allowed.resolve(),
        "scratch_root_outside_allowed_root",
    )
    if not scratch.is_dir() or scratch.is_symlink() or any(scratch.iterdir()):
        raise ControlledBuiltinRejected("scratch_changed_after_preflight")
    return scratch


def _bounded_capture(value: str, field: str) -> bytes:
    payload = value.encode("utf-8", errors="replace")
    if len(payload) > MAX_CAPTURE_BYTES:
        raise ControlledBuiltinRejected(f"{field}_limit_exceeded")
    return payload


def _write_bytes(path: Path, payload: bytes) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(payload)
    os.replace(temporary, path)


def execute_controlled_builtin(
    preflight: ControlledBuiltinPreflight,
    payload: Mapping[str, object],
    *,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
) -> ControlledBuiltinRun:
    """Execute the fixed trusted builtin without any database transaction."""
    scratch = _verify_preflight(preflight)
    if timeout_seconds <= 0 or timeout_seconds > MAX_TIMEOUT_SECONDS:
        raise ValueError("invalid_timeout_seconds")

    input_directory = scratch / "input"
    output_directory = scratch / "output"
    input_directory.mkdir(mode=0o700)
    output_directory.mkdir(mode=0o700)
    input_path = input_directory / "input.json"
    result_path = output_directory / "result.md"
    stdout_path = output_directory / "stdout.txt"
    stderr_path = output_directory / "stderr.txt"
    for path in (input_path, result_path, stdout_path, stderr_path):
        _require_within(path.resolve(strict=False), scratch, "scratch_path_escape")
        if path.is_symlink():
            raise ControlledBuiltinRejected("scratch_symlink_forbidden")

    input_bytes = canonical_json_bytes(dict(payload))
    if len(input_bytes) > MAX_INPUT_BYTES:
        raise ControlledBuiltinRejected("builtin_input_limit_exceeded")
    _write_bytes(input_path, input_bytes)

    started = time.monotonic()
    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-I",
                "-S",
                str(BUILTIN_SCRIPT),
                "--input",
                str(input_path),
                "--output",
                str(result_path),
            ],
            cwd=scratch,
            env={
                "LANG": "C",
                "LC_ALL": "C",
                "PATH": os.defpath,
                "PYTHONIOENCODING": "utf-8",
            },
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
        )
        exit_code = completed.returncode
        stdout = _bounded_capture(completed.stdout, "stdout")
        stderr = _bounded_capture(completed.stderr, "stderr")
        error_code = None if exit_code == 0 else "controlled_builtin_failed"
        error_summary = None if exit_code == 0 else "builtin returned non-zero"
    except subprocess.TimeoutExpired as exc:
        exit_code = 124
        stdout = _bounded_capture(
            (exc.stdout or "") if isinstance(exc.stdout, str) else "",
            "stdout",
        )
        stderr = _bounded_capture(
            (exc.stderr or "") if isinstance(exc.stderr, str) else "",
            "stderr",
        )
        error_code = "controlled_builtin_timeout"
        error_summary = "builtin exceeded execution timeout"

    _write_bytes(stdout_path, stdout)
    _write_bytes(stderr_path, stderr)
    if exit_code != 0 and not result_path.exists():
        _write_bytes(
            result_path,
            f"# Controlled builtin failure\n\n{error_summary}\n".encode("utf-8"),
        )
    if (
        not result_path.is_file()
        or result_path.is_symlink()
        or result_path.stat().st_size > MAX_RESULT_BYTES
    ):
        raise ControlledBuiltinRejected("invalid_builtin_result")
    for path in scratch.rglob("*"):
        if path.is_symlink():
            raise ControlledBuiltinRejected("scratch_symlink_forbidden")
        _require_within(path.resolve(), scratch, "scratch_path_escape")

    duration_ms = max(0, round((time.monotonic() - started) * 1000))
    evidence = AttemptResultEvidence(
        terminal_state="succeeded" if exit_code == 0 else "failed",
        result_ref="scratch://output/result.md",
        stdout_ref="scratch://output/stdout.txt",
        stderr_ref="scratch://output/stderr.txt",
        exit_code=exit_code,
        result_payload_hash=_sha256_file(result_path),
        cost_summary={
            "amount": "0",
            "currency": "USD",
            "duration_ms": duration_ms,
            "source": "controlled_builtin",
        },
        error_code=error_code,
        error_summary=error_summary,
    )
    return ControlledBuiltinRun(
        preflight_ref=preflight.evidence_ref,
        runtime_session_id=f"builtin:{preflight.attempt_id}",
        evidence=evidence,
    )


__all__ = [
    "BUILTIN_SCRIPT",
    "ControlledBuiltinPreflight",
    "ControlledBuiltinRejected",
    "ControlledBuiltinRun",
    "execute_controlled_builtin",
    "preflight_controlled_builtin",
]
