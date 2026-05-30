#!/usr/bin/env python3
"""
v0.15 — Skill Registry Contract Test

Verifies the YAML-based Skill Registry routing without needing a backend.
Tests can run standalone (just need pyyaml).
"""
import json
import os
import sys

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

PASS = 0
FAIL = 0


def test(name: str, condition: bool, detail: str = ""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✅ {name}")
    else:
        FAIL += 1
        print(f"  ❌ {name} — {detail}")


def step_header(s: str):
    print(f"\n{'='*60}")
    print(f" {s}")
    print(f"{'='*60}")


def run_all():
    print("=" * 70)
    print(" v0.15 — Skill Registry Contract Test")
    print("=" * 70)

    from app.services.skill_registry import load, get_contract, list_skills, list_task_types, ROUTING_UNKNOWN

    # 1. Load and verify basics
    step_header("1. Registry loads correctly")
    cache = load(force_reload=True)
    test("YAML loaded successfully", len(cache) > 0, f"{len(cache)} task types")
    test("5 skills registered", len(list_skills()) == 5, str(len(list_skills())))

    # 2. Known task types route correctly
    step_header("2. Known task_type routing")
    cases = [
        ("research_summary", "research_summary", "research-agent", "openclaw", "low", False),
        ("finance_analysis", "finance_analysis", "finance-analyst", "openclaw", "medium", True),
        ("amazon_seller_analysis", "amazon_seller_analysis", "amazon-seller", "openclaw", "medium", True),
        ("opportunity_scan", "opportunity_scan", "research-agent", "openclaw", "low", False),
        ("code_change", "code_change", "codex", "code_bridge", "high", True),
    ]
    for task_type, expected_skill, expected_agent, expected_runtime, expected_risk, expected_approval in cases:
        r = get_contract(task_type)
        test(f"'{task_type}' → status=ok", r.status == "ok", str(r.status))
        test(f"'{task_type}' → skill={expected_skill}",
             r.contract.skill_id == expected_skill, r.contract.skill_id)
        test(f"'{task_type}' → agent={expected_agent}",
             r.contract.default_agent == expected_agent, r.contract.default_agent)
        test(f"'{task_type}' → runtime={expected_runtime}",
             r.contract.runtime == expected_runtime, r.contract.runtime)
        test(f"'{task_type}' → risk={expected_risk}",
             r.contract.risk_level == expected_risk, r.contract.risk_level)
        test(f"'{task_type}' → approval={expected_approval}",
             r.contract.approval_required == expected_approval, str(r.contract.approval_required))
        test(f"'{task_type}' → has routing_reason",
             bool(r.contract.routing_reason), r.contract.routing_reason[:60])

    # 3. Old compatible task types still work
    step_header("3. Compat: old task_type values still route")
    compat_cases = [
        ("research", "research_summary"),
        ("market_analysis", "research_summary"),
        ("report_generation", "research_summary"),
        ("read_context_and_write_summary", "research_summary"),
        ("business_report", "finance_analysis"),
        ("code_build", "code_change"),
        ("feature_implementation", "code_change"),
        ("external_data", "amazon_seller_analysis"),
    ]
    for task_type, expected_skill in compat_cases:
        r = get_contract(task_type)
        test(f"'{task_type}' → {expected_skill}",
             r.status == "ok" and r.contract.skill_id == expected_skill,
             f"{r.status}/{r.contract.skill_id}")

    # 4. Unknown task type → needs_review
    step_header("4. Unknown task_type → needs_review")
    unknown_cases = ["totally_unknown_task", "customer_support", "deploy", "publish"]
    for task_type in unknown_cases:
        r = get_contract(task_type)
        test(f"'{task_type}' → needs_review",
             r.status == ROUTING_UNKNOWN,
             f"{r.status} ({r.reason[:50]})")
        test(f"'{task_type}' → no contract",
             r.contract is None,
             str(r.contract))

    # 5. Skill Registry Result → to_dict()
    step_header("5. Result serialization")
    r = get_contract("research_summary")
    d = r.to_dict()
    test("to_dict has status", d.get("status") == "ok", str(d.get("status")))
    test("to_dict has skill_id", d.get("skill_id") == "research_summary", d.get("skill_id"))
    test("to_dict has routing_reason", bool(d.get("routing_reason")), d.get("routing_reason", "")[:50])

    # 6. List functions work
    step_header("6. Listing functions")
    skills = list_skills()
    test(f"list_skills returns {len(skills)} skills", len(skills) == 5, str(skills))
    ttypes = list_task_types()
    test(f"list_task_types returns {len(ttypes)} types", len(ttypes) >= 17, str(len(ttypes)))
    test("research_summary in task_types", "research_summary" in ttypes)
    test("code_change in task_types", "code_change" in ttypes)

    total = PASS + FAIL
    print(f"\n{'='*70}")
    print(f" Results: {PASS}/{total} passed, {FAIL}/{total} failed")
    if FAIL == 0:
        print(" ✅ ALL SKILL REGISTRY TESTS PASSED")
    return FAIL == 0


if __name__ == "__main__":
    success = run_all()
    sys.exit(0 if success else 1)
