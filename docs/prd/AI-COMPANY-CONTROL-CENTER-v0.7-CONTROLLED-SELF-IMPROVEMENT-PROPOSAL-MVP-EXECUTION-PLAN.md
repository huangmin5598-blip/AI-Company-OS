# v0.7 — Controlled Self-Improvement Proposal MVP 执行计划

> **预估工时**: 8-9h（Sprint A ~3h + Sprint B ~2.5h + Sprint C ~2h + 收尾 ~0.5h）

---

## Sprint A: Core Proposal Layer (~3h)

### Step 1: 创建 ImprovementProposal 模型

**文件**: `backend/app/models/improvement_proposal.py` (Create)

```python
# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base

class ImprovementProposal(Base):
    __tablename__ = "improvement_proposals"

    id = Column(Integer, primary_key=True)
    source_finding_id = Column(String, nullable=True)
    source_finding_type = Column(String, nullable=False)
    # stuck_task / cost_spike / error_rate / runtime_health
    proposal_type = Column(String, nullable=False)
    # retry_task_proposal / context_update_proposal / budget_review_proposal
    # runtime_recovery_proposal / memory_update_proposal
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    rationale = Column(Text, nullable=True)
    action_plan_json = Column(Text, nullable=False, default='{}')
    risk_level = Column(String, nullable=False, default='medium')
    # low / medium / high
    business_line = Column(String, nullable=True)
    requires_command_center = Column(Integer, default=0)
    recommended_next_step = Column(String, nullable=True)
    status = Column(String, nullable=False, default='draft')
    # draft → proposed → approved → action_created
    # → closed_success / closed_failed / rejected / dismissed
    approval_id = Column(Integer, nullable=True)
    created_task_id = Column(Integer, nullable=True)
    command_draft_json = Column(Text, nullable=True)
    verification_plan_json = Column(Text, nullable=False, default='{}')
    verification_result_json = Column(Text, nullable=True)
    verified_by = Column(String, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

### Step 2: 注册模型

**文件**: `backend/app/models/__init__.py` (Modify)

添加:
```python
from app.models.improvement_proposal import ImprovementProposal
```
加到 `__all__`:
```python
"ImprovementProposal",
```

### Step 3: 创建 Improvement Proposal Generator

**文件**: `backend/app/improvement/__init__.py` (Create — empty init)
**文件**: `backend/app/improvement/generator.py` (Create)

```python
# @PRODUCT Generator — OS Core
import json
from datetime import datetime
from app.database import get_sync_session
from app.models.improvement_proposal import ImprovementProposal
from app.models.approval import Approval


ACTIVE_STATUSES = {"proposed", "approved", "action_created"}

PROPOSAL_TEMPLATES = {
    "stuck_task": {
        "proposal_type": "retry_task_proposal",
        "title_template": "Task \"{title}\" seems stuck — consider retry",
        "rationale": "Monitor detected task has not progressed beyond expected duration.",
        "action_plan": {
            "steps": [
                "1. Diagnose why task is stuck (context, dependencies, API)",
                "2. Create a controlled retry entry (without auto-cancel)",
                "3. Monitor the retry result for first 5 minutes"
            ],
            "note": "v0.7 does NOT auto-cancel or auto-retry. This is a diagnostic entry."
        },
        "verification_plan": {
            "checks": [
                "Check task status after retry — should transition to in_progress",
                "Check no duplicate running task",
                "Check execution_record created within 5 minutes"
            ],
            "expected": "Task transitions from stuck to in_progress"
        },
        "risk_level": "medium",
        "requires_command_center": False,
    },
    "cost_spike": {
        "proposal_type": "budget_review_proposal",
        "title_template": "Cost spike detected for {entity} — review budget",
        "rationale": "Cost monitor detected significant spike above threshold.",
        "action_plan": {
            "steps": [
                "1. Review cost trend for the affected agent/line",
                "2. Consider lowering priority or setting budget cap",
                "3. Check for runaway loops or excessive retries"
            ]
        },
        "verification_plan": {
            "checks": [
                "Compare next 24h cost trend vs before spike",
                "Confirm alert does not repeat within 24h"
            ],
            "expected": "Cost returns to baseline within 24h"
        },
        "risk_level": "medium",
        "requires_command_center": False,
    },
    "runtime_health": {
        "proposal_type": "runtime_recovery_proposal",
        "title_template": "Runtime \"{name}\" is {status} — diagnose and recover",
        "rationale": "Runtime health check detected offline or degraded runtime.",
        "action_plan": {
            "steps": [
                "1. Check runtime health endpoint manually",
                "2. Inspect recent heartbeat history",
                "3. Attempt recovery via launchctl restart (only via Command Center)"
            ],
            "note": "v0.7 does NOT auto-restart. Recovery requires Command Center dry-run."
        },
        "verification_plan": {
            "checks": [
                "Run runtime health check — should return online",
                "Confirm heartbeat status = online",
                "Confirm no new runtime_health finding in next scan"
            ],
            "expected": "Runtime status returns to online"
        },
        "risk_level": "high",
        "requires_command_center": True,
    },
    "error_rate": {
        "proposal_type": "memory_update_proposal",
        "title_template": "Error rate elevated for {entity} — consider knowledge update",
        "rationale": "Execution error rate exceeded threshold, suggesting knowledge gap.",
        "action_plan": {
            "steps": [
                "1. Analyze recent errors for common patterns",
                "2. Create Learning Candidate with failure patterns",
                "3. Update context or Org Memory to prevent recurrence"
            ]
        },
        "verification_plan": {
            "checks": [
                "Check error rate in next monitoring cycle",
                "Confirm error pattern is addressed in Org Memory"
            ],
            "expected": "Error rate returns below threshold"
        },
        "risk_level": "medium",
        "requires_command_center": False,
    },
}


def has_active_proposal(session, finding_type: str, source_finding_id: str) -> bool:
    """Check if there's already an active proposal for this finding + type."""
    existing = session.query(ImprovementProposal).filter(
        ImprovementProposal.source_finding_type == finding_type,
        ImprovementProposal.source_finding_id == source_finding_id,
        ImprovementProposal.status.in_(ACTIVE_STATUSES),
    ).first()
    return existing is not None


def generate_proposal(finding: dict, config: dict) -> dict | None:
    """Generate an ImprovementProposal from a monitor finding.

    Returns dict with proposal data (not yet saved) or None if skipped.
    """
    # 1. Config filter
    imp_config = config.get("improvement_proposals", {})
    if not imp_config.get("enabled", True):
        return None

    min_severity = imp_config.get("min_severity", "warning")
    severity_order = {"info": 0, "warning": 1, "critical": 2}
    if severity_order.get(finding.get("severity", "info"), 0) < severity_order.get(min_severity, 1):
        return None  # Skip info-level findings

    finding_type = finding.get("finding_type", "")
    if finding_type not in imp_config.get("auto_generate_for", list(PROPOSAL_TEMPLATES.keys())):
        return None

    # 2. Check template exists
    template = PROPOSAL_TEMPLATES.get(finding_type)
    if not template:
        return None

    source_finding_id = finding.get("source_id") or finding.get("id", "")

    session = get_sync_session()
    try:
        # 3. Dedup: same source_finding_id + proposal_type → one active
        if has_active_proposal(session, finding_type, source_finding_id):
            return None

        # 4. Build proposal
        title = template["title_template"].format(**finding.get("context", {}))
        proposal = ImprovementProposal(
            source_finding_id=source_finding_id,
            source_finding_type=finding_type,
            proposal_type=template["proposal_type"],
            title=title,
            rationale=template.get("rationale", ""),
            action_plan_json=json.dumps(template["action_plan"]),
            risk_level=template.get("risk_level", "medium"),
            requires_command_center=template.get("requires_command_center", False),
            verification_plan_json=json.dumps(template["verification_plan"]),
            status="proposed",
        )
        session.add(proposal)
        session.flush()

        # 5. Create approval record (sync)
        approval = Approval(
            target_type="improvement_proposal",
            target_id=proposal.id,
            risk_level=proposal.risk_level,
            reason=proposal.rationale,
            status="approval_requested",
        )
        session.add(approval)
        session.flush()

        proposal.approval_id = approval.id
        session.commit()

        return {
            "id": proposal.id,
            "proposal_type": proposal.proposal_type,
            "title": proposal.title,
            "status": proposal.status,
            "approval_id": approval.id,
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

### Step 4: 创建 Router

**文件**: `backend/app/routers/improvement_proposals.py` (Create)

```python
# @PRODUCT Router — OS Core
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.database import get_sync_session
from app.models.improvement_proposal import ImprovementProposal
from app.models.approval import Approval
from app.models.task_pool import TaskPool
from datetime import datetime
import json

router = APIRouter(prefix="/api/v1/improvement-proposals", tags=["improvement"])


class GenerateRequest(BaseModel):
    finding: dict
    config: dict = {}


@router.post("/generate")
def generate_proposal(req: GenerateRequest):
    from app.improvement.generator import generate_proposal as gen
    result = gen(req.finding, req.config)
    if result is None:
        raise HTTPException(400, "Proposal generation skipped (dedup, config filter, or unknown type)")
    return result


@router.get("")
def list_proposals(status: str = None, limit: int = 50, offset: int = 0):
    session = get_sync_session()
    try:
        q = session.query(ImprovementProposal).order_by(ImprovementProposal.created_at.desc())
        if status:
            q = q.filter(ImprovementProposal.status == status)
        proposals = q.offset(offset).limit(limit).all()
        return [serialize(p) for p in proposals]
    finally:
        session.close()


@router.get("/{proposal_id}")
def get_proposal(proposal_id: int):
    session = get_sync_session()
    try:
        p = session.query(ImprovementProposal).filter_by(id=proposal_id).first()
        if not p:
            raise HTTPException(404, "Proposal not found")
        return serialize(p)
    finally:
        session.close()


class ApproveRequest(BaseModel):
    founder_notes: str = ""
    decision_context: str = ""


@router.post("/{proposal_id}/approve")
def approve_proposal(proposal_id: int, req: ApproveRequest):
    """Approve a proposal → creates task_pool task (no execute)."""
    session = get_sync_session()
    try:
        p = session.query(ImprovementProposal).filter_by(id=proposal_id).first()
        if not p:
            raise HTTPException(404, "Proposal not found")
        if p.status != "proposed":
            raise HTTPException(400, f"Proposal status is '{p.status}', expected 'proposed'")

        # Update approval record
        approval = session.query(Approval).filter_by(id=p.approval_id).first()
        if approval:
            approval.status = "approved"
            approval.founder_decision = "approved"
            approval.founder_notes = req.founder_notes
            approval.decision_context = req.decision_context
            approval.approved_at = datetime.utcnow()

        # Update proposal status
        p.status = "approved"
        session.flush()

        # Create task_pool task
        task = TaskPool(
            title=p.title,
            description=p.summary or p.rationale,
            source="improvement_proposal",
            source_id=f"improvement_proposal:{p.id}",
            status="approval_required",
            risk_level=p.risk_level,
            requires_approval=True,
            context_pack_id=None,
            business_line=p.business_line,
            acceptance_criteria=json.dumps({
                "proposal_type": p.proposal_type,
                "verification_plan": json.loads(p.verification_plan_json),
            }),
        )
        session.add(task)
        session.flush()

        p.status = "action_created"
        p.created_task_id = task.id
        session.commit()

        return {"proposal_id": p.id, "status": p.status, "task_id": task.id}
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.post("/{proposal_id}/close")
def close_proposal(proposal_id: int, result: str, verification_result: dict = None,
                   verified_by: str = "founder"):
    """Close a proposal as success or failure."""
    session = get_sync_session()
    try:
        p = session.query(ImprovementProposal).filter_by(id=proposal_id).first()
        if not p:
            raise HTTPException(404, "Proposal not found")
        if p.status not in ("action_created",):
            raise HTTPException(400, f"Proposal status is '{p.status}', expected 'action_created'")

        if result == "success":
            if not verification_result:
                raise HTTPException(400, "closed_success requires verification_result")
            p.status = "closed_success"
            p.verification_result_json = json.dumps(verification_result)
            p.verified_by = verified_by
            p.verified_at = datetime.utcnow()

            # Optional: generate Learning Candidate draft
            from app.improvement.learning import create_success_candidate
            candidate = create_success_candidate(session, p)
        elif result == "failed":
            p.status = "closed_failed"
            p.verification_result_json = json.dumps(verification_result or {})
            p.verified_by = verified_by
            p.verified_at = datetime.utcnow()
        else:
            raise HTTPException(400, "result must be 'success' or 'failed'")

        session.commit()
        return {"proposal_id": p.id, "status": p.status}
    except HTTPException:
        session.rollback()
        raise
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@router.post("/{proposal_id}/reject")
def reject_proposal(proposal_id: int, founder_notes: str = ""):
    session = get_sync_session()
    try:
        p = session.query(ImprovementProposal).filter_by(id=proposal_id).first()
        if not p:
            raise HTTPException(404, "Proposal not found")
        if p.status != "proposed":
            raise HTTPException(400, f"Proposal status is '{p.status}', expected 'proposed'")
        p.status = "rejected"

        approval = session.query(Approval).filter_by(id=p.approval_id).first()
        if approval:
            approval.status = "rejected"
            approval.founder_decision = "rejected"
            approval.founder_notes = founder_notes

        session.commit()
        return {"proposal_id": p.id, "status": p.status}
    finally:
        session.close()


def serialize(p: ImprovementProposal) -> dict:
    return {
        "id": p.id,
        "source_finding_id": p.source_finding_id,
        "source_finding_type": p.source_finding_type,
        "proposal_type": p.proposal_type,
        "title": p.title,
        "summary": p.summary,
        "rationale": p.rationale,
        "action_plan": json.loads(p.action_plan_json) if p.action_plan_json else {},
        "risk_level": p.risk_level,
        "business_line": p.business_line,
        "requires_command_center": bool(p.requires_command_center),
        "recommended_next_step": p.recommended_next_step,
        "status": p.status,
        "approval_id": p.approval_id,
        "created_task_id": p.created_task_id,
        "verification_plan": json.loads(p.verification_plan_json) if p.verification_plan_json else {},
        "verification_result": json.loads(p.verification_result_json) if p.verification_result_json else None,
        "verified_by": p.verified_by,
        "verified_at": p.verified_at.isoformat() if p.verified_at else None,
        "created_at": p.created_at.isoformat() if p.created_at else None,
        "updated_at": p.updated_at.isoformat() if p.updated_at else None,
    }
```

### Step 5: 注册路由

**文件**: `backend/app/routers/__init__.py` (Modify)
**文件**: `backend/app/main.py` (Check — likely no change needed, routers auto-register)

---

## Sprint B: Approval + Controlled Action (~2.5h)

### Step 6: Monitor runner 集成 Generator

**文件**: `backend/app/monitor/runner.py` (Modify)

在 probes + analyzers 之后，output 之前加入：

```python
    # 2.5 Improvement Proposal Generator
    if config.get("improvement_proposals", {}).get("enabled", True):
        try:
            from app.improvement.generator import generate_proposal
            for finding in all_findings:
                generate_proposal(finding, config)
        except Exception as e:
            errors.append(f"improvement_generator: {e}")
```

### Step 7: Approval Center 前端面板

**文件**: `frontend/src/app/approvals/page.tsx` (Modify)

新增 Improvement Proposals 区域（详情见 Sprint C 前端代码模式）。

---

## Sprint C: Detail Page + Failure Learning (~2h)

### Step 8: Failure Learning

**文件**: `backend/app/improvement/learning.py` (Create)

```python
# @PRODUCT Learning — OS Core
from app.models.learning_candidate import LearningCandidate


def create_success_candidate(session, proposal) -> LearningCandidate | None:
    """Create a LearningCandidate draft on closed_success."""
    candidate = LearningCandidate(
        source_type="improvement_proposal",
        source_id=f"improvement_proposal:{proposal.id}",
        source_summary=proposal.summary or proposal.title,
        candidate_type="success_pattern",
        summary=f"Improvement proposal '{proposal.title}' closed successfully. "
                f"Type: {proposal.proposal_type}.",
        recommendation=proposal.action_plan_json,
        approval_status="pending_approval",
    )
    session.add(candidate)
    session.flush()
    return candidate
```

### Step 9: 前端详情页

**文件**: `frontend/src/app/improvement-proposals/[id]/page.tsx` (Create)

---

## 验收流程

```bash
# 1. Create table (auto via init_db)
python -c "from app.database import init_db; init_db()"

# 2. Generate a proposal from a finding
curl -X POST http://localhost:8001/api/v1/improvement-proposals/generate \
  -H "Content-Type: application/json" \
  -d '{"finding": {"finding_type": "stuck_task", "severity": "warning", "source_id": "test:1", "context": {"title": "Generate report"}}, "config": {"improvement_proposals": {"enabled": true, "min_severity": "warning", "auto_generate_for": ["stuck_task", "cost_spike", "error_rate", "runtime_health"]}}}'

# 3. Approve proposal
curl -X POST http://localhost:8001/api/v1/improvement-proposals/1/approve \
  -H "Content-Type: application/json" \
  -d '{"founder_notes": "Looks good, proceed"}'

# 4. Close as success
curl -X POST "http://localhost:8001/api/v1/improvement-proposals/1/close?result=success&verified_by=founder" \
  -H "Content-Type: application/json" \
  -d '{"task_status": "completed", "duration_minutes": 5}'

# 5. Verify
curl http://localhost:8001/api/v1/improvement-proposals | python3 -m json.tool
```
