#!/usr/bin/env python3
"""
v0.9.1.2 Mock Mode Acceptance Test
Tests: create CCR → generate plan → approve plan → generate patch → staging check
"""
import json
import subprocess
import sys
import os

BASE = "http://localhost:8001"
WORKDIR = os.path.expanduser("~/Documents/Codex/ai-company-os")
PASS = 0
FAIL = 0
STEP = 0

def api(method, path, data=None):
    url = f"{BASE}{path}"
    cmd = ["curl", "-s", "-X", method, url]
    if data is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(data)]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
    try:
        return json.loads(result.stdout)
    except:
        return {"_raw": result.stdout}

def step(name, condition, detail=""):
    global PASS, FAIL, STEP
    STEP += 1
    status = "✅ PASS" if condition else "❌ FAIL"
    if status == "✅ PASS":
        PASS += 1
    else:
        FAIL += 1
    print(f"\n[{STEP}] {status} | {name}")
    if detail:
        for line in detail.strip().split("\n"):
            print(f"      {line}")

print("=" * 60)
print("v0.9.1.2 SCHEMA PATCH INTEGRATION — MOCK MODE TEST")
print("=" * 60)

# ── Step 1: Create CCR ──
print("\n─── Step 1: Create CCR ───")
ccr = api("POST", "/api/v1/code-change-requests", {
    "source_type": "execution_request",
    "source_id": "1",
    "execution_request_id": 1,
    "runtime_id": "codex",
    "title": "v0.9.1.2 mock test - output-schema integration",
    "problem_summary": "Test the new --output-schema code path in mock mode."
})
ccr_id = ccr.get("id")
step("CCR created", ccr_id is not None,
     f"CCR #{ccr_id} | status={ccr.get('status')}")
if ccr_id is None:
    print(json.dumps(ccr, indent=2))
    sys.exit(1)

# ── Step 2: Generate Plan ──
print("\n─── Step 2: Generate Plan ───")
plan = api("POST", f"/api/v1/code-change-requests/{ccr_id}/generate-plan")
plan_status = plan.get("status")
plan_summary = plan.get("plan_summary", "")
step("Plan generated", plan_status == "plan_generated",
     f"status={plan_status} | plan_summary={'yes' if plan_summary else 'no'}")

# ── Step 3: Approve Plan ──
print("\n─── Step 3: Approve Plan ───")
approved = api("POST", f"/api/v1/code-change-requests/{ccr_id}/approve-plan", {
    "approved_by": "test-bot"
})
approve_status = approved.get("status")
step("Plan approved", approve_status == "plan_approved",
     f"status={approve_status} | approved_by={approved.get('plan_approved_by')}")

# ── Step 4: Generate Patch (v0.9.1.2 key step) ──
print("\n─── Step 4: Generate Patch ───")
patch = api("POST", f"/api/v1/code-change-requests/{ccr_id}/generate-patch")
patch_status = patch.get("status")
patch_diff = patch.get("patch_diff", "")
check_result = patch.get("check_result")
diff_summary = patch.get("diff_summary", "")

step("Patch generated", patch_status in ("patch_generated", "checks_pending", "checks_failed"),
     f"status={patch_status} | diff_len={len(patch_diff) if patch_diff else 0}")
step("Diff not empty", bool(patch_diff) and len(patch_diff) > 50,
     f"diff length: {len(patch_diff) if patch_diff else 0} chars")

# ⚠️ NOTE: In mock mode, the git apply --check may fail because mock
# generates patches that reference non-existent files. That's expected.
# The real mode (Codex) generates valid patches.
step("Check result present", bool(check_result),
     f"check_result type: {type(check_result).__name__}")
step("Protected file check present", bool(patch.get("protected_file_check")),
     f"protected_file_check: {json.dumps(patch.get('protected_file_check'), indent=2)[:100] if patch.get('protected_file_check') else 'MISSING'}")

# ── Step 5: Verify Staging Files ──
print("\n─── Step 5: Verify Staging Files ───")
staging_base = os.path.join(WORKDIR, ".ai-company-os", "staging")
staging_dir = os.path.join(staging_base, str(ccr_id))

files_to_check = {
    "patch_spec.json": os.path.join(staging_dir, "patch_spec.json"),
    "patch.diff": os.path.join(staging_dir, "patch.diff"),
    "protected_file_check.json": os.path.join(staging_dir, "protected_file_check.json"),
}

all_staging_ok = True
for name, path in files_to_check.items():
    exists = os.path.isfile(path)
    if not exists:
        all_staging_ok = False
    step(f"Staging file: {name}", exists,
         f"path={path} | size={os.path.getsize(path) if exists else 'N/A'} bytes")

# ── Step 6: Check Workspace ──
print("\n─── Step 6: Check Workspace ───")
check_ws = os.path.join(staging_dir, "check_workspace")
check_ws_exists = os.path.isdir(check_ws)
step("Check workspace directory exists", check_ws_exists,
     f"path={check_ws}")

if check_ws_exists:
    files_in_ws = []
    for root, dirs, files in os.walk(check_ws):
        for f in files:
            files_in_ws.append(os.path.join(root, f))
    step("Check workspace has files", len(files_in_ws) > 0,
         f"found {len(files_in_ws)} files: {files_in_ws[:5]}")

# ── Step 7: Check git apply --check ──
print("\n─── Step 7: git apply --check ───")
# Read the patch diff from the staging area (or from the API response)
patch_path = os.path.join(staging_dir, "patch.diff")
if os.path.isfile(patch_path):
    result = subprocess.run(
        ["git", "apply", "--check", patch_path],
        capture_output=True, text=True, cwd=WORKDIR, timeout=10
    )
    apply_ok = result.returncode == 0
    step("git apply --check passes", apply_ok,
         f"returncode={result.returncode}" + (f"\n      stderr={result.stderr[:200]}" if result.stderr else ""))
else:
    step("git apply --check N/A (no patch.diff)", False,
         "patch.diff not found in staging")

# ── Summary ──
print("\n" + "=" * 60)
total = PASS + FAIL
print(f"RESULTS: {PASS}/{total} PASSED, {FAIL}/{total} FAILED")
print("=" * 60)

if FAIL > 0:
    sys.exit(1)
else:
    print("🎉 All tests passed!")
