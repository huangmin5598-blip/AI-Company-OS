# @PRODUCT Router — v0.9 Code-Capable Runtime Bridge
import json
import os
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from app.database import get_sync_session
from app.models.code_change_request import CodeChangeRequest
from app.models.execution_request import ExecutionRequest

router = APIRouter(prefix="/api/v1/code-change-requests", tags=["code_bridge"])

# ── State machine transitions ──

TRANSITIONS = {
    "draft": {"generate_plan": "plan_generated"},
    "plan_generated": {"approve": "plan_approved", "reject": "rejected"},
    "plan_approved": {"generate_patch": "patch_generated", "reject": "rejected"},
    "patch_generated": {"run_checks": "checks_passed"},  # actual result determined by check outcome
    "checks_passed": {"apply": "applied", "reject": "rejected", "revise": "plan_approved"},
    "checks_warning": {"apply_with_warning": "applied", "reject": "rejected", "revise": "plan_approved"},
    "checks_failed": {"revise": "plan_approved", "reject": "rejected"},
    "applied": {"rollback": "rolled_back"},
    "rolled_back": {},
    "rejected": {},
}

CHECK_STATES = {"checks_passed", "checks_warning", "checks_failed"}


def _validate_transition(current: str, action: str) -> str:
    if current not in TRANSITIONS:
        raise HTTPException(400, f"Unknown state: {current}")
    if action not in TRANSITIONS[current]:
        raise HTTPException(
            400,
            f"Action '{action}' not allowed from state '{current}'. "
            f"Allowed: {list(TRANSITIONS[current].keys())}",
        )
    return TRANSITIONS[current][action]


def _safe_json_load(val: str | None, default=None):
    if not val:
        return default
    try:
        return json.loads(val)
    except (json.JSONDecodeError, TypeError):
        return default


def _serialize(ccr: CodeChangeRequest) -> dict:
    return {
        "id": ccr.id,
        "source_type": ccr.source_type,
        "source_id": ccr.source_id,
        "execution_request_id": ccr.execution_request_id,
        "runtime_id": ccr.runtime_id,
        "title": ccr.title,
        "problem_summary": ccr.problem_summary,
        "plan_summary": ccr.plan_summary,
        "impact_scope": ccr.impact_scope,
        "risk_level": ccr.risk_level,
        "files_expected": _safe_json_load(ccr.files_expected_json, []),
        "files_changed": _safe_json_load(ccr.files_changed_json, []),
        "patch_diff": ccr.patch_diff,
        "diff_summary": ccr.diff_summary,
        "check_result": _safe_json_load(ccr.check_result_json),
        "protected_file_check": _safe_json_load(ccr.protected_file_check_json),
        "applied_with_warning": bool(ccr.applied_with_warning),
        "status": ccr.status,
        "plan_approved_by": ccr.plan_approved_by,
        "plan_approved_at": ccr.plan_approved_at.isoformat() if ccr.plan_approved_at else None,
        "applied_by": ccr.applied_by,
        "applied_at": ccr.applied_at.isoformat() if ccr.applied_at else None,
        "rolled_back_by": ccr.rolled_back_by,
        "rolled_back_at": ccr.rolled_back_at.isoformat() if ccr.rolled_back_at else None,
        "created_at": ccr.created_at.isoformat() if ccr.created_at else None,
        "updated_at": ccr.updated_at.isoformat() if ccr.updated_at else None,
    }


# ── Schemas ──


class CreateCodeChangeRequest(BaseModel):
    execution_request_id: int
    title: str
    problem_summary: str = ""
    runtime_id: str = "codex"


class ApprovePlanRequest(BaseModel):
    approved_by: str = "founder"


class ApplyRequest(BaseModel):
    applied_by: str = "founder"


class RollbackRequest(BaseModel):
    rolled_back_by: str = "founder"


# ── Endpoints ──


@router.get("")
def list_requests(
    status: str = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    session = get_sync_session()
    try:
        q = session.query(CodeChangeRequest).order_by(CodeChangeRequest.created_at.desc())
        if status:
            q = q.filter(CodeChangeRequest.status == status)
        return [_serialize(r) for r in q.offset(offset).limit(limit).all()]
    finally:
        session.close()


@router.get("/{request_id}")
def get_request(request_id: int):
    session = get_sync_session()
    try:
        ccr = session.query(CodeChangeRequest).filter_by(id=request_id).first()
        if not ccr:
            raise HTTPException(404, "Code change request not found")
        return _serialize(ccr)
    finally:
        session.close()


@router.post("")
def create_request(req: CreateCodeChangeRequest):
    """Create a code_change_request linked to an execution_request."""
    session = get_sync_session()
    try:
        # Verify execution_request exists
        ex = session.query(ExecutionRequest).filter_by(id=req.execution_request_id).first()
        if not ex:
            raise HTTPException(404, f"Execution request {req.execution_request_id} not found")

        ccr = CodeChangeRequest(
            source_type="execution_request",
            source_id=str(req.execution_request_id),
            execution_request_id=req.execution_request_id,
            runtime_id=req.runtime_id,
            title=req.title,
            problem_summary=req.problem_summary,
            status="draft",
        )
        session.add(ccr)
        session.commit()
        session.refresh(ccr)
        return _serialize(ccr)
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.post("/{request_id}/generate-plan")
async def generate_plan(request_id: int):
    """Generate plan via Code-Capable Runtime."""
    from app.code_bridge.planner import CodePlanner

    session = get_sync_session()
    try:
        ccr = session.query(CodeChangeRequest).filter_by(id=request_id).first()
        if not ccr:
            raise HTTPException(404, "Code change request not found")

        _validate_transition(ccr.status, "generate_plan")

        # Determine repo root
        repo_root = os.path.expanduser("~/Documents/Codex/ai-company-os")

        planner = CodePlanner(runtime_type=ccr.runtime_id or "codex")
        result = await planner.generate(
            problem=ccr.problem_summary or ccr.title,
            workdir=repo_root,
        )

        ccr.plan_summary = result.plan_summary
        ccr.impact_scope = result.impact_scope
        ccr.risk_level = result.risk_level
        ccr.files_expected_json = json.dumps(result.files_expected)
        ccr.status = "plan_generated"
        session.commit()

        return _serialize(ccr)
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(500, f"Plan generation failed: {str(e)}")
    finally:
        session.close()


@router.post("/{request_id}/approve-plan")
def approve_plan(request_id: int, req: ApprovePlanRequest = ApprovePlanRequest()):
    """Founder approves the generated plan."""
    session = get_sync_session()
    try:
        ccr = session.query(CodeChangeRequest).filter_by(id=request_id).first()
        if not ccr:
            raise HTTPException(404, "Code change request not found")

        _validate_transition(ccr.status, "approve")

        ccr.status = "plan_approved"
        ccr.plan_approved_by = req.approved_by
        ccr.plan_approved_at = datetime.utcnow()
        session.commit()

        return {"request_id": ccr.id, "status": ccr.status}
    except HTTPException:
        session.rollback()
        raise
    finally:
        session.close()


@router.post("/{request_id}/generate-patch")
async def generate_patch(request_id: int):
    """Generate patch to staging + create check_workspace."""
    from app.code_bridge.patch_generator import PatchGenerator
    from app.code_bridge.protected_files import ProtectedFileChecker

    session = get_sync_session()
    try:
        ccr = session.query(CodeChangeRequest).filter_by(id=request_id).first()
        if not ccr:
            raise HTTPException(404, "Code change request not found")

        _validate_transition(ccr.status, "generate_patch")

        repo_root = os.path.expanduser("~/Documents/Codex/ai-company-os")

        # Load plan from DB
        from app.runtime.code_capable import PlanResult
        plan = PlanResult(
            plan_summary=ccr.plan_summary or "",
            impact_scope=ccr.impact_scope or "",
            risk_level=ccr.risk_level,
            files_expected=json.loads(ccr.files_expected_json) if ccr.files_expected_json else [],
        )

        # Pre-check protected files
        checker = ProtectedFileChecker(repo_root)
        pre_check = checker.pre_check(plan.files_expected)

        generator = PatchGenerator(runtime_type=ccr.runtime_id or "codex")
        patch_result = await generator.generate(request_id, plan, repo_root)

        ccr.patch_diff = patch_result.patch_diff
        ccr.files_changed_json = json.dumps(patch_result.files_changed)
        ccr.diff_summary = patch_result.diff_summary

        # Post-check protected files
        post_check = checker.post_check(patch_result.patch_diff, patch_result.files_changed)
        ccr.protected_file_check_json = json.dumps({
            "pre_check": pre_check,
            "post_check": post_check,
        })

        # If post-check fails, skip directly to checks_failed
        if not post_check["passed"]:
            ccr.status = "checks_failed"
            ccr.check_result_json = json.dumps({
                "protected_file_violation": post_check,
                "_summary": {
                    "checks_passed": False,
                    "has_warnings": False,
                    "all_passed": False,
                },
            })
        else:
            ccr.status = "patch_generated"

        session.commit()
        return _serialize(ccr)
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(500, f"Patch generation failed: {str(e)}")
    finally:
        session.close()


@router.post("/{request_id}/run-checks")
async def run_checks(request_id: int):
    """Run automated checks in isolated check_workspace."""
    from app.code_bridge.checks_runner import ChecksRunner

    session = get_sync_session()
    try:
        ccr = session.query(CodeChangeRequest).filter_by(id=request_id).first()
        if not ccr:
            raise HTTPException(404, "Code change request not found")

        _validate_transition(ccr.status, "run_checks")

        repo_root = os.path.expanduser("~/Documents/Codex/ai-company-os")
        runner = ChecksRunner(repo_root)
        check_result = await runner.run_all(request_id)

        summary = check_result.pop("_summary")
        ccr.check_result_json = json.dumps(check_result)

        if not summary["checks_passed"]:
            ccr.status = "checks_failed"
        elif summary["has_warnings"]:
            ccr.status = "checks_warning"
        else:
            ccr.status = "checks_passed"

        session.commit()
        return _serialize(ccr)
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(500, f"Checks failed: {str(e)}")
    finally:
        session.close()


@router.post("/{request_id}/apply")
async def apply_patch(request_id: int, req: ApplyRequest = ApplyRequest()):
    """Apply patch from staging to actual project directory."""
    from app.code_bridge.applier import CodeApplier, PathSafetyError

    session = get_sync_session()
    try:
        ccr = session.query(CodeChangeRequest).filter_by(id=request_id).first()
        if not ccr:
            raise HTTPException(404, "Code change request not found")

        # Determine which action to use based on status
        if ccr.status == "checks_passed":
            _validate_transition(ccr.status, "apply")
            applied_with_warning = False
        elif ccr.status == "checks_warning":
            _validate_transition(ccr.status, "apply_with_warning")
            applied_with_warning = True
        else:
            raise HTTPException(400, f"Cannot apply from state '{ccr.status}'. Must be checks_passed or checks_warning")

        # Re-check protected files from manifest
        from app.code_bridge.protected_files import ProtectedFileChecker
        repo_root = os.path.expanduser("~/Documents/Codex/ai-company-os")
        checker = ProtectedFileChecker(repo_root)

        # Build a quick manifest check
        staging_dir = os.path.join(".ai-company-os/staging", str(request_id))
        manifest_path = os.path.join(staging_dir, "rollback_manifest.json")
        if os.path.exists(manifest_path):
            import json as j
            with open(manifest_path) as f:
                manifest = j.load(f)
            manifest_check = checker.check_manifest(manifest)
            if not manifest_check["passed"]:
                raise HTTPException(400, f"Protected file in manifest: {manifest_check['violations']}")

        applier = CodeApplier(repo_root)
        try:
            result = await applier.apply(request_id)
        except PathSafetyError as e:
            raise HTTPException(400, str(e))

        ccr.status = "applied"
        ccr.applied_by = req.applied_by
        ccr.applied_at = datetime.utcnow()
        ccr.applied_with_warning = 1 if applied_with_warning else 0

        # Update execution_request status to verification_pending
        ex = session.query(ExecutionRequest).filter_by(id=ccr.execution_request_id).first()
        if ex:
            ex.status = "verification_pending"
            ex.executed_at = datetime.utcnow()

        session.commit()

        return {
            "request_id": ccr.id,
            "status": "applied",
            "applied_files": result["applied_files"],
            "applied_with_warning": applied_with_warning,
        }
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(500, f"Apply failed: {str(e)}")
    finally:
        session.close()


@router.post("/{request_id}/rollback")
async def rollback_patch(request_id: int, req: RollbackRequest = RollbackRequest()):
    """Rollback applied patch."""
    from app.code_bridge.applier import CodeApplier, PathSafetyError

    session = get_sync_session()
    try:
        ccr = session.query(CodeChangeRequest).filter_by(id=request_id).first()
        if not ccr:
            raise HTTPException(404, "Code change request not found")

        _validate_transition(ccr.status, "rollback")

        repo_root = os.path.expanduser("~/Documents/Codex/ai-company-os")
        applier = CodeApplier(repo_root)

        try:
            result = await applier.rollback(request_id)
        except PathSafetyError as e:
            raise HTTPException(400, str(e))

        ccr.status = "rolled_back"
        ccr.rolled_back_by = req.rolled_back_by
        ccr.rolled_back_at = datetime.utcnow()

        # Update execution_request status
        ex = session.query(ExecutionRequest).filter_by(id=ccr.execution_request_id).first()
        if ex:
            ex.status = "rolled_back"

        session.commit()

        return {
            "request_id": ccr.id,
            "status": "rolled_back",
            "rolled_back_files": result["rolled_back_files"],
        }
    except HTTPException:
        session.rollback()
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(500, f"Rollback failed: {str(e)}")
    finally:
        session.close()


@router.post("/{request_id}/reject")
def reject_request(request_id: int):
    """Reject code change request."""
    session = get_sync_session()
    try:
        ccr = session.query(CodeChangeRequest).filter_by(id=request_id).first()
        if not ccr:
            raise HTTPException(404, "Code change request not found")

        _validate_transition(ccr.status, "reject")
        ccr.status = "rejected"
        session.commit()

        return {"request_id": ccr.id, "status": "rejected"}
    except HTTPException:
        session.rollback()
        raise
    finally:
        session.close()


@router.post("/{request_id}/revise")
def revise_request(request_id: int):
    """Send back to plan_approved for re-generation."""
    session = get_sync_session()
    try:
        ccr = session.query(CodeChangeRequest).filter_by(id=request_id).first()
        if not ccr:
            raise HTTPException(404, "Code change request not found")

        _validate_transition(ccr.status, "revise")
        ccr.status = "plan_approved"
        # Clear previous patch/check data
        ccr.patch_diff = None
        ccr.files_changed_json = None
        ccr.diff_summary = None
        ccr.check_result_json = None
        ccr.protected_file_check_json = None
        session.commit()

        return {"request_id": ccr.id, "status": "plan_approved"}
    except HTTPException:
        session.rollback()
        raise
    finally:
        session.close()
