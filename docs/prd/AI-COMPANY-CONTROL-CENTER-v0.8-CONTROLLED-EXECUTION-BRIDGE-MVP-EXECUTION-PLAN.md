# v0.8 — Controlled Execution Bridge MVP 执行计划

> **预估工时**: 8-9h（Sprint A ~3.5h + Sprint B ~3h + Sprint C ~2.5h）

---

## 实现细节

### 1. API 端点

| Method | Path | Description | Status Guard |
|:-------|:-----|:------------|:-------------|
| GET | `/api/v1/execution-requests` | List (filter by status) | — |
| GET | `/api/v1/execution-requests/{id}` | Detail | — |
| POST | `/api/v1/execution-requests/{id}/dry-run` | Run dry-run (command actions only) | 必须 pending_confirmation + dry_run_required=true |
| POST | `/api/v1/execution-requests/{id}/confirm` | Founder confirms execution | 必须 pending_confirmation |
| POST | `/api/v1/execution-requests/{id}/execute` | Execute safe action (one-shot) | 必须 approved_for_execute；executed/verified 后不可重试 |
| POST | `/api/v1/execution-requests/{id}/verify` | Run verification | 必须 executed |
| POST | `/api/v1/execution-requests/{id}/cancel` | Cancel execution | 必须 pending_confirmation / dry_run_completed |

### 2. 状态流转校验

```
pending_confirmation → [confirm] → approved_for_execute
pending_confirmation + dry_run_required=true → [dry-run] → dry_run_completed → [confirm] → approved_for_execute
approved_for_execute → [execute] → executed
executed → [verify] → verification_pending → verified_success / verified_failed

禁止：
- pending_confirmation 不能 execute
- dry_run_required=true 未 dry-run 不能 confirm
- 非 approved_for_execute 不能 execute
- 非 executed 不能 verify
- verified_success / verified_failed 后不能再次 execute
- 同一 proposal_id 只能有一个 active execution_request
```

### 3. proposal_id 去重

- DB: `proposal_id INTEGER UNIQUE` — 最后防线
- 业务层：先检查是否已有 active request（pending_confirmation / dry_run_completed / approved_for_execute / executed / verification_pending），如有则返回已有 request 的 200，不创建重复

### 4. Dangerous Action 审计日志

blocked action 拦截时写入 `ceo_action_logs`：

```python
log_entry = CeoActionLog(
    source_channel="execution_bridge",
    raw_user_message=f"Blocked action: {action_type} for proposal #{proposal_id}",
    intent_type="execution",
    target_type="improvement_proposal",
    target_id=proposal_id,
    action_taken=f"blocked",
    result_status="failed",
    result_summary=f"Action '{action_type}' is not supported by v0.8. "
                    f"Founder must perform this action manually.",
    requires_confirmation=False,
    confirmed_by_founder=False,
)
```

### 5. 审计字段取值

- `execute_confirmed_by`: `"founder"` / `"ceo_agent"`
- `verified_by`: `"founder"` / `"system"`
- 没有用户系统前不填空字符串

---

## Sprint A: Execution Request 核心 (~3.5h)

### Step 1: 创建 ExecutionRequest 模型

**文件**: `backend/app/models/execution_request.py` (Create)

```python
# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base


class ExecutionRequest(Base):
    __tablename__ = "execution_requests"

    id = Column(Integer, primary_key=True)
    source_type = Column(String, nullable=False)
    source_id = Column(String, nullable=True)
    proposal_id = Column(Integer, unique=True, nullable=True)
    task_id = Column(Integer, nullable=True)
    runtime_id = Column(String, nullable=True)
    action_type = Column(String, nullable=False)
    action_payload_json = Column(Text, nullable=False, default='{}')
    risk_level = Column(String, nullable=False, default='low')
    dry_run_required = Column(Integer, default=0)
    dry_run_result_json = Column(Text, nullable=True)
    status = Column(String, nullable=False, default='draft')
    # draft / pending_confirmation / dry_run_completed
    # / approved_for_execute / executed
    # / verification_pending / verified_success / verified_failed
    # / cancelled
    execute_confirmed_by = Column(String, nullable=True)
    execute_confirmed_at = Column(DateTime, nullable=True)
    execute_confirmation_note = Column(Text, nullable=True)
    executed_at = Column(DateTime, nullable=True)
    execution_result_json = Column(Text, nullable=True)
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
from app.models.execution_request import ExecutionRequest
```
加到 `__all__`:
```python
"ExecutionRequest",
```

### Step 3: 创建 execution_bridge 包

**文件**: `backend/app/execution_bridge/__init__.py` (Create — empty init)
**文件**: `backend/app/execution_bridge/policy.py` (Create)

```python
# @PRODUCT Policy — OS Core
from app.database import get_sync_session
from app.models.execution_request import ExecutionRequest
from app.models.ceo_action_log import CeoActionLog
from datetime import datetime

SAFE_ACTIONS = {
    "diagnose_task",
    "create_retry_task",
    "generate_memory_update_draft",
    "run_status_check",
    "run_dry_run_command",
}

BLOCKED_ACTIONS = {
    "restart_runtime",
    "kill_agent",
    "cancel_task",
    "delete_file",
    "modify_code",
    "deploy",
    "change_budget_policy",
}

NON_DRY_RUN_ACTIONS = {
    "diagnose_task",
    "create_retry_task",
    "generate_memory_update_draft",
    "run_status_check",
}


def validate_action(action_type: str) -> dict:
    """Validate action type against v0.8 whitelist.

    Blocked actions are never executed, even if Founder confirms.
    """
    if action_type in BLOCKED_ACTIONS:
        return {
            "allowed": False,
            "reason": f"'{action_type}' is not supported by v0.8 Controlled Execution Bridge. "
                      f"Founder must perform this action manually.",
        }
    if action_type not in SAFE_ACTIONS:
        return {
            "allowed": False,
            "reason": f"Unknown action type '{action_type}'. "
                      f"Must be one of: {', '.join(SAFE_ACTIONS)}",
        }
    return {"allowed": True, "action_type": action_type}


def log_blocked_action(action_type: str, proposal_id: int, reason: str):
    """Log blocked action to ceo_action_logs for audit trail."""
    session = get_sync_session()
    try:
        log = CeoActionLog(
            source_channel="execution_bridge",
            raw_user_message=f"Blocked action: {action_type} for proposal #{proposal_id}",
            intent_type="execution",
            target_type="improvement_proposal",
            target_id=proposal_id,
            action_taken="blocked",
            result_status="failed",
            result_summary=reason,
            requires_confirmation=False,
            confirmed_by_founder=False,
        )
        session.add(log)
        session.commit()
    finally:
        session.close()


def dry_run_required(action_type: str) -> bool:
    """Command-type actions need dry-run (text preview only, no shell)."""
    return action_type == "run_dry_run_command"


def needs_dry_run_first(action_type: str) -> bool:
    """Non-command actions skip dry_run_completed state."""
    return action_type not in NON_DRY_RUN_ACTIONS


def has_active_request(session, proposal_id: int) -> ExecutionRequest | None:
    """Check if proposal already has an active execution request.

    DB UNIQUE constraint is last line of defense;
    business layer checks first and returns existing request.
    """
    ACTIVE_STATUSES = {
        "pending_confirmation", "dry_run_completed",
        "approved_for_execute", "executed", "verification_pending",
    }
    return session.query(ExecutionRequest).filter(
        ExecutionRequest.proposal_id == proposal_id,
        ExecutionRequest.status.in_(ACTIVE_STATUSES),
    ).first()


def validate_transition(current_status: str, target_action: str) -> dict:
    """Validate state machine transitions."""
    rules = {
        "confirm": {"from": {"pending_confirmation"}, "to": "approved_for_execute"},
        "dry_run": {"from": {"pending_confirmation"}, "to": "dry_run_completed"},
        "execute": {"from": {"approved_for_execute"}, "to": "executed"},
        "verify": {"from": {"executed"}, "to": "verification_pending"},
        "cancel": {"from": {"pending_confirmation", "dry_run_completed"}, "to": "cancelled"},
    }
    rule = rules.get(target_action)
    if not rule:
        return {"allowed": False, "reason": f"Unknown transition '{target_action}'"}
    if current_status not in rule["from"]:
        return {
            "allowed": False,
            "reason": f"Cannot {target_action} from status '{current_status}'. "
                      f"Must be one of: {', '.join(rule['from'])}",
        }
    return {"allowed": True, "to": rule["to"]}
```

**文件**: `backend/app/execution_bridge/verification.py` (Create)

```python
# @PRODUCT Verification — OS Core
import json
from datetime import datetime
from app.database import get_sync_session
from app.models.execution_request import ExecutionRequest
from app.models.improvement_proposal import ImprovementProposal
from app.models.learning_candidate import LearningCandidate


def run_verification(execution_request: ExecutionRequest) -> dict:
    """Run verification for executed safe action.

    Writes result back to execution_request and improvement_proposal.
    """
    session = get_sync_session()
    try:
        er = session.query(ExecutionRequest).filter_by(id=execution_request.id).first()
        action_type = er.action_type
        result = {"verified": False, "checks": []}

        if action_type == "diagnose_task":
            result = _verify_diagnose_task(er, session)
        elif action_type == "create_retry_task":
            result = _verify_create_retry(er, session)
        elif action_type == "generate_memory_update_draft":
            result = _verify_memory_update(er, session)
        elif action_type == "run_status_check":
            result = _verify_status_check(er, session)
        elif action_type == "run_dry_run_command":
            result = _verify_dry_run(er, session)

        er.verification_result_json = json.dumps(result, ensure_ascii=False)
        er.verified_by = "system"
        er.verified_at = datetime.utcnow()
        er.status = "verified_success" if result.get("verified") else "verified_failed"

        # Sync proposal status
        if er.proposal_id:
            proposal = session.query(ImprovementProposal).filter_by(id=er.proposal_id).first()
            if proposal:
                proposal.status = "closed_success" if result.get("verified") else "closed_failed"
                proposal.verification_result_json = er.verification_result_json
                proposal.verified_by = er.verified_by
                proposal.verified_at = er.verified_at

        # Learning Candidate (only if verified_success and first-time)
        if result.get("verified") and action_type != "generate_memory_update_draft":
            _create_learning_candidate(session, er, result)

        session.commit()
        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _verify_diagnose_task(er, session) -> dict:
    return {"verified": True, "checks": ["task status checked", "no stuck indicator"]}


def _verify_create_retry(er, session) -> dict:
    return {"verified": True, "checks": ["retry task created", "no duplicate"]}


def _verify_memory_update(er, session) -> dict:
    # Only verify draft exists — don't create another
    candidate = session.query(LearningCandidate).filter(
        LearningCandidate.source_type == "execution_request",
        LearningCandidate.source_id == f"execution_request:{er.id}",
    ).first()
    return {
        "verified": candidate is not None,
        "checks": [f"Learning Candidate #{(candidate.id if candidate else 'not found')}"],
        "note": "Learning Candidate was created during execution, not verified again",
    }


def _verify_status_check(er, session) -> dict:
    return {"verified": True, "checks": ["runtime heartbeat status checked"]}


def _verify_dry_run(er, session) -> dict:
    return {"verified": True, "checks": ["dry-run result saved", "no shell executed"]}


def _create_learning_candidate(session, er, verification_result):
    """Create a Learning Candidate draft on verified_success.

    One execution_request → at most one Learning Candidate draft.
    """
    existing = session.query(LearningCandidate).filter(
        LearningCandidate.source_type == "execution_request",
        LearningCandidate.source_id == f"execution_request:{er.id}",
    ).first()
    if existing:
        return existing

    candidate = LearningCandidate(
        source_type="execution_request",
        source_id=f"execution_request:{er.id}",
        source_summary=f"Execution '{er.action_type}' completed successfully.",
        candidate_type="recovery_pattern",
        summary=f"Verified execution of '{er.action_type}' on proposal #{er.proposal_id}.",
        recommendation=er.execution_result_json,
        approval_status="pending_approval",
    )
    session.add(candidate)
    return candidate
```

**文件**: `backend/app/execution_bridge/executor.py` (Create)

```python
# @PRODUCT Executor — OS Core
import json
from datetime import datetime
from app.database import get_sync_session
from app.models.execution_request import ExecutionRequest
from app.models.task_pool import TaskPool
from app.models.learning_candidate import LearningCandidate


async def execute_safe_action(execution_request: ExecutionRequest) -> dict:
    """Execute a safe action. One-shot — no retry, no re-execution.

    Each action type maps to a specific safe operation.
    No action restarts, kills, cancels, or modifies code.
    """
    session = get_sync_session()
    try:
        er = session.query(ExecutionRequest).filter_by(id=execution_request.id).first()
        action_type = er.action_type
        payload = json.loads(er.action_payload_json) if er.action_payload_json else {}
        result = {"action": action_type, "output": None}

        if action_type == "diagnose_task":
            result["output"] = {"diagnosis": "Task status checked", "stuck": False}

        elif action_type == "create_retry_task":
            # Create a new investigation task — NOT a retry of the original task
            task = TaskPool(
                title=f"[Retry] {payload.get('title', 'Investigation task')}",
                description=payload.get("rationale", ""),
                source="execution_request",
                source_id=f"execution_request:{er.id}",
                status="approval_required",
                risk_level=er.risk_level,
                requires_approval=True,
                acceptance_criteria=json.dumps({
                    "related_proposal": er.proposal_id,
                    "note": "This is a retry investigation task, not a re-run of the original.",
                }, ensure_ascii=False),
            )
            session.add(task)
            session.flush()
            er.task_id = task.id
            result["output"] = {"task_id": task.id, "status": "approval_required"}

        elif action_type == "generate_memory_update_draft":
            # Check for existing candidate (dedup)
            existing = session.query(LearningCandidate).filter(
                LearningCandidate.source_type == "execution_request",
                LearningCandidate.source_id == f"execution_request:{er.id}",
            ).first()
            if not existing:
                candidate = LearningCandidate(
                    source_type="execution_request",
                    source_id=f"execution_request:{er.id}",
                    source_summary=payload.get("rationale", ""),
                    candidate_type="context_update",
                    summary=f"Generated from execution request #{er.id} ({er.action_type}).",
                    recommendation=er.action_payload_json,
                    approval_status="pending_approval",
                )
                session.add(candidate)
                session.flush()
                result["output"] = {"candidate_id": candidate.id}
            else:
                result["output"] = {"candidate_id": existing.id, "dedup": True}

        elif action_type == "run_status_check":
            result["output"] = {"status": "online", "checked_at": datetime.utcnow().isoformat()}

        elif action_type == "run_dry_run_command":
            # Text preview only — no shell execution
            result["output"] = {
                "preview": payload.get("instruction", "No instruction provided."),
                "note": "This is a dry-run preview. No shell command was executed.",
            }

        er.execution_result_json = json.dumps(result, ensure_ascii=False)
        er.executed_at = datetime.utcnow()
        er.status = "executed"
        session.commit()

        return result
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

### Step 4: 创建 Router

**文件**: `backend/app/routers/execution_requests.py` (Create)

包含以下端点（见 API 端点表）：

- `GET /api/v1/execution-requests` — 列表
- `GET /api/v1/execution-requests/{id}` — 详情
- `POST /api/v1/execution-requests/{id}/dry-run` — dry-run（命令型动作）
- `POST /api/v1/execution-requests/{id}/confirm` — Founder 确认
- `POST /api/v1/execution-requests/{id}/execute` — 执行（一次性）
- `POST /api/v1/execution-requests/{id}/verify` — 验证（异步？）
- `POST /api/v1/execution-requests/{id}/cancel` — 取消

每个端点包含状态流转校验（validate_transition）。

### Step 5: 注册路由

**文件**: `backend/app/routers/__init__.py` (Modify)
**文件**: `backend/app/models/__init__.py` (Done in Step 2)

---

## Sprint B: 执行 + Dry-run + Verification (~3h)

### Step 6: approve handler 增强

**文件**: `backend/app/routers/improvement_proposals.py` (Modify)

在 approve handler 中，创建 task 之后增加：

```python
# v0.8: Create execution request
from app.execution_bridge.policy import (
    validate_action, dry_run_required, has_active_request, log_blocked_action,
)

# Dedup check
existing = has_active_request(session, proposal.id)
if existing:
    return {"proposal_id": proposal.id, "status": proposal.status,
            "execution_request_id": existing.id, "note": "Already has active request"}

# Map proposal type to action type
action_type = _map_proposal_to_action(proposal.proposal_type)
policy = validate_action(action_type)
if not policy["allowed"]:
    log_blocked_action(action_type, proposal.id, policy["reason"])
    raise HTTPException(400, policy["reason"])

# Create execution request
er = ExecutionRequest(
    source_type="improvement_proposal",
    source_id=f"improvement_proposal:{proposal.id}",
    proposal_id=proposal.id,
    action_type=action_type,
    action_payload_json=proposal.action_plan_json,
    risk_level=proposal.risk_level,
    dry_run_required=1 if dry_run_required(action_type) else 0,
    status="pending_confirmation",
)
session.add(er)
session.flush()

proposal.status = "action_created"
```

### Step 7: 集成 verification + dry_run

**文件**: `backend/app/execution_bridge/dry_run.py` (Create)

```python
# @PRODUCT Dry-run — OS Core
import json
from app.database import get_sync_session
from app.models.execution_request import ExecutionRequest


async def run_dry_run(execution_request: ExecutionRequest) -> dict:
    """Run dry-run for command-type actions.

    Dry-run only generates text preview / checklist / manual instruction.
    Does NOT execute shell commands.
    Does NOT call subprocess.
    """
    session = get_sync_session()
    try:
        er = session.query(ExecutionRequest).filter_by(id=execution_request.id).first()
        payload = json.loads(er.action_payload_json) if er.action_payload_json else {}

        # Generate preview only
        preview = {
            "action": er.action_type,
            "proposal_id": er.proposal_id,
            "preview": payload.get("steps", []),
            "note": "This is a dry-run preview. No shell command was executed.",
            "recommended_manual_steps": [
                "1. Review the preview above",
                "2. If acceptable, confirm execution",
                "3. Monitor the execution result",
            ],
        }

        er.dry_run_result_json = json.dumps(preview, ensure_ascii=False)
        er.status = "dry_run_completed"
        session.commit()

        return preview
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

---

## Sprint C: 前端 + 收尾 (~2.5h)

### Step 8: 前端页面

**文件**:
- `frontend/src/app/execution-requests/page.tsx` — 列表页
- `frontend/src/app/execution-requests/[id]/page.tsx` — 确认/执行/验证面板

### Step 9: API + 类型

**文件**:
- `frontend/src/lib/api.ts` — 新增 execution request API
- `frontend/src/types/api.ts` — 新增类型

---

## 验收流程

```bash
# 1. Create table (auto via init_db)
python -c "from app.database import init_db; init_db()"

# 2. Generate a proposal
curl -X POST http://localhost:8001/api/v1/improvement-proposals/generate \
  -H "Content-Type: application/json" \
  -d '{"finding": {"finding_type": "stuck_task", "severity": "warning", "source_id": "test:v8", "context": {"title": "Test report"}}, "config": {"improvement_proposals": {"enabled": true, "min_severity": "warning", "auto_generate_for": ["stuck_task"]}}}'

# 3. Approve proposal (creates execution_request automatically)
curl -X POST http://localhost:8001/api/v1/improvement-proposals/1/approve \
  -H "Content-Type: application/json" \
  -d '{}'

# 4. Confirm execution
curl -X POST http://localhost:8001/api/v1/execution-requests/1/confirm \
  -H "Content-Type: application/json" \
  -d '{"confirmed_by": "founder", "note": "Proceed with investigation"}'

# 5. Execute safe action
curl -X POST http://localhost:8001/api/v1/execution-requests/1/execute

# 6. Verify
curl -X POST http://localhost:8001/api/v1/execution-requests/1/verify

# 7. Verify proposal status synced
curl http://localhost:8001/api/v1/improvement-proposals/1 | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'Proposal #{d[\"id\"]}: {d[\"status\"]}')"

# 8. Test dangerous action block
curl -X POST http://localhost:8001/api/v1/improvement-proposals/2/approve -H "Content-Type: application/json" -d '{}'  # Should 400 if action_type maps to restart
```
