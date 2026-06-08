"""Validated evidence envelopes for canonical execution commands."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Mapping

from app.foundation.canonical_json import canonical_json_bytes


SHA256_PATTERN = re.compile(r"^sha256:[0-9a-f]{64}$")


def _require_sha256(value: str, field: str) -> str:
    if not SHA256_PATTERN.fullmatch(value):
        raise ValueError(f"invalid_{field}")
    return value


@dataclass(frozen=True)
class RuntimeSelection:
    runtime_id: str
    runtime_type: str
    display_name: str
    adapter_module: str
    script_sha256: str
    scratch_only: bool
    registry_source: str = "disposable_test_fixture"
    production_registered: bool = False

    @classmethod
    def from_registry_row(cls, row: Mapping[str, Any]) -> "RuntimeSelection":
        try:
            config = json.loads(row["config_json"])
        except (KeyError, TypeError, json.JSONDecodeError) as exc:
            raise ValueError("invalid_runtime_registry_config") from exc
        if row.get("enabled") != 1:
            raise ValueError("runtime_registry_entry_not_enabled")
        if config.get("executor") != "controlled_builtin":
            raise ValueError("invalid_runtime_executor")
        scratch_only = config.get("scratch_only") is True
        if not scratch_only:
            raise ValueError("runtime_scratch_only_required")
        return cls(
            runtime_id=str(row["runtime_id"]),
            runtime_type=str(row["runtime_type"]),
            display_name=str(row["display_name"]),
            adapter_module=str(row["adapter_module"]),
            script_sha256=_require_sha256(
                str(config.get("script_sha256", "")),
                "script_sha256",
            ),
            scratch_only=scratch_only,
        )

    @property
    def adapter_version(self) -> str:
        return self.script_sha256

    def config_snapshot(self) -> dict[str, object]:
        return {
            "executor": "controlled_builtin",
            "script_sha256": self.script_sha256,
            "scratch_only": self.scratch_only,
        }

    def invocation_authenticity(
        self,
        *,
        wrapper: str,
        preflight_ref: str,
        preflight_hash: str,
        preflight_evidence: Mapping[str, object],
    ) -> dict[str, object]:
        _require_sha256(preflight_hash, "preflight_hash")
        if not preflight_ref.startswith("preflight://"):
            raise ValueError("invalid_preflight_ref")
        return {
            "wrapper": wrapper,
            "registry_selected": True,
            "registry_source": self.registry_source,
            "production_registered": self.production_registered,
            "script_sha256": self.script_sha256,
            "preflight_ref": preflight_ref,
            "preflight_hash": preflight_hash,
            "preflight_evidence": dict(preflight_evidence),
        }


@dataclass(frozen=True)
class AttemptResultEvidence:
    terminal_state: str
    result_ref: str
    stdout_ref: str
    stderr_ref: str
    exit_code: int
    result_payload_hash: str
    cost_summary: Mapping[str, object]
    error_code: str | None = None
    error_summary: str | None = None

    def __post_init__(self) -> None:
        if self.terminal_state not in {"succeeded", "failed"}:
            raise ValueError("invalid_attempt_terminal_state")
        _require_sha256(self.result_payload_hash, "result_payload_hash")
        for field, value in (
            ("result_ref", self.result_ref),
            ("stdout_ref", self.stdout_ref),
            ("stderr_ref", self.stderr_ref),
        ):
            if not value.startswith("scratch://"):
                raise ValueError(f"invalid_{field}")
        if self.terminal_state == "succeeded" and self.exit_code != 0:
            raise ValueError("successful_result_requires_zero_exit")
        if self.terminal_state == "failed" and self.exit_code == 0:
            raise ValueError("failed_result_requires_nonzero_exit")

    def cost_summary_json(self) -> str:
        return canonical_json_bytes(dict(self.cost_summary)).decode("utf-8")


__all__ = ["AttemptResultEvidence", "RuntimeSelection"]
