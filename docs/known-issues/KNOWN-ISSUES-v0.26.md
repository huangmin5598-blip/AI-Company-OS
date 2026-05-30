# Known Issues — v0.26

> Record of pre-existing test errors that do not block v0.26.
> Created: 2026-05-30
> Test baseline: 21 passed, 12 errors (all from same 3 root causes)

---

## KI-001: `test()` helper function name collision with pytest fixture resolution

| Field | Value |
|-------|-------|
| **Issue ID** | KI-001 |
| **Error summary** | `fixture 'name' not found` — pytest discovers `def test(name, condition, detail)` as a test function, interprets `name` as a fixture parameter, and fails to find it. |
| **Observed command** | `python3 -m pytest` in project root |
| **Affected area** | 3 standalone test scripts (designed to run with `python3 scripts/xxx.py`, not pytest) |
| **Affected files** | `scripts/test_callback_api_contract.py` (line 35), `scripts/test_governance.py` (line 22), `scripts/test_skill_registry.py` (line 19) |
| **Cascade count** | 3 errors (one per file) |
| **Root cause** | Each file defines a helper function `def test(name: str, condition: bool, detail: str = "")` for inline assertion tracking. pytest auto-discovers any function starting with "test" and interprets positional args as fixture references. These files are standalone scripts with `if __name__ == "__main__":` blocks — they are not pytest-native test suites. |
| **Impact** | These 3 scripts cannot participate in `pytest` test discovery. They must be run directly: `python3 scripts/test_callback_api_contract.py`. Their actual test logic (6, 4, 8 test cases respectively) is unaffected when run standalone. |
| **Why it does not block v0.26** | These scripts are standalone test harnesses, not core infrastructure. They have no functional dependency with v0.26 Evidence or GitHub Refresh work. The 21 actual pytest-native tests all pass. |
| **Planned handling** | **Fix in v0.27**: Rename helper function to `assert_that()` or `verify()` to avoid pytest discovery collision. Alternatively, prefix with `_test()` or move to a shared `scripts/test_helpers.py`. |
| **Owner / next version** | Hermes / v0.27 |

---

## KI-002: Missing `bridge` fixture in OpenClaw Bridge v2 integration tests

| Field | Value |
|-------|-------|
| **Issue ID** | KI-002 |
| **Error summary** | `fixture 'bridge' not found` — 8 test functions declare `bridge: OpenClawBridge` as a parameter but no pytest fixture provides it. |
| **Observed command** | `python3 -m pytest` in project root |
| **Affected area** | `scripts/test_openclaw_bridge_v2.py` |
| **Affected functions** | `test_create_task_card` (line 69), `test_claim_lifecycle` (line 111), `test_polling_no_result` (line 138), `test_result_manifest` (line 151), `test_malformed_result` (line 208), `test_missing_fields_result` (line 234), `test_timeout` (line 258), `test_get_tasks` (line 515) |
| **Cascade count** | 8 errors (all from same root cause) |
| **Root cause** | These 8 test functions originally expected a shared `OpenClawBridge` instance passed as a parameter. The `test_bridge_creation()` (line 59, no fixture param) creates and returns a bridge instance, but the downstream tests never received it via a pytest fixture chain. No `conftest.py` or fixture definition exists for `bridge`. |
| **Impact** | These 8 integration tests cannot run via `pytest`. However, `test_bridge_creation()` (no fixture), `test_execution_mode_handler()` (line 276), `test_callback_service()` (line 304), `test_full_work_order_flow()` (line 350), and `test_callback_endpoint_mock()` (line 419) **all pass** — covering the same functionality without the fixture dependency. |
| **Why it does not block v0.26** | The core integration coverage is already provided by the 5 passing tests in the same file. The 8 bridge-parameter tests are a subset that can be refactored to match the pattern used by the passing tests. v0.26 touches no bridge or callback code. |
| **Planned handling** | **Fix in v0.27**: Refactor the 8 affected test functions to instantiate their own `OpenClawBridge()` (matching the pattern in `test_bridge_creation`). Either remove the `bridge` parameter or add a proper `@pytest.fixture` in `conftest.py`. |
| **Owner / next version** | Hermes / v0.27 |

---

## KI-003: `test()` helper function in `test_openclaw_bridge_v2.py` (same pattern as KI-001)

| Field | Value |
|-------|-------|
| **Issue ID** | KI-003 |
| **Error summary** | `fixture 'name' not found` — same root cause as KI-001: the otherwise-passing `test()` helper at line 36 is discovered by pytest as a test function. |
| **Observed command** | `python3 -m pytest` in project root |
| **Affected area** | `scripts/test_openclaw_bridge_v2.py` |
| **Affected function** | `test` (line 36) |
| **Cascade count** | 1 error |
| **Root cause** | Same as KI-001: `def test(name: str, condition: bool, detail: str = "")` is a helper function for inline assertion tracking. pytest interprets `name` as a fixture reference. |
| **Impact** | This file's `test()` helper cannot be discovered by pytest. All 5 real test functions that don't take `bridge` as a parameter (`test_bridge_creation`, `test_execution_mode_handler`, `test_callback_service`, `test_full_work_order_flow`, `test_callback_endpoint_mock`) pass correctly. |
| **Why it does not block v0.26** | Same reasoning as KI-001. v0.26 touches no test infrastructure. |
| **Planned handling** | **Fix in v0.27** alongside KI-001: consolidate all `test()` helpers into `scripts/test_helpers.py` using a non-colliding name. |
| **Owner / next version** | Hermes / v0.27 |

---

## Summary

| Metric | Value |
|--------|-------|
| Total known issues | 3 distinct root causes |
| Cascade errors | 12 total (3 + 8 + 1) |
| Passing tests | 21 (all pytest-native, all backend integration) |
| Blocking v0.26? | **No** — none of the 3 issues affect v0.26 scope |
| Fix target | v0.27: rename helpers + add bridge fixture |

### How to verify

```bash
python3 -m pytest                          # 21 passed, 12 expected errors
python3 scripts/test_callback_api_contract.py # 6/6 passed (standalone)
python3 scripts/test_governance.py            # 4/4 passed (standalone)
python3 scripts/test_skill_registry.py        # 8/8 passed (standalone)
```

### Quick fix for CI pipeline (optional, pre-v0.27)

Add `pytest.ini` or `pyproject.toml` with test path filtering to exclude standalone scripts:

```toml
[tool.pytest.ini_options]
testpaths = ["scripts/"]
# Add a custom marker filter if needed
# python_files = ["test_*.py"]
# But exclude via --ignore in CI:
# pytest --ignore=scripts/test_callback_api_contract.py ...
```
