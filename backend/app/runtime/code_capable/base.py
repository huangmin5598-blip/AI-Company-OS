# @PRODUCT Code-Capable Runtime — v0.9
"""Base classes and result types for Code-Capable Runtime adapters."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional


# ── Result Types ──


@dataclass
class PlanResult:
    """Result from generate_plan()."""

    plan_summary: str
    """Natural language description of what will be changed and how."""
    impact_scope: str
    """Description of affected components, services, and risk."""
    risk_level: str  # low / medium / high
    """Risk assessment for the proposed change."""
    files_expected: list[str]
    """List of file paths expected to be modified."""
    raw_output: str = ""
    """Full raw output from the CLI for audit purposes."""


@dataclass
class PatchResult:
    """Result from generate_patch()."""

    patch_diff: str
    """Git diff format string of the changes."""
    files_changed: list[str]
    """Actual list of file paths that were changed."""
    diff_summary: str
    """Natural language summary of the diff (lines added/removed, files)."""
    raw_output: str = ""
    """Full raw output from the CLI for audit purposes."""


@dataclass
class CheckResult:
    """Result from run_checks()."""

    build_passed: Optional[bool] = None
    build_output: str = ""
    lint_passed: Optional[bool] = None
    lint_output: str = ""
    lint_warnings: list[str] = field(default_factory=list)
    typecheck_passed: Optional[bool] = None
    typecheck_output: str = ""
    backend_import_passed: Optional[bool] = None
    backend_import_output: str = ""
    checks_passed: bool = False
    """True only when ALL blocking checks pass."""
    has_warnings: bool = False
    """True when non-blocking warnings exist but blocking checks pass."""
    raw_output: str = ""


@dataclass
class HealthResult:
    """Result from health_check()."""

    online: bool
    runtime_type: str
    version: str = ""
    capabilities: list[str] = field(default_factory=list)
    error: str = ""


# ── Abstract Base Class ──


class CodeCapableAdapter(ABC):
    """Abstract interface for all Code-Capable Runtimes.

    Implementations (Codex, Claude Code) override the glue methods.
    If a runtime doesn't support a capability, raise NotImplementedError.
    """

    def __init__(self, runtime_id: str, display_name: str):
        self._runtime_id = runtime_id
        self._display_name = display_name

    @property
    def runtime_id(self) -> str:
        return self._runtime_id

    @property
    def name(self) -> str:
        return self._display_name

    @property
    @abstractmethod
    def runtime_type(self) -> str:
        """Return 'codex' or 'claude_code'."""

    @abstractmethod
    async def generate_plan(self, problem: str, context: dict) -> PlanResult:
        """Analyze code and generate a natural language modification plan.

        Args:
            problem: Natural language description of what needs to change.
            context: Dict with keys like 'workdir', 'relevant_files', etc.

        Returns:
            PlanResult with plan_summary, impact_scope, risk_level, files_expected.
        """

    @abstractmethod
    async def generate_patch(self, plan: PlanResult, workdir: str) -> PatchResult:
        """Generate a git diff patch based on an approved plan.

        Args:
            plan: The approved PlanResult (plan_approved status).
            workdir: The project working directory (read-only access).

        Returns:
            PatchResult with patch_diff, files_changed, diff_summary.
        """

    async def run_checks(self, check_workspace: str) -> CheckResult:
        """Run automated checks in an isolated workspace.

        Default raises NotImplementedError — override in adapter if supported.
        The code_bridge checks_runner handles the actual build/lint execution.
        """
        raise NotImplementedError(
            f"{self.name} does not support run_checks. "
            "Use the code_bridge checks_runner instead."
        )

    @abstractmethod
    async def health_check(self) -> HealthResult:
        """Check if the runtime is available and return capabilities."""

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
