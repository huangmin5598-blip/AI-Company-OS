# AI Company Control Center v0.3 — CEO Agent Lite / Founder Intent Interface PRD

> **状态**: 📋 PRD · 待执行
> **预估工时**: 12-16h（约 2 天冲刺）
> **定位**: v0.3 让 Founder 可以用自然语言向 AI Company OS 表达目标和确认审批，系统将其转化为结构化任务闭环，不自动执行、不自动审批、不绕过安全门。
>
> **一句话**: v0.3 = Founder Intent Interface — 你的自然语言第一次稳定进入 AI Company OS 的任务闭环。

---

## 一、产品定位

### 从被动到主动

| 版本 | 驱动模式 | 触发方式 |
|:-----|:---------|:---------|
| v0.1.x | 可见 | 系统数据 → 面板 |
| v0.2 | 被动闭环 | 系统告警 → 任务 → 审批 → 执行 → 验收 |
| **v0.3** | **主动承接** | **Founder 目标 → 任务入池 + Founder 审批 → 系统留痕** |

### 核心链路

```
v0.3 新增: Founder Intent → CEO Agent → Structured Action → Backend Truth Layer

两条链路:

1. Goal Intake
Founder: "亚马逊选品最近连续失败，排查并修复"
  → Hermes CEO Skill
    → 理解目标
    → 拆解 2-5 个 Task Proposal
    → 每个 task 生成 Context Pack 草稿
    → 调用 commit-decomposition 端点
  → CC Backend
    → 写入 goal_sessions
    → 创建 task_pool 条目
    → 创建 context_packs
    → 创建 approvals
    → 写入 ceo_action_logs
  → CEO Agent 返回汇报

2. Approval Action
Founder: "批准刚才第一个任务"
  → Hermes CEO Skill
    → 匹配唯一 approval
    → confidence ≥ 0.85 → 可执行
    → 调用 Approval API
  → CC Backend
    → 更新 approval 状态
    → 写入 ceo_action_logs
  → CEO Agent 返回确认
```

### 回答的问题

> **我的自然语言意图可以稳定进入公司闭环了吗？**

v0.2 回答了"系统告警能不能自动闭环"（✅ 能）。
v0.3 回答"我的想法能不能变成系统任务"（✅ 能）+ "我的审批能不能用自然语言完成"（✅ 能）。

---

## 二、范围

### 必做

| 模块 | 说明 | 优先级 |
|:-----|:------|:------:|
| **CEO Skill（Hermes）** | 目标拆解 + 审批操作解析，结构化 schema 输出，few-shot 示例 | P0 |
| **goal_sessions 表** | Founder 输入的每个目标的完整记录 | P0 |
| **ceo_action_logs 表** | 所有 CEO 代操作的审计日志 | P0 |
| **commit-decomposition 端点** | 原子写入：goal_session + task_pool + context_packs + approvals + logs | P0 |
| **CEO Workbench** | CEO Agent 工作台：展示 goal_sessions、拆解结果、action_logs；可创建 goal_session draft；不要求 v0.3 实现实时聊天 | P0 |
| **飞书输入** | 可选（验收不依赖飞书） | P1 |
| **Action Logs 页面** | 查看所有 CEO 代操作记录 | P1 |

### 二类意图

#### 意图 1：Goal Intake（目标→任务入池）

Founder 输入一个经营目标 → CEO Agent：

1. 理解目标：总结目标、判断类型（repair/growth/research/review/ops）
2. 拆解任务：2-5 个可执行的 Task Proposal
3. 每个任务附上 Context Pack 草稿
4. 自动生成 Approval Request
5. 原子写入后端
6. CEO 返回结构化汇报

#### 意图 2：Approval Action（自然语言审批）

Founder 明确表达审批决定 → CEO Agent：

1. 匹配唯一目标 approval
2. 复述关键信息（任务、风险、影响）
3. **置信度 ≥ 0.85 + 唯一匹配** → 可调用 Approval API 完成审批动作
4. **匹配不唯一（matched_targets_count > 1）** → 返回候选 approval 列表，不执行。CEO 回复：\"我找到了 N 个待审批项：1. approval #X — ... 2. approval #Y — ... 请回复编号。\"
5. **置信度不足（confidence < 0.85）** → 追问确认，不执行
6. 所有操作（包括失败、模糊、追问）均写入 ceo_action_logs

### 不做

| 不做 | 原因 |
|:-----|:------|
| ❌ 自动执行 | 安全边界，v0.4+ |
| ❌ 自动分派 Agent 执行 | CEO 不自执行具体任务 |
| ❌ 低风险自动批准 | 最早 v0.3.1 或 v0.4 |
| ❌ Status Query 自然语言 | → v0.3.1 |
| ❌ Task Follow-up 自然语言 | → v0.3.1 |
| ❌ 每日自动简报 | → v0.4 |
| ❌ Monitor Agent | → v0.4 |
| ❌ Agent Meeting | → v0.7 |
| ❌ 多 Runtime | → v0.6 |
| ❌ 绕过 Approval Center | 不可变 |
| ❌ 绕过 Command Center safety gate | 不可变 |
| ❌ 绕过 Review Gate | 不可变 |

---

## 三、架构

```
Founder
  │
  ├── Feishu / Hermes TUI (自然语言对话入口) ← 主要
  └── CEO Workbench (工作台：展示/记录)      ← 辅助
        │
        ▼
  Hermes CEO Skill
  │
  ├── goal_decomposition schema
  │   └── 输出: { goal_summary, tasks[], context_packs[] }
  │
  ├── approval_action schema
  │   └── 输出: { decision, target_id, confidence, requires_confirmation }
  │
  └── cc_api tool
      └── 调用 CC 后端 API
            │
            ▼
      Control Center Backend
      │
      ├── goal_sessions        ← 新增表
      ├── ceo_action_logs      ← 新增表
      ├── task_pool            ← 复用 v0.2
      ├── context_packs        ← 复用 v0.2
      ├── approvals            ← 复用 v0.2
      └── command_logs         ← 复用现有
```

### CEO Skill Schema 设计

#### Goal Intake Output

```json
{
  "goal_summary": "排查亚马逊选品连续失败",
  "goal_type": "repair",
  "business_line": "amazon-seller",
  "risk_level": "medium",
  "confidence": 0.88,
  "tasks": [
    {
      "title": "检查 amazon-seller 最近失败记录",
      "why": "确认 400 错误是否来自 API 参数或权限问题",
      "task_type": "diagnosis",
      "assigned_agent": "amazon-seller",
      "risk_level": "low",
      "priority": "medium",
      "acceptance_criteria": "定位最近 3 次失败的共同原因",
      "context_pack": {
        "founder_intent": "排查亚马逊选品连续失败的根因",
        "related_sources": ["recent_alerts", "execution_records"],
        "known_failures": [],
        "constraints": "不得修改 OpenClaw runtime 配置"
      }
    }
  ]
}
```

#### Approval Action Schema

```json
{
  "intent_type": "approval_action",
  "decision": "approved",
  "target_type": "approval",
  "target_id": 12,
  "matched_targets_count": 1,
  "confidence": 0.91,
  "requires_confirmation": false,
  "founder_phrase": "批准 approval #12"
}
```

**安全规则：**
- `confidence ≥ 0.85` **且** `matched_targets_count === 1` → 可调用 Approval API 完成审批动作，不得执行具体任务
- `matched_targets_count > 1` → 返回候选列表，不执行
- `confidence < 0.85` → 追问确认，不执行
- 所有结果（包括失败、模糊、追问）均写入 ceo_action_logs

---

## 四、数据模型

### 4.1 goal_sessions

```sql
字段名                  类型          说明
──────────────────────────────────────────────────────
id                      Integer PK
source_channel          String        cc_panel / feishu
raw_goal                Text          Founder 原始输入
client_request_id       String        可选，幂等保护（唯一请求标识）
interpreted_goal        String       CEO 理解后的目标摘要
goal_type               String       repair / growth / research / build / review / ops
business_line           String
priority                String        low / medium / high / critical
risk_level              String        low / medium / high
status                  String        draft / decomposed / committed / cancelled / failed
decomposition_json      Text          JSON: 完整的结构化拆解结果
task_ids_json           Text          JSON: [task.id, ...]
approval_ids_json       Text          JSON: [approval.id, ...]
model_used              String        使用的模型
confidence              Float         0.0-1.0
schema_version          String        "v0.3.0"
error_message           Text          失败原因
created_at              DateTime
updated_at              DateTime
```

### 4.2 ceo_action_logs

```sql
字段名                  类型          说明
──────────────────────────────────────────────────────
id                      Integer PK
source_channel          String        cc_panel / feishu
raw_user_message        Text          Founder 的原始消息
intent_type             String        goal_intake / approval_action
target_type             String        goal_session / task / approval / learning_candidate
target_id               Integer
action_taken            String        decomposed / approved / rejected / revised / deferred / cancelled / failed
payload_json            Text          JSON: 完整的请求/响应数据
result_status           String        success / failed / ambiguous / cancelled
result_summary          Text          结果摘要
confidence              Float         0.0-1.0
requires_confirmation   Boolean       是否需要 Founder 确认
confirmed_by_founder    Boolean       Founder 是否已确认
created_at              DateTime
```

---

## 五、API 端点

### 新增端点

| 端点 | 方法 | 功能 |
|:-----|:----:|:-----|
| `/api/v1/ceo/goal-sessions` | GET | 目标列表 |
| `/api/v1/ceo/goal-sessions` | POST | 创建目标记录 |
| `/api/v1/ceo/goal-sessions/{id}` | GET | 目标详情（含拆解结果） |
| `/api/v1/ceo/commit-decomposition` | POST | **原子提交** 拆解结果 → goal_session + tasks + context_packs + approvals + logs |
| `/api/v1/ceo/action-logs` | GET | 操作日志列表 |
| `/api/v1/ceo/action-logs` | POST | 写入操作日志 |

### 复用端点（v0.2 已有，CEO Skill 直接调用）

| 端点 | 用途 |
|:-----|:------|
| `PATCH /api/v1/approvals/{id}/decide` | 审批决策 |
| `GET /api/v1/approvals` | 查询待审批项 |
| `GET /api/v1/task-pool/{id}` | 查询任务详情 |
| `GET /api/v1/task-pool` | 查询任务列表（用于匹配） |

---

## 六、安全边界

| 边界 | 实现 |
|:-----|:------|
| CEO 不自执行具体任务 | 不调用 execute API |
| 审批操作必须 Founder 明确表达 | confidence + matched_targets 双阈值 |
| 模糊意图必须追问 | 不追问不得执行 |
| 所有操作可审计 | ceo_action_logs 强制写入 |
| 不绕过 Command Center safety gate | Execute 前仍需 dry-run + confirm |
| 不绕过 Review Gate | 任务完成仍需 Review |
| 不绕过 Learning Candidate 审批 | Learning Candidate 仍走 approval |

---

## 七、前端页面

### 7.1 CEO Workbench（新增页 `/ceo`）

v0.3 中 CEO Workbench 是 **工作台**，不是实时聊天入口。实际自然语言对话入口优先为飞书 / Hermes TUI。

- **创建 goal_session draft**：输入目标摘要，保存到后端（status=draft）
- **展示目标拆解结果**：查看已处理的 goal_sessions 和分解出的任务
- **展示 action_logs**：所有 CEO 代操作的审计日志
- **快速链接**：前往 Approval Center、TASK-POOL 查看审批/任务状态

> 不要求 v0.3 实现"前端输入 → 触发 Hermes 推理 → 实时返回"的完整链路。

### 7.2 Goal Sessions 页（新增 `/ceo/goals`）

- 最近目标列表
- 每个目标显示：摘要、状态（decomposed/committed/cancelled）、任务数、时间
- 点击进入详情：显示拆解结果 JSON

### 7.3 Action Logs 页（新增 `/ceo/logs`）

- 所有 CEO 操作的审计日志
- 按意图类型筛选：goal_intake / approval_action
- 每条显示：原始消息、目标类型、执行结果、时间

### 7.4 Task Detail 补充

任务详情页补充一行：
```
Created by CEO Agent
From goal_session_id: {id}
Goal: {goal_summary}
```

---

## 八、验收标准

### 验收 1：Goal Intake

**输入：**
> 亚马逊选品最近连续失败，帮我排查并推进修复。

**系统结果（全部通过）：**
1. ✅ `goal_sessions` 新增 1 条记录（status=committed）
2. ✅ `task_pool` 新增 2-5 条任务（status=approval_required）
3. ✅ 每条任务有 `context_packs` 记录（auto_generated=True）
4. ✅ `approvals` 表新增对应审批申请
5. ✅ `ceo_action_logs` 有 1 条 goal_intake 记录
6. ✅ CEO 返回结构化汇报
7. ⛔ 不触发任何 execute
8. ⛔ 不修改 OpenClaw runtime

### 验收 2：Approval Action

**输入：**
> 批准刚才创建的第一个任务

**系统结果（全部通过）：**
1. ✅ CEO 能定位唯一 approval
2. ✅ 调用 `PATCH /api/v1/approvals/{id}/decide` 完成 approved
3. ✅ approval 状态更新为 approved
4. ✅ task 状态同步更新
5. ✅ `ceo_action_logs` 有 1 条 approval_action 记录
6. ✅ 若匹配不唯一或置信度不足 → 追问，不执行

---

## 九、不做清单（速查）

```text
❌ 自动执行
❌ 自动分派 Agent
❌ 低风险自动批准
❌ Status Query 自然语言
❌ Task Follow-up 自然语言
❌ 每日简报自动化
❌ Monitor Agent
❌ Agent Meeting
❌ 多 Runtime
❌ 绕过 Approval Center
❌ 绕过 Command Center safety gate
❌ 绕过 Review Gate
❌ 绕过 Learning Candidate 审批
```

---

> **v0.3 CEO Agent Lite / Founder Intent Interface**
>
> 让 Founder 的自然语言意图第一次稳定进入 AI Company OS 的结构化闭环。
>
> Goal Intake + Approval Action：两个闭环，一步跃迁。
>
> 从"系统告警驱动闭环"到"Founder 目标驱动闭环"。
