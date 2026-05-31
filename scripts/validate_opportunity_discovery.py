#!/usr/bin/env python3
"""
v0.32 — Validate Opportunity Discovery Output

Schema validation + boundary checks for candidate signals.
Run before release to ensure no data leaks and schema compliance.

Usage:
  python3 scripts/validate_opportunity_discovery.py              # Check all candidates
  python3 scripts/validate_opportunity_discovery.py --all        # Include schema + fixtures + git
  python3 scripts/validate_opportunity_discovery.py --schema     # Schema validation only
  python3 scripts/validate_opportunity_discovery.py --git        # Git safety check only
  python3 scripts/validate_opportunity_discovery.py --fixtures   # Run fixtures through scanner
"""

import argparse
import json
import os
import re
import subprocess
import sys

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
_CANDIDATES_DIR = os.path.join(_PROJECT_ROOT, "research", "opportunity-candidates")
_SCHEMA_PATH = os.path.join(_PROJECT_ROOT, "config", "schemas", "candidate_signal.schema.json")
_FIXTURES_DIR = os.path.join(_PROJECT_ROOT, "tests", "fixtures", "opportunity_scout")

# ── Expected values ──────────────────────────────────────────

VALID_ENUMS = {
    "candidate_type": ["venture_opportunity", "os_improvement"],
    "signal_type": ["pain", "capability", "trend", "platform", "asset", "system_gap"],
    "primary_engine": ["cash_engine", "attention_engine", "platform_play",
                        "content_engine", "knowledge_asset", "os_evolution"],
    "source_type": ["user_complaint", "ai_capability", "market_trend",
                     "platform_shift", "asset_scan", "os_feedback"],
    "evidence_gate_status": ["passed", "needs_more_evidence", "weak_candidate"],
    "status": ["candidate", "promoted", "dismissed", "needs_more_evidence"],
    "recommended_route": ["promote_signal", "request_card", "request_deep_research",
                           "park", "dismiss", "create_os_improvement_task"],
}

VALID_PRODUCT_LINES = [
    "ai_company_os", "ai_seller_finance", "ai_content_products",
    "ai_game_products", "ai_short_drama", "knowledge_assets",
    "saas_microtools", "platform_ecosystem_experiments",
]

REQUIRED_FIELDS = [
    "candidate_id", "candidate_type", "title", "created_at",
    "signal_source", "primary_engine", "related_product_lines",
    "evidence_gate_status", "recommended_route", "status",
]

REQUIRED_SOURCE_FIELDS = ["source_type", "source_tier"]

REQUIRED_SCORING_DIMS = [
    "pain_score", "evidence_score", "why_now_score",
    "founder_fit_score", "asset_leverage_score", "mvp_speed_score",
    "distribution_score", "monetization_score", "attention_score",
    "os_compounding_score",
]

ID_PATTERN = re.compile(r"^CD-\d{8}-\d{3}$")


# ══════════════════════════════════════════════════════════════════════
# Checks
# ══════════════════════════════════════════════════════════════════════

def check_all():
    """Run all checks and return consolidated results."""
    print(f"{'=' * 60}")
    print(f"  AI Company OS — Opportunity Discovery Validation")
    print(f"{'=' * 60}")
    print()

    results = {"pass": 0, "fail": 0, "warn": 0, "checks": []}

    _run_check(results, "Schema Validation", check_schema)
    _run_check(results, "ID Format", check_id_formats)
    _run_check(results, "Required Fields", check_required_fields)
    _run_check(results, "Enum Values", check_enum_values)
    _run_check(results, "Scoring Completeness", check_scoring)
    _run_check(results, "Product Line Validity", check_product_lines)
    _run_check(results, "Source Ref Format", check_source_refs)
    _run_check(results, "Git Safety", check_git_safety)
    _run_check(results, "Fixtures Run Viability", check_fixtures)

    return results


def _run_check(results, name, check_fn):
    """Run a check function and record results."""
    try:
        errors = check_fn()
        if not errors:
            results["pass"] += 1
            results["checks"].append({"name": name, "status": "pass", "detail": ""})
        else:
            results["fail"] += 1
            for e in errors:
                print(f"  ❌ [{name}] {e}")
            results["checks"].append({"name": name, "status": "fail", "detail": "; ".join(errors)})
    except Exception as e:
        results["fail"] += 1
        print(f"  ❌ [{name}] Exception: {e}")
        results["checks"].append({"name": name, "status": "fail", "detail": str(e)})


def check_schema() -> list:
    """Validate all candidate JSON files against schema."""
    errors = []

    if not os.path.exists(_SCHEMA_PATH):
        return [f"Schema file not found: {_SCHEMA_PATH}"]

    try:
        import jsonschema
    except ImportError:
        return ["jsonschema not installed. Run: pip install jsonschema"]

    try:
        with open(_SCHEMA_PATH, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except Exception as e:
        return [f"Cannot load schema: {e}"]

    if not os.path.isdir(_CANDIDATES_DIR):
        return ["No candidates directory — nothing to validate"]

    for fname in sorted(os.listdir(_CANDIDATES_DIR)):
        if not fname.endswith(".json") or not fname.startswith("CD-"):
            continue
        fpath = os.path.join(_CANDIDATES_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                candidate = json.load(f)
            jsonschema.validate(instance=candidate, schema=schema)
        except jsonschema.ValidationError as e:
            errors.append(f"{fname}: schema violation — {e.message}")
        except json.JSONDecodeError as e:
            errors.append(f"{fname}: invalid JSON — {e}")
        except Exception as e:
            errors.append(f"{fname}: {e}")

    if not errors:
        print(f"  ✅ Schema validation: all candidates valid against schema")

    return errors


def check_id_formats() -> list:
    """Validate candidate ID format."""
    errors = []
    if not os.path.isdir(_CANDIDATES_DIR):
        return []

    for fname in sorted(os.listdir(_CANDIDATES_DIR)):
        if not fname.endswith(".json"):
            continue
        candidate_id = fname[:-5]  # Remove .json
        if not ID_PATTERN.match(candidate_id):
            errors.append(f"{fname}: ID '{candidate_id}' does not match CD-YYYYMMDD-NNN")
            continue
        fpath = os.path.join(_CANDIDATES_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                candidate = json.load(f)
            cid = candidate.get("candidate_id", "")
            if cid != candidate_id:
                errors.append(f"{fname}: filename ID '{candidate_id}' != internal ID '{cid}'")
        except Exception:
            pass

    return errors


def check_required_fields() -> list:
    """Check all required fields are present in each candidate."""
    errors = []
    if not os.path.isdir(_CANDIDATES_DIR):
        return []

    for fname in sorted(os.listdir(_CANDIDATES_DIR)):
        if not fname.endswith(".json") or not fname.startswith("CD-"):
            continue
        fpath = os.path.join(_CANDIDATES_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                c = json.load(f)
        except Exception:
            continue

        for field in REQUIRED_FIELDS:
            if field not in c:
                errors.append(f"{fname}: missing required field '{field}'")

        # Check nested signal_source
        source = c.get("signal_source", {})
        if source:
            for sfield in REQUIRED_SOURCE_FIELDS:
                if sfield not in source:
                    errors.append(f"{fname}: missing required signal_source field '{sfield}'")

        # Check product_lines is an array with at least 1 item
        pl = c.get("related_product_lines", [])
        if not isinstance(pl, list) or len(pl) == 0:
            errors.append(f"{fname}: related_product_lines must be non-empty array")

    return errors


def check_enum_values() -> list:
    """Check all enum fields have valid values."""
    errors = []
    if not os.path.isdir(_CANDIDATES_DIR):
        return []

    field_enums = {
        "candidate_type": VALID_ENUMS["candidate_type"],
        "signal_type": VALID_ENUMS["signal_type"],
        "primary_engine": VALID_ENUMS["primary_engine"],
        "evidence_gate_status": VALID_ENUMS["evidence_gate_status"],
        "status": VALID_ENUMS["status"],
        "recommended_route": VALID_ENUMS["recommended_route"],
    }

    for fname in sorted(os.listdir(_CANDIDATES_DIR)):
        if not fname.endswith(".json") or not fname.startswith("CD-"):
            continue
        fpath = os.path.join(_CANDIDATES_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                c = json.load(f)
        except Exception:
            continue

        # Root-level enums
        for field, valid_values in field_enums.items():
            val = c.get(field)
            if val and val not in valid_values:
                errors.append(f"{fname}: '{field}' = '{val}' not in {valid_values}")

        # signal_source.source_type
        source_type = c.get("signal_source", {}).get("source_type")
        if source_type and source_type not in VALID_ENUMS["source_type"]:
            errors.append(f"{fname}: source_type = '{source_type}' not valid")

        # product lines
        for pl in c.get("related_product_lines", []):
            if pl not in VALID_PRODUCT_LINES:
                errors.append(f"{fname}: product_line = '{pl}' not in valid list")

        # secondary engines
        for eng in c.get("secondary_engines", []):
            if eng not in VALID_ENUMS["primary_engine"]:
                errors.append(f"{fname}: secondary_engine = '{eng}' not valid")

    return errors


def check_scoring() -> list:
    """Check scoring completeness and value ranges."""
    errors = []
    if not os.path.isdir(_CANDIDATES_DIR):
        return []

    for fname in sorted(os.listdir(_CANDIDATES_DIR)):
        if not fname.endswith(".json") or not fname.startswith("CD-"):
            continue
        fpath = os.path.join(_CANDIDATES_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                c = json.load(f)
        except Exception:
            continue

        scoring = c.get("scoring", {})
        if not scoring:
            errors.append(f"{fname}: 'scoring' object missing or empty")
            continue

        for dim in REQUIRED_SCORING_DIMS:
            entry = scoring.get(dim)
            if entry is None:
                errors.append(f"{fname}: scoring missing dimension '{dim}'")
                continue
            value = entry.get("value")
            if not isinstance(value, int) or value < 1 or value > 5:
                errors.append(f"{fname}: scoring '{dim}' = {value}, expected int 1-5")

    return errors


def check_product_lines() -> list:
    """Check product line references are valid."""
    errors = []
    if not os.path.isdir(_CANDIDATES_DIR):
        return []

    for fname in sorted(os.listdir(_CANDIDATES_DIR)):
        if not fname.endswith(".json") or not fname.startswith("CD-"):
            continue
        fpath = os.path.join(_CANDIDATES_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                c = json.load(f)
        except Exception:
            continue

        pl = c.get("related_product_lines", [])
        if len(pl) > 3:
            errors.append(f"{fname}: {len(pl)} product lines (max 3)")

    return errors


def check_source_refs() -> list:
    """Check source_refs format."""
    errors = []
    if not os.path.isdir(_CANDIDATES_DIR):
        return []

    for fname in sorted(os.listdir(_CANDIDATES_DIR)):
        if not fname.endswith(".json") or not fname.startswith("CD-"):
            continue
        fpath = os.path.join(_CANDIDATES_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                c = json.load(f)
        except Exception:
            continue

        refs = c.get("signal_source", {}).get("source_refs", [])
        for ref in refs:
            if not isinstance(ref, dict):
                errors.append(f"{fname}: source_ref is not an object")
                continue
            has_url = bool(ref.get("url"))
            has_detail = bool(ref.get("detail"))
            has_excerpt = bool(ref.get("excerpt"))
            if not has_url and not has_detail:
                errors.append(f"{fname}: source_ref has neither url nor detail")

    return errors


def check_git_safety() -> list:
    """Check that no Layer 2 data is tracked by git."""
    errors = []

    try:
        result = subprocess.run(
            ["git", "ls-files", "research/"],
            capture_output=True, text=True, cwd=_PROJECT_ROOT,
        )
        tracked_research = [l for l in result.stdout.strip().split("\n") if l]
        if tracked_research:
            errors.append(f"⚠️  {len(tracked_research)} research/ files tracked in git!")
            for f in tracked_research[:5]:
                errors.append(f"  → {f}")
    except Exception:
        errors.append("Could not check git — is this a git repo?")

    # Check config/company-context.yaml
    try:
        result = subprocess.run(
            ["git", "ls-files", "config/company-context.yaml"],
            capture_output=True, text=True, cwd=_PROJECT_ROOT,
        )
        if result.stdout.strip():
            errors.append("⚠️  config/company-context.yaml is tracked in git!")
    except Exception:
        pass

    # Check .gitignore has research/
    gitignore_path = os.path.join(_PROJECT_ROOT, ".gitignore")
    if os.path.exists(gitignore_path):
        with open(gitignore_path, "r", encoding="utf-8") as f:
            content = f.read()
        if "research/" not in content:
            errors.append("⚠️  research/ not in .gitignore!")

    if not errors:
        print(f"  ✅ Git safety: no Layer 2 data tracked")

    return errors


def check_fixtures() -> list:
    """Verify all 6 fixtures exist and are parseable YAML."""
    errors = []

    expected_fixtures = [
        "fixture-01-user-complaint.yaml",
        "fixture-02-ai-capability.yaml",
        "fixture-03-market-trend.yaml",
        "fixture-04-platform-shift.yaml",
        "fixture-05-asset-scan.yaml",
        "fixture-06-os-feedback.yaml",
    ]

    if not os.path.isdir(_FIXTURES_DIR):
        return [f"Fixtures directory not found: {_FIXTURES_DIR}"]

    for fixture in expected_fixtures:
        fpath = os.path.join(_FIXTURES_DIR, fixture)
        if not os.path.exists(fpath):
            errors.append(f"Missing fixture: {fixture}")
            continue

        # Parse YAML
        try:
            import yaml
            with open(fpath, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data:
                errors.append(f"{fixture}: empty or invalid YAML")
                continue
            # Check required source fields
            if "source_type" not in data:
                errors.append(f"{fixture}: missing source_type")
        except Exception as e:
            errors.append(f"{fixture}: parse error — {e}")

    if not errors:
        print(f"  ✅ All {len(expected_fixtures)} fixtures present and parseable")

    return errors


# ══════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="v0.32 — Validate Opportunity Discovery output",
    )
    parser.add_argument("--all", action="store_true", help="Run all checks")
    parser.add_argument("--schema", action="store_true", help="Schema validation only")
    parser.add_argument("--git", action="store_true", help="Git safety check only")
    parser.add_argument("--fixtures", action="store_true", help="Fixture viability check only")
    parser.add_argument("--fields", action="store_true", help="Field boundary checks only")
    args = parser.parse_args()

    # If no specific flags, run all
    run_all = args.all or not (args.schema or args.git or args.fixtures or args.fields)
    run_schema = args.schema or run_all
    run_git = args.git or run_all
    run_fixtures = args.fixtures or run_all
    run_fields = args.fields or run_all

    results = {"pass": 0, "fail": 0, "checks": []}

    if run_schema:
        _run_check(results, "Schema Validation", check_schema)
        _run_check(results, "ID Format", check_id_formats)

    if run_fields:
        _run_check(results, "Required Fields", check_required_fields)
        _run_check(results, "Enum Values", check_enum_values)
        _run_check(results, "Scoring Completeness", check_scoring)
        _run_check(results, "Product Line Validity", check_product_lines)
        _run_check(results, "Source Ref Format", check_source_refs)

    if run_git:
        _run_check(results, "Git Safety", check_git_safety)

    if run_fixtures:
        _run_check(results, "Fixtures", check_fixtures)

    # Summary
    print()
    print(f"{'=' * 60}")
    print(f"  Results: ✅ {results['pass']} pass  ❌ {results['fail']} fail")
    print(f"{'=' * 60}")

    if results["fail"] > 0:
        sys.exit(1)
    else:
        print(f"  🎉 All checks passed!")
        sys.exit(0)


if __name__ == "__main__":
    main()
