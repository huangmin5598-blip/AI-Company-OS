# AI Company Control Center v0.8 — Controlled Execution Bridge MVP PRD

> **状态**: 📋 PRD · 待执行
> **预估工时**: 8-9h（分 Sprint A + Sprint B + Sprint C）
> **定位**: v0.8 让已批准的 Improvement Proposal 可以进入一次性、可审计、可验证的受控执行流程；系统可以执行低风险动作或生成 dry-run 指令，但不自动修复、不自动重试循环、不自动修改代码。
>
> **一句话**: v0.8 = Controlled Execution Bridge — 让系统第一次能"安全地动一下手"，但只能动低风险、可验证、可回滚的手。
>
> **核心子系统**: Improvement Proposal → Execution Request → dry-run / Safe Action → Verification → Learning Candidate

---

## 一、产品定位

### 从"提方案"到"安全执行"

| 版本 | 核心能力 | 系统状态 |
|:-----|:---------|:---------|
| v0.5 | Monitor Framework 发现问题 | Finding → Alert，无后续 |
| v0.6 | Runtime Layer MVP | 知道有哪些 Runtime |
| v0.7 | Improvement Proposal Layer | Finding → Proposal → Controlled Draft |
| **v0.8** | **Controlled Execution Bridge** | **Proposal → Execution Request → Safe Action → Verification** |
| v0.9 | Code-Capable Runtime Integration | Coding agent 接入执行桥 |
| v1.0 | Agent Meeting Session | 多 Agent 结构化会议 |

### 为什么要现在做

v0.7 的链路停在：

```
Finding → Proposal → Approval → Task (approval_required) ── 不动了
```

Founder 批准之后，系统只是创建了一个 `approval_required` 的 task，**没有人真正去执行它**。

v0.8 补的就是这一层：

```
approved proposal
  → Execution Request（审计：谁要求什么 Action）
    → Dry-run（命令型动作先模拟）
      → Founder 确认
        → 执行一次性 safe action
          → Verification（验证改对了）
            → Learning Candidate（沉淀经验）
```

这是系统第一次真正从"观察自己"走向"影响自己"。但这个影响是**受控的、单次的、可审计、可验证的**。

### 五条执行原则（强制执行）

1. **One-shot execution only** — 每个 approved proposal 最多触发一次 execution request。不自动重试。
2. **Founder confirmation required** — 执行前必须有 Founder 显式确认。**approve proposal ≠ approve execute。** 这是 v0.8 最重要的安全边界。
3. **Dry-run first** — 命令型动作（任何可能产生副作用的操作）必须先生成 dry-run 结果，Founder 审阅后才可执行。
4. **No destructive action** — v0.8 **不支持** restart / kill / cancel / delete / deploy / code write。Founder 可以在系统外手动执行这些操作，但 v0.8 的执行桥不执行、不绕过。
5. **Verification required** — 执行后必须进入 verification，不验证就不能 closed_success。

---

## 二、范围

### 必做

| 模块 | 说明 | 工时 |
|:-----|:------|:----:|
| ExecutionRequest 表 | 执行请求模型，分离意图与执行 | 1h |
| 生成逻辑 | proposal approved → execution request created | 1h |
| Action Type 白名单 | 5 种 safe action 策略校验 | 1h |
| Dry-run 支持 | 命令型动作先生成 preview / manual instruction（不执行 shell） | 1.5h |
| Safe Action 执行 | 低风险动作一次性执行，执行后不可重复 | 1.5h |
| Verification 闭环 | 执行后验证 + 同步写回 proposal 状态 | 1h |
| Dangerous Action 拦截 | 策略拒绝 + 审计日志，即使 Founder 确认也不执行 | 0.5h |
| 前端 Execution Request 面板 | 查看、确认、执行、验证 | 1.5h |

### Action Type 白名单（v0.8 第一版）

| Action Type | 说明 | 关联 Proposal | Dry-run 要求 |
|:------------|:-----|:--------------|:-------------|
| `diagnose_task` | 检查卡住任务的状态、上下文、依赖 | retry_task_proposal | 否 |
| `create_retry_task` | 创建**新的** retry investigation task。不 cancel、不 restart、不 re-run 原任务。新 task status = approval_required | retry_task_proposal | 否 |
| `generate_memory_update_draft` | 生成 Learning Candidate draft。一个 execution_request 最多生成一条。 | memory_update_proposal | 否 |
| `run_status_check` | 检查 Runtime 健康状态 | runtime_recovery_proposal | 否 |
| `run_dry_run_command` | 生成命令预览 / 恢复指令。**不执行 shell，不调 subprocess**。输出为文本预览、checklist 或 manual instruction。 | runtime_recovery_proposal | 是 |

### 不允许的 Action（策略拦截 — 即使 Founder 确认也不执行）

| Action | 原因 | 替代 |
|:-------|:-----|:-----|
| `restart_runtime` | 副作用大，可能影响其他 Agent | 只生成 dry-run 恢复指令 |
| `kill_agent` | 破坏性操作 | 不进受控执行桥 |
| `cancel_task` | 可能丢失进度 | 交给 Founder 手动操作 |
| `delete_file` | 不可逆 | 不进受控执行桥 |
| `modify_code` | 需 Code-Capable Runtime 集成（v0.9） | 延迟 |
| `deploy` | 生产风险 | 不进受控执行桥 |
| `change_budget_policy` | 影响面广 | 不进受控执行桥 |

### 状态机（双路径）

**非命令型动作**（diagnose_task / create_retry_task / generate_memory_update_draft / run_status_check）:

```
draft
  → pending_confirmation     (proposal approved → execution request 创建)
    → approved_for_execute   (Founder 确认执行)
      → executed              (一次性 safe action 执行，不可重试)
        → verification_pending
          → verified_success
          → verified_failed
    → cancelled              (Founder 取消)
```

**命令型动作**（run_dry_run_command）:

```
draft
  → pending_confirmation
    → dry_run_completed      (dry-run 完成，结果写入 dry_run_result_json)
      → approved_for_execute (Founder 审阅 dry-run 结果后确认)
        → executed
          → verification_pending
            → verified_success
            → verified_failed
    → cancelled
```

### 不做

- ❌ 自动 restart runtime
- ❌ 自动 kill / cancel agent
- ❌ 自动 retry loop
- ❌ 自动修改代码
- ❌ 自动部署
- ❌ Codex 修复 PR（v0.9）
- ❌ Claude Code 真接入（v0.9）
- ❌ Agent Meeting Session（v1.0）
- ❌ 跨 Runtime 自动调度
- ❌ 绕过 Approval Center
- ❌ 绕过 Command Center dry-run
- ❌ 自动写 Org Memory（只生成 draft）

### Codex Adapter Spike（v0.8 可选 — 不阻塞主线，不占 Sprint C）

v0.8 可以做一个轻量 Codex Adapter Spike，但**不作为主线交付验收**：

- 范围：health_check + capability discovery + `enabled=experimental`
- 不做：不执行任何代码操作、不接入执行桥、不生成修复 PR
- 如果接入成本高，不阻塞 v0.8 主线

建议独立版本号：`v0.8.1-codex-spike` 如果后续单独做。

---

## 三、系统设计

### 3.1 主线链路

```
Improvement Proposal approved (v0.7)
  ↓
去重检查：同一 proposal_id 只能有一个 active execution_request
  ↓
Execution Request Created (status=pending_confirmation)
  ↓
[非命令型] → Founder Review → approved_for_execute
[命令型]   → Dry-run (仅 preview, 不 exec) → Founder Review → approved_for_execute
  ↓
Safe Action Execution (一次性，不重试，执行后不可重复执行)
  ↓
Verification
  ├── verified_success
  │     → 更新 proposal status = closed_success
  │     → (若 action_type != generate_memory_update_draft) 创建 Learning Candidate
  │     → 如果已有 Learning Candidate 不重复创建
  └── verified_failed
        → 更新 proposal status = closed_failed
```

### 3.2 ExecutionRequest 表

```sql
CREATE TABLE execution_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_type TEXT NOT NULL,
    -- improvement_proposal / task / command
    source_id TEXT,
    proposal_id INTEGER UNIQUE,
    -- 唯一关联 proposal，重复执行防护
    task_id INTEGER,
    -- Link to task_pool
    runtime_id TEXT,
    -- Which runtime should execute this
    action_type TEXT NOT NULL,
    -- diagnose_task / create_retry_task / generate_memory_update_draft
    -- run_status_check / run_dry_run_command
    action_payload_json TEXT NOT NULL DEFAULT '{}',
    -- JSON: specific parameters for the action
    risk_level TEXT NOT NULL DEFAULT 'low',
    -- low / medium / high
    dry_run_required INTEGER DEFAULT 0,
    dry_run_result_json TEXT,
    -- JSON: dry-run preview / simulation result (not shell exec)
    status TEXT NOT NULL DEFAULT 'draft',
    -- 见双路径状态机
    execute_confirmed_by TEXT,
    -- Founder who confirmed execution (审计字段)
    execute_confirmed_at TEXT,
    execute_confirmation_note TEXT,
    executed_at TEXT,
    execution_result_json TEXT,
    -- JSON: actual execution result
    verification_result_json TEXT,
    -- JSON: verification outcome
    verified_by TEXT,
    verified_at TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

**去重规则（代码强制，不依赖 UNIQUE 约束）**：
- 同一 `proposal_id` 只能有一个 active execution_request
- active statuses = pending_confirmation / dry_run_completed / approved_for_execute / executed / verification_pending
- 已 verified_success / verified_failed 的 request 不允许再次 execute

### 3.3 Proposal 状态同步规则

execution_request 的状态变化必须写回 improvement_proposal：

```
execution_request created
  → proposal.status = action_created

execution_request.verified_success
  → proposal.status = closed_success
  → proposal.verification_result_json = execution_request.verification_result_json
  → proposal.verified_by = execution_request.verified_by
  → proposal.verified_at = execution_request.verified_at

execution_request.verified_failed
  → proposal.status = closed_failed

execution_request.cancelled
  → proposal.status 保持 approved 或由 Founder 决定转 dismissed
```

### 3.4 Action Type 策略引擎

```python
# 伪代码 — 白名单校验
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


def validate_action(action_type: str) -> dict:
    """校验 action_type 是否在白名单内。即使 Founder 确认，blocked action 也不执行。"""
    if action_type in BLOCKED_ACTIONS:
        return {
            "allowed": False,
            "reason": f"'{action_type}' is not supported by v0.8 Controlled Execution Bridge. "
                      f"Founder must perform this action manually outside the system.",
        }
    if action_type not in SAFE_ACTIONS:
        return {
            "allowed": False,
            "reason": f"Unknown action type '{action_type}'. "
                      f"Must be one of: {', '.join(SAFE_ACTIONS)}",
        }
    return {"allowed": True, "action_type": action_type}


def determine_dry_run_required(action_type: str) -> bool:
    """命令型动作需要 dry-run。dry-run 不执行 shell / subprocess。"""
    return action_type in ("run_dry_run_command",)


def has_active_request(session, proposal_id: int) -> bool:
    """重复执行防护：同一 proposal 只能有一个 active execution request。"""
    ACTIVE_STATUSES = {
        "pending_confirmation", "dry_run_completed",
        "approved_for_execute", "executed", "verification_pending",
    }
    existing = session.query(ExecutionRequest).filter(
        ExecutionRequest.proposal_id == proposal_id,
        ExecutionRequest.status.in_(ACTIVE_STATUSES),
    ).first()
    return existing is not None
```

### 3.5 与 v0.7 ImprovementProposal 的衔接

proposal 被 approve 后，approve handler 自动创建 execution_request：

```python
# v0.8: approve handler 增强
def approve_proposal(proposal_id):
    # ... (v0.7 原有逻辑)

    # 去重检查
    if has_active_request(session, proposal_id):
        return existing  # 返回已有 request，不创建重复

    # 映射 action_type
    action_type = map_proposal_to_action(proposal.proposal_type)
    policy = validate_action(action_type)

    if not policy["allowed"]:
        raise PolicyBlocked(policy["reason"])

    execution_request = ExecutionRequest(
        source_type="improvement_proposal",
        source_id=f"improvement_proposal:{proposal.id}",
        proposal_id=proposal.id,
        action_type=action_type,
        action_payload_json=proposal.action_plan_json,
        risk_level=proposal.risk_level,
        dry_run_required=determine_dry_run_required(action_type),
        status="pending_confirmation",
    )

    # 同步 proposal 状态
    proposal.status = "action_created"
```

### 3.6 Dry-run 设计

dry-run **不执行任何 shell command**。只生成：

- 命令预览（文本格式）
- 操作 checklist
- 手动恢复指令

**禁止**：

- `subprocess.run(...)` / `subprocess.Popen(...)`
- `os.system(...)`
- `shell=True`

### 3.7 Learning Candidate 去重规则

```
如果 action_type = generate_memory_update_draft：
  - execution 阶段生成 Learning Candidate draft
  - verification 只验证 draft 是否存在
  - verified_success 不再重复生成

如果 action_type ≠ generate_memory_update_draft：
  - verified_success 后可生成一条 execution_result / recovery_pattern 类 Learning Candidate
  - 如果已有同类型的 Learning Candidate，不重复

一个 execution_request 最多有一条 Learning Candidate draft。
```

### 3.8 Verification 模式

每个 action type 对应不同的验证方式：

| Action Type | Verification |
|:------------|:-------------|
| `diagnose_task` | 检查 task status 不再 stuck；有新的 execution_record |
| `create_retry_task` | 确认新的 task 已创建（status=approval_required）；没有 duplicate |
| `generate_memory_update_draft` | 确认 Learning Candidate 已创建（status=pending_approval）；不超过 1 条 |
| `run_status_check` | 检查 runtime heartbeats 最新记录；确认 status=online |
| `run_dry_run_command` | 确认 dry-run 结果已保存；不实际执行 |

---

## 四、验收标准

### 验收 1: Approved proposal 生成 Execution Request（含去重）

**输入**: Improvement Proposal approve（如 `retry_task_proposal`）

**结果**:
- ✅ `execution_request` 已创建
- ✅ `source_type = "improvement_proposal"`
- ✅ `proposal_id` 正确关联且唯一
- ✅ `status = "pending_confirmation"`
- ✅ `action_type` 在白名单内
- ❌ 不触发 execute

**额外验证**:
- ✅ 同一 proposal 重复 approve → 返回已有 request（不重复创建）
- ✅ 非 dry-run action → 状态可以直接进入 `approved_for_execute`

### 验收 2: Dry-run 能跑通且不执行 shell

**输入**: `runtime_recovery_proposal` → execution request → dry-run

**结果**:
- ✅ dry-run 结果写入 `dry_run_result_json`（文本预览 / checklist）
- ✅ `status = "dry_run_completed"`
- ❌ `subprocess.run` / `os.system` / `shell=True` never called
- ❌ 没有执行任何 shell command

### 验收 3: Safe Action 能执行一次

**输入**: `memory_update_proposal` → execution request → execute

**结果**:
- ✅ Learning Candidate draft 已创建（最多 1 条）
- ✅ `execution_result_json` 已写入
- ✅ `status = "executed"`

**输入**: `stuck_task` → execution request → execute

**结果**:
- ✅ 创建了 retry investigation task（不是 cancel + retry）
- ✅ 新 task `source = "execution_request"`，`status = "approval_required"`
- ✅ `status = "executed"`
- ❌ 不触发原任务 cancel / restart / re-run

### 验收 4: Verification 闭环 + Proposal 状态同步

**输入**: execute → verification → verified_success

**结果**:
- ✅ `verification_result_json` 已写入 execution_request
- ✅ `verification_result_json` 已写入 improvement_proposal
- ✅ `proposal.status = closed_success`
- ✅ `verified_by` 和 `verified_at` 已记录

**输入**: execute → verification → verified_failed

**结果**:
- ✅ `proposal.status = closed_failed`

### 验收 5: 危险动作被拦截（即使 Founder 确认）

**输入**: `restart_runtime` / `kill_agent` / `cancel_task` 等 blocked action

**结果**:
- ✅ 策略拒绝，返回 400
- ✅ 日志记录
- ❌ Founder 用确认按钮也无法绕过

### 验收 6: Execute Confirmation 审计

**输入**: Founder 确认 execution → approved_for_execute

**结果**:
- ✅ `execute_confirmed_by` 已记录（Founder 标识）
- ✅ `execute_confirmed_at` 已记录
- ✅ `execute_confirmation_note` 可选但可记录

### 验收 7: Learning Candidate 不重复生成

**输入**: `generate_memory_update_draft` → execute → verified_success

**结果**:
- ✅ 生成 1 条 Learning Candidate draft
- ✅ verified_success 后不再生成第 2 条

**输入**: 非 memory 类 action → executed → verified_success

**结果**:
- ✅ 可生成 1 条 recovery_pattern 类 Learning Candidate
- ✅ 不生成第 2 条

---

## 五、执行计划概览

### Sprint A (~3.5h) — Execution Request 核心

| Step | 文件 | 说明 |
|:-----|:-----|:------|
| 1 | `backend/app/models/execution_request.py` | 模型（含 proposal_id unique、审计字段） |
| 2 | `backend/app/models/__init__.py` | 注册模型 |
| 3 | `backend/app/execution_bridge/__init__.py` | 包初始化 |
| 4 | `backend/app/execution_bridge/policy.py` | 白名单 + 策略引擎（去重、拦截） |
| 5 | `backend/app/execution_bridge/verification.py` | 验证器 + proposal 状态同步 |
| 6 | `backend/app/routers/execution_requests.py` | CRUD API |

### Sprint B (~3h) — 执行 + Dry-run + Verification

| Step | 文件 | 说明 |
|:-----|:-----|:------|
| 7 | `backend/app/execution_bridge/executor.py` | Safe Action 执行器（一次性、不重试） |
| 8 | `backend/app/routers/improvement_proposals.py` | approve handler 增强（去重 + 创建 execution request + proposal 同步） |
| 9 | `backend/app/execution_bridge/dry_run.py` | Dry-run 模拟器（不执行 shell） |
| 10 | 验证 1-3 | Approved→Request→Dry-run→Execute→Verification |

### Sprint C (~2.5h) — 前端 + 收尾

| Step | 文件 | 说明 |
|:-----|:-----|:------|
| 11 | `frontend/src/app/execution-requests/page.tsx` | 执行请求列表 |
| 12 | `frontend/src/app/execution-requests/[id]/page.tsx` | 确认/执行/验证面板 |
| 13 | 验证 4-7 | Verification 闭环 + 危险动作拦截 + 审计 + Learning Candidate 去重 |
| 14 | Commit + Tag + GitHub Release | v0.8 |

---

## 六、路线衔接

| 版本 | 核心 | 与 v0.8 的关系 |
|:-----|:-----|:----------------|
| v0.7 | Improvement Proposal Layer | v0.8 的输入（approved proposal → execution request） |
| **v0.8** | **Controlled Execution Bridge** | **搭执行框架，让系统安全执行低风险动作** |
| v0.9 | Code-Capable Runtime Integration | Codex/Claude Code 挂上执行桥，执行 code-safe action |
| v1.0 | Agent Meeting Session | 多 Agent 会议 + 决策产出挂上执行桥 |

---

> **相关文档**
> - Roadmap: `docs/AI-COMPANY-OS-ROADMAP.md`
> - v0.7 Controlled Self-Improvement Proposal MVP PRD: `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.7-CONTROLLED-SELF-IMPROVEMENT-PROPOSAL-MVP-PRD.md`
> - v0.6 Runtime Layer MVP PRD: `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.6-RUNTIME-LAYER-MVP-PRD.md`
> - 产品化架构: `docs/architecture/PRODUCTIZATION-ARCHITECTURE.md`
