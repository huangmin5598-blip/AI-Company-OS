# AI Company Control Center v0.7 — Controlled Self-Improvement Proposal MVP PRD

> **状态**: 📋 PRD · 待执行
> **预估工时**: 8-9h（分 Sprint A + Sprint B + Sprint C）
> **定位**: v0.7 让 AI Company OS 能基于 Monitor Findings 自动生成可审查的改进提案；Founder 批准后，系统只创建受控任务或 dry-run entry，**不直接执行修复**。
>
> **一句话**: v0.7 = Improvement Proposal Layer — 让系统能"提出怎么改进自己"，但还不能"自己动手改自己"。
>
> **核心子系统**: Monitor Finding → Improvement Proposal Generator → Approval → Controlled Action Draft (task_pool) → Verification → Learning Candidate

---

## 一、产品定位

### 从"看见问题"到"提出改进方案"

| 版本 | 核心能力 | 系统状态 |
|:-----|:---------|:---------|
| v0.5 | Monitor Framework 发现问题 | 有 Finding，无后续动作 |
| v0.6 | Runtime Layer MVP — 知道自己的器官 | Runtime 可观察 |
| **v0.7** | **Improvement Proposal Layer** | **Finding → Proposal → Controlled Draft** |
| v0.8+ | Fix Executor / Codex Repair | 自动修复（未来） |

### 为什么要现在做

v0.5 已经能发现：
- `stuck_task` — 任务卡住
- `cost_spike` — 成本异常
- `error_rate` — 执行错误率升高
- `runtime_health` — 运行时离线

v0.6 又补了 Runtime Layer，让系统知道有哪些 Runtime、状态如何。

但 **Monitor Finding 和实际修复之间还有一条巨大的鸿沟**：

```
v0.5: Finding → Alert → (Founder 手动处理)
v0.7: Finding → Proposal → Founder Approval → Controlled Action Draft → Verification → Learn
```

v0.7 补的就是这条链路的前半段。后半段（自动执行）留到 v0.8+。

---

## 二、范围

### 必做

| 模块 | 说明 | 工时 |
|:-----|:------|:----:|
| ImprovementProposal 表 | 提案存储，含状态机、5 个字段组 | 1h |
| Improvement Proposal Generator | Monitor runner 中新增，finding → proposal | 1.5h |
| finding → proposal API | `POST /api/v1/improvement-proposals/generate` | 0.5h |
| proposal CRUD API | 增删改查 + 状态流转 | 1h |
| Approval Center 集成 | 新增 Improvement Proposals 面板 + 写入 approvals 表 | 1.5h |
| approve → task_pool task | 批准后创建受控任务，同步更新 proposal+approval 状态 | 1h |
| runtime 类 proposal dry-run | 创建 task 标记 requires_command_center=true，不执行任何 shell | 1h |
| proposal 详情页面 | action_plan, verification_plan, 关联项 | 1h |
| Failure Learning (success) | closed_success → Learning Candidate draft | 0.5h |
| Failure Learning (failed, 可选) | closed_failed → failure_pattern / tool_gap / context_update 类型 draft | — |

### 5 种 proposal_type

| 类型 | Finding 来源 | 生成动作 |
|:-----|:-------------|:---------|
| `retry_task_proposal` | stuck_task | 诊断卡住原因，创建受控 retry 入口（不含 cancel） |
| `context_update_proposal` | stuck_task / error_rate | 建议更新 Context Pack |
| `budget_review_proposal` | cost_spike | 建议降低优先级 / 设置预算上限 |
| `runtime_recovery_proposal` | runtime_health | 创建诊断任务（不触发 restart，不调用 launchctl） |
| `memory_update_proposal` | error_rate / runtime_health | 建议写入 Org Memory 避免问题重复 |

### 状态机

```
draft
  → proposed                    (由 Generator 自动创建)
    → approved                  (Founder 批准)
      → action_created          (task_pool task 已创建)
        → closed_success        (验证通过，改进成功)
        → closed_failed         (验证失败，改进未完成)
    → rejected                  (Founder 驳回)
    → dismissed                 (过期或无需处理)
```

**特殊规则**:
- `closed_success` 必须包含 `verification_result_json`、`verified_by`、`verified_at`，不能无依据关闭成功
- `approvals` 表和 `improvement_proposals` 状态必须同步（同一事务或强制互补逻辑）
- 同一 `source_finding_id + proposal_type` 只能有一个 active proposal（active = proposed / approved / action_created）

### Generator 配置

```yaml
improvement_proposals:
  enabled: true
  min_severity: warning          # info 级 finding 默认不生成 proposal
  auto_generate_for:
    - stuck_task
    - cost_spike
    - error_rate
    - runtime_health
```

### 不做

- ❌ 自动执行修复
- ❌ 自动 restart runtime
- ❌ 自动 kill / cancel agent
- ❌ 自动 retry loop（单次受控 retry 入口可创建，但不会自动重试循环）
- ❌ 自动修改 skill / 规则
- ❌ 自动写代码 / 自动部署
- ❌ 自动写 Knowledge Proposal / Org Memory（只生成 Learning Candidate draft）
- ❌ 绕过 Command Center / Approval Center
- ❌ Codex / Claude Code repair workflow
- ❌ 跨 Runtime 自动调度

### 安全边界（强制执行）

> **v0.7 是提案层，不是执行层。**

1. **Improvement Proposal Generator 只生成 draft，不执行任何操作。**
2. **Founder 批准 proposal ≠ 系统直接执行修复。** 批准只允许它进入受控动作链路。
3. **runtime_recovery_proposal 不能直接 restart。** 创建的 task `requires_command_center=true`，不能执行 shell command。
4. **retry_task_proposal 不包含 cancel 动作。** 只创建受控 retry 入口。
5. **closed_success 必须有 verification 依据。** 不能无验证关闭成功。
6. **`action_plan_json` / `verification_plan_json` 后端强制 JSON 格式** — `json.dumps` 保存，API 返回 object。非法 JSON 直接 400。
7. **closed_success 后只生成 Learning Candidate draft，** 不自动写 Knowledge Proposal / Org Memory。
8. **涉及命令型动作的 proposal，创建的 task 只能 `status=approval_required`，不能直接 execute。**

---

## 三、系统设计

### 3.1 主线链路

```
Monitor Finding
  ↓
Improvement Proposal Generator (配置控制: min_severity, auto_generate_for)
  ↓  (去重: 同一 source_finding_id + proposal_type 只能一个 active)
Improvement Proposal (status=proposed)
  ↓  (同步创建 approvals 记录)
Approval Center — Founder 审查
  ↓ approved  (同步更新 approval 和 proposal 状态)
Improvement Proposal (status=approved, approval_id=...)
  ↓
Controlled Action Draft
  ├── task_pool task (source=improvement_proposal, status=approval_required)
  └── (runtime 类) requires_command_center=true
  ↓
Founder Execute Confirmation (via Command Center / Task Pool)
  ↓ executed & verified (必需: verification_result_json + verified_by + verified_at)
Improvement Proposal (status=closed_success / closed_failed)
  ↓ (仅 closed_success — 必做)
Learning Candidate draft (type=success_pattern / recovery_pattern / decision_pattern)
  ↓ (closed_failed — Sprint C 可选)
Learning Candidate draft (type=failure_pattern / tool_gap / context_update)
  ↓
Founder 手动确认 → Knowledge Proposal → Org Memory (v0.4 管道)
```

**关键节点（两道门）:**

```
第一道门：Founder 批准 Proposal  →  允许进入受控动作链路
第二道门：Founder 确认 Execute  →  实际执行动作
```

### 3.2 ImprovementProposal 表

```sql
CREATE TABLE improvement_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_finding_id TEXT,
    -- "monitor_finding:{id}" 或 "alert:{id}"
    source_finding_type TEXT NOT NULL,
    -- stuck_task / cost_spike / error_rate / runtime_health
    proposal_type TEXT NOT NULL,
    -- 5 种类型见上
    title TEXT NOT NULL,
    summary TEXT,
    rationale TEXT,
    -- Why this proposal was generated
    action_plan_json TEXT NOT NULL DEFAULT '{}',
    -- JSON: detailed steps. json.dumps 保存，API 返回 object
    risk_level TEXT NOT NULL DEFAULT 'medium',
    -- low / medium / high
    business_line TEXT,
    requires_command_center INTEGER DEFAULT 0,
    -- 1 if action must go through Command Center
    recommended_next_step TEXT,
    -- What Founder should do next
    status TEXT NOT NULL DEFAULT 'draft',
    -- draft → proposed → approved → action_created
    -- → closed_success / closed_failed / rejected / dismissed
    approval_id INTEGER,
    -- Link to approvals table (target_type=improvement_proposal)
    created_task_id INTEGER,
    -- task_pool task created after approval
    command_draft_json TEXT,
    -- Command Center dry-run draft content (JSON string)
    verification_plan_json TEXT NOT NULL DEFAULT '{}',
    -- JSON: how to verify. json.dumps 保存，API 返回 object
    verification_result_json TEXT,
    -- JSON: actual verification outcome (必填在 closed_success 前)
    verified_by TEXT,
    -- Who verified (Founder / system). 必填在 closed_success 前
    verified_at TEXT,
    -- 必填在 closed_success 前
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
```

### 3.3 Verification Plan 结构

每个 proposal 必须带有验证方案。示例：

**Stuck Task Retry:**
```json
{
  "checks": [
    "Check task status after retry — should be 'in_progress'",
    "Check no duplicate running task",
    "Check execution_record created within 5 minutes"
  ],
  "expected": "Task transitions from stuck to in_progress"
}
```

**Runtime Recovery:**
```json
{
  "checks": [
    "Run runtime health check — should return online",
    "Confirm heartbeat status = online",
    "Confirm no new runtime_health finding in next scan"
  ],
  "expected": "Runtime status returns to online"
}
```

**Cost Spike:**
```json
{
  "checks": [
    "Compare next 24h cost trend vs before spike",
    "Confirm alert does not repeat within 24h"
  ],
  "expected": "Cost returns to baseline within 24h"
}
```

### 3.4 Improvement Proposal Generator

新增一个 analyzer，挂载在 Monitor runner 中，位置在 probe + analyzer 执行之后。

```python
# 伪代码 — 不执行任何操作，只生成 proposal draft
def improve_proposals_generator(finding, config) -> ImprovementProposal | None:
    # 1. 配置过滤：min_severity, auto_generate_for
    severity = finding.get("severity", "info")
    if severity == "info":
        return None  # info 级 finding 默认不生成
    
    # 2. 去重：同一 source_finding_id + proposal_type 不能有 active proposal
    if has_active_proposal(finding):
        return None
    
    # 3. 根据 finding 类型生成对应 proposal
    if finding.finding_type == "stuck_task":
        return generate_retry_proposal(finding)
    elif finding.finding_type == "cost_spike":
        return generate_budget_review_proposal(finding)
    elif finding.finding_type == "runtime_health":
        return generate_runtime_recovery_proposal(finding)
    elif finding.finding_type == "error_rate":
        return generate_memory_update_proposal(finding)
    return None
```

### 3.5 Approval Center 集成

proposal 生成时同步创建 `approvals` 记录：

```
proposal generated (status=proposed)
  → 创建 approval request
    · target_type = "improvement_proposal"
    · target_id = proposal.id
  → proposal.approval_id = approval.id
  → 状态保持同步

Founder approve
  → approval.status = approved
  → proposal.status = approved
  （同一事务或强制互补逻辑）
```

### 3.6 task_pool 复用

不新增 `controlled_action_draft` 表。批准后统一落到 `task_pool`：

```json
{
  "source": "improvement_proposal",
  "source_id": "improvement_proposal:{id}",
  "status": "approval_required",
  "title": "Diagnose and retry task #{original_task_id}",
  "risk_level": "medium",
  "requires_command_center": false
}
```

涉及运行时操作（如 runtime recovery）的 proposal，task 额外标记：

```json
{
  "source": "improvement_proposal",
  "source_id": "improvement_proposal:{id}",
  "status": "approval_required",
  "requires_command_center": true,
  "recommended_next_step": "Open Command Center dry-run"
}
```

**不做 `ready_for_dry_run` 状态** — 统一用现有 `approval_required`，用 `requires_command_center` 字段区分。

### 3.7 JSON 格式强制

```python
# 保存前
action_plan_json = json.dumps(validated_dict)  # 非法 JSON → 400
verification_plan_json = json.dumps(validated_dict)

# API 返回
"action_plan": json.loads(row.action_plan_json),  # 永远是 object
"verification_plan": json.loads(row.verification_plan_json),  # 永远是 object
```

---

## 四、验收标准

### 验收 1: Finding 生成 Proposal（含去重 + 级别过滤）

**输入**: 一个 `stuck_task` monitor_finding（severity=warning）

**结果**:
- ✅ 生成 `improvement_proposal` 记录
- ✅ `proposal_type = retry_task_proposal`
- ✅ `status = proposed`
- ✅ `risk_level` 已设置
- ✅ `action_plan_json` 合法 JSON，API 返回 object
- ✅ `verification_plan_json` 合法 JSON，API 返回 object
- ✅ 同步创建 `approvals` 记录（`target_type=improvement_proposal`）

**额外验证**:
- ✅ 同一 `source_finding_id + proposal_type` 重复调用 generate，不创建第二个 active proposal
- ✅ `info` 级 finding 调用 generate，不创建 proposal

### 验收 2: Proposal 审批后创建受控任务

**输入**: Founder approve proposal（`target_type=improvement_proposal`）

**结果**:
- ✅ `approval.status = approved`
- ✅ `proposal.status = approved`
- ✅ 创建 `task_pool` task
- ✅ `source = "improvement_proposal"`
- ✅ `status = "approval_required"`
- ❌ 不触发 execute
- ❌ 不调用 shell command

### 验收 3: Runtime health proposal 不自动 restart

**输入**: `runtime_health` finding: OpenClaw offline

**结果**:
- ✅ 生成 `runtime_recovery_proposal`
- ✅ `requires_command_center = true`
- ✅ 创建的 task `requires_command_center = true`
- ❌ 不调用 restart
- ❌ 不调用 launchctl
- ❌ 不执行任何 shell command

### 验收 4: 全流程留痕 + 状态同步

**结果**:
- ✅ proposal 关联 `source_finding_id`
- ✅ approval 记录存在（`approval_id != null`）
- ✅ `created_task_id` 记录存在
- ✅ `approvals` 表状态和 `improvement_proposals` 状态一致
- ✅ 不绕过 Approval Center / Command Center

### 验收 5: Failure Learning 安全边界

**输入**: proposal status → `closed_success`（含 `verification_result_json`、`verified_by`、`verified_at`）

**结果**:
- ✅ 生成 Learning Candidate draft
- ❌ 不自动写 Knowledge Proposal
- ❌ 不自动写 Org Memory

**输入**: proposal status → `rejected` / `dismissed`

**结果**:
- ✅ 不生成任何 Learning Candidate

**输入**: proposal status → `closed_success` **缺** `verification_result_json` / `verified_by` / `verified_at`

**结果**:
- ❌ 不允许关闭，返回 400

---

## 五、执行计划概览

### Sprint A (~3h) — Core Proposal Layer

| Step | 文件 | 说明 |
|:-----|:-----|:------|
| 1 | `backend/app/models/improvement_proposal.py` | 模型（含去重索引） |
| 2 | `backend/app/models/__init__.py` | 注册模型 |
| 3 | `backend/app/improvement/generator.py` | Proposal Generator（含配置过滤 + 去重） |
| 4 | `backend/app/improvement/__init__.py` | 包初始化 |
| 5 | `backend/app/routers/improvement_proposals.py` | CRUD + generate + approve API |
| 6 | `backend/app/routers/__init__.py` | 注册路由 |
| 7 | `backend/app/main.py` | 整合 |

### Sprint B (~2.5h) — Approval + Controlled Action

| Step | 文件 | 说明 |
|:-----|:-----|:------|
| 8 | `backend/app/monitor/runner.py` | 集成 Generator（配置控制） |
| 9 | `backend/app/routers/improvement_proposals.py` | approve handler → approvals 表 + task_pool |
| 10 | `frontend/src/app/approvals/page.tsx` | Improvement Proposals 面板 |
| 11 | 验证 1-4 | Finding → Proposal → Approve → Task（含去重、info 过滤、状态同步） |

### Sprint C (~2h) — Detail Page + Failure Learning

| Step | 文件 | 说明 |
|:-----|:-----|:------|
| 12 | `frontend/src/app/improvement-proposals/[id]/page.tsx` | 详情页（action plan, verification plan, 关联项） |
| 13 | `backend/app/improvement/learning.py` | closed_success → Learning Candidate draft |
| 14 | (可选) `backend/app/improvement/learning.py` | closed_failed → failure_pattern draft |
| 15 | 验证 5 | Failure Learning 安全边界 |
| 16 | Commit + Tag + GitHub Release | v0.7 |

---

## 六、不做（详细版）

以下条目在 v0.7 中明确不做：

- **自动执行修复** — System generates proposals, Founder decides. No auto-fix.
- **自动 restart runtime** — Even if runtime is clearly offline, v0.7 only creates a recovery proposal with requires_command_center=true.
- **自动 kill / cancel agent** — retry_task_proposal 不含 cancel 动作。所有 cancel/kill 需要 Founder 明确操作。
- **自动 retry loop** — A retry proposal creates one controlled task entry, not a retry loop with auto-verification.
- **自动修改 skill** — Skill modification has too many side effects. Deferred to v0.8+.
- **自动写代码 / 自动部署** — Code changes require Codex/Claude Code integration (v0.8+).
- **自动写 Knowledge Proposal / Org Memory** — Learning Candidate draft is the only auto-generated output. Founder controls the pipeline from there.
- **绕过 Command Center / Approval Center** — All improvement actions must pass through the existing safety gates.
- **Codex / Claude Code repair workflow** — Requires ACP protocol integration (v0.8+).
- **`ready_for_dry_run` 作为 task_pool 状态** — 统一用 `approval_required`，`requires_command_center` 字段区分。
- **close_success 无验证依据** — 必须填写 `verification_result_json` / `verified_by` / `verified_at`。
- **Multi-Runtime automatic scheduling** — Depends on v0.6 Runtime Layer running stably.

---

> **相关文档**
> - Roadmap: `docs/AI-COMPANY-OS-ROADMAP.md`
> - v0.5 Monitor Framework PRD: `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.5-MONITOR-FRAMEWORK-LITE-PRD.md`
> - v0.6 Runtime Layer MVP PRD: `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.6-RUNTIME-LAYER-MVP-PRD.md`
> - 产品化架构: `docs/architecture/PRODUCTIZATION-ARCHITECTURE.md`
