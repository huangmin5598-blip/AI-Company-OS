#!/usr/bin/env python3
"""
v0.28 — Manifest Validator

Validate all config YAML files for parseability, cross-references,
and git tracking hygiene.

Usage:
    python3 scripts/manifest_validator.py validate

Exit codes:
    0 — All checks pass
    1 — One or more checks failed
"""

import os
import subprocess
import sys
import yaml


# ── Paths ─────────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))

_MANIFESTS = {
    "company-instance.example.yaml": os.path.join(_PROJECT_ROOT, "config", "company-instance.example.yaml"),
    "runtime-manifest.yaml": os.path.join(_PROJECT_ROOT, "config", "runtime-manifest.yaml"),
    "capability-manifest.yaml": os.path.join(_PROJECT_ROOT, "config", "capability-manifest.yaml"),
    "safe-output-policy.yaml": os.path.join(_PROJECT_ROOT, "config", "safe-output-policy.yaml"),
    "capability-boundary.yaml": os.path.join(_PROJECT_ROOT, "config", "capability-boundary.yaml"),
    "capability-registry.yaml": os.path.join(_PROJECT_ROOT, "config", "capability-registry.yaml"),
}

_REAL_INSTANCE = os.path.join(_PROJECT_ROOT, "config", "company-instance.yaml")


# ── Helpers ───────────────────────────────────────────────────────

def _load_yaml(path: str, label: str) -> dict:
    """Load and parse a YAML file. Returns dict or raises."""
    with open(path, "r") as f:
        return yaml.safe_load(f)


def _result(label: str, ok: bool, detail: str = "") -> tuple:
    return (label, ok, detail)


def _print_results(results: list) -> int:
    """Print results and return exit code."""
    passed = sum(1 for r in results if r[1])
    failed = sum(1 for r in results if not r[1])
    total = len(results)

    print(f"\n{'='*60}")
    print(f"  Manifest Validator — Results")
    print(f"{'='*60}\n")

    for label, ok, detail in results:
        icon = "✅" if ok else "❌"
        print(f"  {icon} {label}")
        if detail:
            print(f"     {detail}")
    print()
    print(f"  {passed}/{total} passed, {failed} failed")

    return 1 if failed > 0 else 0


# ── Checks ─────────────────────────────────────────────────────────

def check_yaml_parseable(manifests: dict) -> list:
    """Check all YAML files are parseable."""
    results = []
    for label, path in manifests.items():
        if not os.path.exists(path):
            results.append(_result(f"{label} — file exists", False, "File not found"))
            continue
        try:
            data = _load_yaml(path, label)
            if data is None:
                results.append(_result(f"{label} — parseable", False, "Empty YAML"))
            else:
                results.append(_result(f"{label} — parseable", True))
        except yaml.YAMLError as e:
            results.append(_result(f"{label} — parseable", False, str(e)))
    return results


def check_runtime_manifest_capability_refs() -> list:
    """Check all capability_refs in runtime-manifest.yaml exist in capability-manifest.yaml."""
    results = []
    try:
        runtime = _load_yaml(_MANIFESTS["runtime-manifest.yaml"], "runtime")
        cap_manifest = _load_yaml(_MANIFESTS["capability-manifest.yaml"], "capability")
    except Exception as e:
        return [_result("runtime-manifest capability_refs", False, f"Load error: {e}")]

    if not runtime or not cap_manifest:
        return [_result("runtime-manifest capability_refs", False, "Missing manifest data")]

    # Build set of all capabilities declared in capability-manifest
    declared_caps = set()
    for actor in cap_manifest.get("actors", []):
        for cap in actor.get("capabilities", []):
            declared_caps.add(cap)

    # Check each runtime's capability_refs
    all_ok = True
    missing = []
    for rt in runtime.get("runtimes", []):
        for cref in rt.get("capability_refs", []):
            if cref not in declared_caps:
                missing.append(f"runtime '{rt['runtime_id']}' refs '{cref}' — not in any actor's capabilities")
                all_ok = False

    if all_ok:
        results.append(_result("runtime-manifest capability_refs → capability-manifest", True))
    else:
        for m in missing:
            results.append(_result("runtime-manifest capability_refs", False, m))
    return results


def check_capability_manifest_runtime_refs() -> list:
    """Check all runtime_ref in capability-manifest.yaml exist in runtime-manifest.yaml."""
    results = []
    try:
        runtime = _load_yaml(_MANIFESTS["runtime-manifest.yaml"], "runtime")
        cap_manifest = _load_yaml(_MANIFESTS["capability-manifest.yaml"], "capability")
    except Exception as e:
        return [_result("capability-manifest runtime_ref", False, f"Load error: {e}")]

    if not runtime or not cap_manifest:
        return [_result("capability-manifest runtime_ref", False, "Missing manifest data")]

    runtime_ids = {rt["runtime_id"] for rt in runtime.get("runtimes", [])}
    all_ok = True
    for actor in cap_manifest.get("actors", []):
        ref = actor.get("runtime_ref", "")
        if ref and ref not in runtime_ids:
            results.append(_result(
                "capability-manifest runtime_ref",
                False,
                f"actor '{actor['actor_id']}' refs runtime '{ref}' — not found in runtime-manifest"
            ))
            all_ok = False

    if all_ok:
        results.append(_result("capability-manifest runtime_ref → runtime-manifest", True))
    return results


def check_actor_id_boundary_match() -> list:
    """Check all actor_id in capability-manifest can be mapped in capability-boundary.yaml."""
    results = []
    try:
        cap_manifest = _load_yaml(_MANIFESTS["capability-manifest.yaml"], "capability")
        boundary = _load_yaml(_MANIFESTS["capability-boundary.yaml"], "boundary")
    except Exception as e:
        return [_result("actor_id → boundary match", False, f"Load error: {e}")]

    if not cap_manifest or not boundary:
        return [_result("actor_id → boundary match", False, "Missing manifest data")]

    boundary_actors = set(boundary.get("actors", {}).keys())
    manifest_actors = {a["actor_id"] for a in cap_manifest.get("actors", [])}

    # Actors in manifest but not in boundary (optional, not a failure)
    extra_in_manifest = manifest_actors - boundary_actors
    extra_in_boundary = boundary_actors - manifest_actors

    if extra_in_manifest:
        results.append(_result(
            "actor_id → boundary match",
            False,
            f"Manifest has actors not in boundary: {sorted(extra_in_manifest)}"
        ))
        return results

    if extra_in_boundary:
        results.append(_result(
            "actor_id → boundary match",
            True,
            f"Boundary has extra actors (ok): {sorted(extra_in_boundary)}"
        ))
    else:
        results.append(_result("actor_id → boundary match", True))

    return results


def check_instance_not_tracked() -> list:
    """Verify company-instance.yaml is NOT in git tracking."""
    results = []
    try:
        result = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "config/company-instance.yaml"],
            capture_output=True, text=True, cwd=_PROJECT_ROOT,
        )
        if result.returncode == 0:
            results.append(_result("company-instance.yaml not tracked", False, "File is tracked by git!"))
        else:
            results.append(_result("company-instance.yaml not tracked", True))
    except Exception as e:
        results.append(_result("company-instance.yaml not tracked", False, f"Git check error: {e}"))
    return results


def check_gitignore_contains_instance() -> list:
    """Verify .gitignore contains config/company-instance.yaml."""
    results = []
    gitignore = os.path.join(_PROJECT_ROOT, ".gitignore")
    if not os.path.exists(gitignore):
        return [_result(".gitignore contains company-instance.yaml", False, ".gitignore not found")]

    with open(gitignore) as f:
        content = f.read()

    if "config/company-instance.yaml" in content:
        results.append(_result(".gitignore contains company-instance.yaml", True))
    else:
        results.append(_result(".gitignore contains company-instance.yaml", False))
    return results


# ── Main ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Manifest Validator — v0.28",
    )
    parser.add_argument("command", choices=["validate"], help="Validate all manifests")
    args = parser.parse_args()

    results = []

    # 1. YAML parseability
    results.extend(check_yaml_parseable(_MANIFESTS))

    # 2. Cross-reference checks
    results.extend(check_runtime_manifest_capability_refs())
    results.extend(check_capability_manifest_runtime_refs())
    results.extend(check_actor_id_boundary_match())

    # 3. Git hygiene
    results.extend(check_instance_not_tracked())
    results.extend(check_gitignore_contains_instance())

    # Print and exit
    exit_code = _print_results(results)
    sys.exit(exit_code)


if __name__ == "__main__":
    import argparse
    main()
