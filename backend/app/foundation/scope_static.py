"""AST-based enforcement for canonical repository scope arguments."""

from __future__ import annotations

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


PROTECTED_METHODS = frozenset(
    {
        "get",
        "get_by_id",
        "list",
        "search",
        "count",
        "export",
        "autocomplete",
        "add",
        "create",
        "update",
        "delete",
        "request_approval",
        "apply_approval_decision",
        "mark_running_after_claim",
        "mark_waiting_review_after_result",
        "apply_review_outcome",
        "capture_artifact",
        "create_candidate",
        "approve_candidate",
    }
)
MUTATOR_METHODS = frozenset({"add", "create", "update", "delete"})
SCOPED_BASES = frozenset(
    {"ScopedReadRepository", "ScopedCommandRepository", "ScopedRepository"}
)


@dataclass(frozen=True)
class ScopeStaticViolation:
    path: str
    line: int
    code: str
    message: str


def _argument_names(node: ast.FunctionDef | ast.AsyncFunctionDef) -> set[str]:
    positional = [*node.args.posonlyargs, *node.args.args]
    return {argument.arg for argument in [*positional, *node.args.kwonlyargs]}


def _base_name(node: ast.expr) -> str | None:
    if isinstance(node, ast.Subscript):
        return _base_name(node.value)
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def scan_repository_source(source: str, *, path: str = "<memory>") -> list[ScopeStaticViolation]:
    tree = ast.parse(source, filename=path)
    violations: list[ScopeStaticViolation] = []

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imported_names: set[str] = set()
            if isinstance(node, ast.Import):
                imported_names = {alias.name for alias in node.names}
            else:
                imported_names = {alias.name for alias in node.names}
            if "get_sync_session" in imported_names:
                violations.append(
                    ScopeStaticViolation(
                        path,
                        node.lineno,
                        "unscoped_session_factory",
                        "Canonical repositories may not import get_sync_session",
                    )
                )

        if not isinstance(node, ast.ClassDef) or not node.name.endswith("Repository"):
            continue
        if node.name in SCOPED_BASES:
            continue
        base_names = {_base_name(base) for base in node.bases}
        scoped_bases = SCOPED_BASES.intersection(base_names)
        if not scoped_bases:
            violations.append(
                ScopeStaticViolation(
                    path,
                    node.lineno,
                    "repository_must_inherit_scoped_base",
                    f"{node.name} must inherit a scoped repository base",
                )
            )
        read_only_repository = scoped_bases == {"ScopedReadRepository"}
        for member in node.body:
            if not isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if member.name not in PROTECTED_METHODS:
                continue
            if read_only_repository and member.name in MUTATOR_METHODS:
                violations.append(
                    ScopeStaticViolation(
                        path,
                        member.lineno,
                        "read_repository_mutator_forbidden",
                        f"{node.name}.{member.name} is forbidden on a read repository",
                    )
                )
            if "scope" not in _argument_names(member):
                violations.append(
                    ScopeStaticViolation(
                        path,
                        member.lineno,
                        "missing_scope_argument",
                        f"{node.name}.{member.name} must require a scope argument",
                    )
                )
    return violations


def scan_repository_paths(paths: Iterable[Path]) -> list[ScopeStaticViolation]:
    violations: list[ScopeStaticViolation] = []
    for path in sorted(paths, key=lambda item: item.as_posix()):
        if path.name == "__init__.py":
            continue
        violations.extend(
            scan_repository_source(path.read_text(encoding="utf-8"), path=str(path))
        )
    return violations
