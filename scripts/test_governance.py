#!/usr/bin/env python3
"""v0.16 — Governance Test: Health, Failure Policy, Cost Summary, Budget Guard."""
import json
import os
import sys
import urllib.request

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
BACKEND_URL = "http://localhost:8001"

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


def api_get(path: str) -> dict:
    try:
        with urllib.request.urlopen(f"{BACKEND_URL}{path}", timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}


def api_post(path: str, data: dict) -> dict:
    body = json.dumps(data).encode()
    req = urllib.request.Request(f"{BACKEND_URL}{path}", data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e)}


def test_runtime_health():
    print("\n" + "=" * 60)
    print(" 1. Runtime Health Check")
    print("=" * 60)
    health = api_get("/api/v1/governance/health")
    test("API accessible", "error" not in health, str(health.get("error", "")))

    results = health.get("results", {})
    test("openclaw health returned", "openclaw" in results)
    test("codex health returned", "codex" in results)
    test("local_llm health returned", "local_llm" in results)
    test("openclaw is healthy or degraded",
         results["openclaw"]["status"] in ("healthy", "degraded"),
         results["openclaw"]["status"])
    test("all_healthy is bool", isinstance(health.get("all_healthy"), bool))


def test_cost_summary():
    print("\n" + "=" * 60)
    print(" 2. Cost Summary")
    print("=" * 60)
    cost = api_get("/api/v1/governance/cost-summary")
    test("API accessible", "error" not in cost, str(cost.get("error", "")))
    test("total_tokens >= 0", cost.get("total_tokens", -1) >= 0, str(cost.get("total_tokens")))
    test("work_order_count >= 0", cost.get("work_order_count", -1) >= 0, str(cost.get("work_order_count")))
    test("by_agent is dict", isinstance(cost.get("by_agent"), dict))
    test("by_runtime is dict", isinstance(cost.get("by_runtime"), dict))
    test("by_skill is dict", isinstance(cost.get("by_skill"), dict))


def test_budget_guard():
    print("\n" + "=" * 60)
    print(" 3. Soft Budget Guard")
    print("=" * 60)

    # Under budget
    under = api_post("/api/v1/governance/budget-check", {"total_tokens": 5000, "skill_id": "research_summary"})
    test("under budget: passed=True", under.get("passed") is True, str(under.get("passed")))
    test("under budget: no violations", under.get("violations") == [], str(under.get("violations")))

    # Over budget (research_summary: 60000 max, warn)
    over = api_post("/api/v1/governance/budget-check", {"total_tokens": 65000, "skill_id": "research_summary"})
    test("over budget: passed=False", over.get("passed") is False, str(over.get("passed")))
    test("over budget: has violations", len(over.get("violations", [])) > 0, str(over.get("violations")))
    test("over budget: action=warn",
         over["violations"][0].get("action") == "warn",
         str(over["violations"][0].get("action")))

    # Over budget (code_change: 50000 max, needs_review)
    over2 = api_post("/api/v1/governance/budget-check", {"total_tokens": 60000, "skill_id": "code_change"})
    test("code_change over budget: action=needs_review",
         over2["violations"][0].get("action") == "needs_review",
         str(over2["violations"][0].get("action")))


def test_failure_policy():
    print("\n" + "=" * 60)
    print(" 4. Failure Policy")
    print("=" * 60)
    from app.services.failure_policy import classify, FailureCode, FailureAction

    # Unknown task type
    d = classify("unknown_xyz", "low", 1)
    test("unknown task → needs_review",
         d.action == FailureAction.NEEDS_REVIEW,
         f"{d.code.value} / {d.action.value}")
    test("unknown task → code=UNKNOWN_TASK_TYPE",
         d.code == FailureCode.UNKNOWN_TASK_TYPE,
         d.code.value)

    # Runtime unhealthy
    d2 = classify("research_summary", "low", 1,
                  health_status={"openclaw": "unhealthy", "codex": "healthy"})
    test("unhealthy runtime → needs_review",
         d2.action == FailureAction.NEEDS_REVIEW,
         f"{d2.code.value} / {d2.action.value}")

    # Executor timeout, low risk → retry
    d3 = classify("read_context_and_write_summary", "low", 1,
                  executor_result={"status": "failed", "error_message": "timed out"})
    test("timeout low risk → retry",
         d3.action == FailureAction.RETRY,
         f"{d3.code.value} / {d3.action.value}")
    test("timeout low risk → can_retry=True",
         d3.can_retry is True, str(d3.can_retry))

    # Executor timeout, high risk → needs_review (no retry)
    d4 = classify("code_change", "high", 1,
                  executor_result={"status": "failed", "error_message": "timed out"})
    test("timeout high risk → needs_review",
         d4.action == FailureAction.NEEDS_REVIEW,
         f"{d4.code.value} / {d4.action.value}")
    test("timeout high risk → can_retry=False",
         d4.can_retry is False, str(d4.can_retry))

    # Consecutive failures
    d5 = classify("research_summary", "low", 3)
    test("consecutive failures → escalate",
         d5.action == FailureAction.ESCALATE,
         f"{d5.code.value} / {d5.action.value}")

    # to_dict serialization
    d6_dict = d.to_dict()
    test("to_dict has failure_code", "failure_code" in d6_dict, str(d6_dict))
    test("to_dict has action", "action" in d6_dict, str(d6_dict))
    test("to_dict has reason", "reason" in d6_dict, str(d6_dict))


def run():
    print("=" * 70)
    print(" v0.16 — Runtime Governance Lite")
    print("=" * 70)

    test_runtime_health()
    test_cost_summary()
    test_budget_guard()
    test_failure_policy()

    total = PASS + FAIL
    print(f"\n{'='*70}")
    print(f" Results: {PASS}/{total} passed, {FAIL}/{total} failed")
    if FAIL == 0:
        print(" ✅ ALL GOVERNANCE TESTS PASSED")
    return FAIL == 0


if __name__ == "__main__":
    success = run()
    sys.exit(0 if success else 1)
