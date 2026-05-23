# AI Company Control Center v0.2 — Company Loop MVP PRD

> **状态**: 📋 PRD · 待执行
> **预估工时**: 14-18h（约 2-3 天冲刺）
> **验收标准**: 一条真实告警完整跑通闭环
>
> **定位**: v0.2 将 Control Center 从"可见层"升级为 AI Company OS 的第一个"公司运行闭环"。
> 让每个重要动作都能被记录、被上下文化、被确认、被执行、被验收，并产生可复用的学习候选项。

---

## 一、产品定位

### 一句话定义

> **v0.2 = AI Company OS 的第一个公司运行闭环层。**
> **Intention Engine = v0.2 的核心子系统（TASK-POOL + Context Pack）。**

### 核心链路

```
Alert / Command / Manual Input
    → Task（意图注册）
    → Context Pack（公司上下文绑定）
    → Approval（Founder 确认）
    → Execute（Command Center 执行）
    → Review（三态验收）
    → Learning Candidate（自我改进入口）
```

### 回答的问题

> **公司可以闭环执行了吗？**

v0.1.x 回答了"公司可读了吗？"（✅ 数据可信）。
v0.2 回答"公司能把一个意图变成可记录、可执行、可验收、可学习的闭环吗？"

---

## 二、范围

### 做

| 模块 | 说明 | 优先级 |
|:-----|:------|:------:|
| **TASK-POOL** | 唯一任务源/意图寄存器（产品概念上为现有 tasks 能力升级；工程实现上新建 task_pool 表，旧 tasks 表不动） | P0 |
| **Context Pack** | 每个任务绑定的最小公司上下文（含知识库引用） | P0 |
| **Approval Center** | Founder 自确认/决策留痕，不是企业审批流 | P0 |
| **Review Gate** | PASS / REVISION REQUIRED / BLOCKED 三态验收 | P0 |
| **Learning Candidate** | 失败/经验/规则/工具缺口/资产沉淀的候选入口 | P0 |
| **Alert 自动入池** | 已有告警 → 自动生成 Task + Context Pack → 入审批 | P0 |
| **冷启动迁移** | alerts / command_logs / execution_records → 首批数据 | P0 |
| **TASK-POOL 预留字段** | execution_runtime / execution_mode / execution_workspace | P1 |
| **Context Pack 引用知识库** | 引用 AI-Knowledge-OS page slug | P1 |
| **Loop Dashboard** | 闭环指标总览 | P1 |

### 不做

| 不做 | 原因 |
|:-----|:------|
| CEO Agent | → v0.3（Hermes Panel 自然升级） |
| 完整 Monitor Agent | → v0.4 |
| Agent Meeting Session | → v0.7 |
| 多 Runtime 接入 | → v0.6 |
| 自动修复（Learning Candidate 自动执行） | → v0.5+ |
| Learning Candidate 自动写入知识库 | → v0.2.1 |
| Tool Registry 完整新表 | v0.2 只需 `/tools` 端点列可用工具清单 |
| Event Trace 新表 | 不新建 task_events 表，command_logs 只关联 task_pool |
| RAG / 自动知识库搜索 | Context Pack 仅手动引用 page slug |

---

## 三、验收标准（游标卡尺）

**v0.2 的最低完成标志：一条真实告警完整走完以下链路。**

| 步骤 | 具体检验点 | 通过标准 |
|:----:|:-----------|:---------|
| 1 | Alert 自动入池 | 一个真实 alert（如"亚马逊选品 400 错误"）自动生成 task_pool 任务 |
| 2 | Task 带 Context Pack | Context Pack 包含 alert 详情、关联 cron、历史 run、知识库引用 |
| 3 | 进入 Approval Center | Founder 可以 approve / revise / reject / defer |
| 4 | Approved 后可执行 | 通过 Command Center 执行，默认 dry-run，execute 仍受安全门控 |
| 5 | 执行结果进入 Review | 支持 PASS / REVISION REQUIRED / BLOCKED |
| 6 | Review 后生成 Learning Candidate | 例如 failure_pattern_candidate / tool_gap_candidate / context_update_candidate |
| 7 | Learning Candidate 进入审批 | 状态为 pending_approval，Founder 可以 approve / reject |

> 步骤 7 的"approve"只更新审批状态，不自动写入知识库（→ v0.2.1）。

---

## 四、数据模型

### 4.1 task_pool（产品概念上为现有 tasks 能力升级；工程实现上新建 task_pool 表，旧 tasks 表不动）

```
字段名              类型          说明
─────────────────────────────────────────────────────────
id                  Integer PK    自增主键
title               String        任务标题（必填）
description         Text          任务描述
business_line       String        业务线（openclaw / novel / amazon / ...）
source              String        来源：alert / command / manual / cron
source_id           String        上游 ID（如 alert_id / command_log_id）

status              String        日/WIP/审批/排队/执行/验收/完成/阻塞/取消
                    draft → ready → approval_required → approved → running → review → done
                    ↕ blocked / revision_required

priority            String        low / medium / high / critical
risk_level          String        low / medium / high
assigned_agent      String        执行 Agent（如 amazon-seller）
context_pack_id     Integer       FK → context_packs.id（nullable）
requires_approval   Boolean       默认 true
acceptance_criteria Text         完成标准

result_summary      Text          执行结果摘要
error_message       Text          失败原因
cost_usd            Float         执行成本
failure_reason      Text          失败原因（用于 Learning Candidate）

execution_runtime   String        预留，默认 "openclaw"
execution_mode      String        预留：standard / lite / resume / blocked
execution_workspace String        预留：sandbox path

created_at          DateTime
updated_at          DateTime
completed_at        DateTime
```

**状态机：**

```
draft ──→ ready ──→ approval_required ──→ approved ──→ running ──→ review ──→ done
  │          │             │                  │            │           │
  └── cancelled   └── cancelled    └── revision_required ──→ approval_required
                                                              (re-entry)
                           └── rejected ─→ done
                                              └── blocked ─→ review
                                                     │
                                                     └── done
```

### 4.2 context_packs

```
字段名                  类型          说明
─────────────────────────────────────────────────────────
id                      Integer PK
task_id                 Integer       FK → task_pool.id（1:1）
founder_intent          Text          Founder 想达成什么
business_line_state     Text          业务线当前状态
related_runs            Text          JSON: ["run-id-1", "run-id-2"]
related_artifacts       Text          JSON: ["artifact-id"]
known_failures          Text          JSON: 已知失败模式
relevant_rules          Text          JSON: 适用协议/SOP
constraints             Text          执行约束
forbidden_actions       Text          禁止做的事
budget_limit            Float         预算上限
acceptance_criteria     Text          验收标准（和 task 层可不同粒度）

referenced_knowledge    Text          JSON: [{title, path, slug, reason}]
                                    ← 引用 AI-Knowledge-OS 页面

auto_generated          Boolean       默认 false。true 表示由系统生成草稿
created_at              DateTime
updated_at              DateTime
```

### 4.3 approvals

```
字段名                  类型          说明
─────────────────────────────────────────────────────────
id                      Integer PK
target_type             String        task / command / learning_candidate
target_id               Integer       关联目标 ID
risk_level              String        low / medium / high
reason                  Text          申请理由（系统建议或人工填写）
founder_decision        String        approved / revised / rejected / deferred
founder_notes           Text          Founder 判断依据
decision_context        Text          JSON: 决策时的系统状态快照
status                  String        approval_requested / approved / rejected
                                      / expired / executed / cancelled
approved_at             DateTime
created_at              DateTime
```

### 4.4 reviews

```
字段名                  类型          说明
─────────────────────────────────────────────────────────
id                      Integer PK
task_id                 Integer       FK → task_pool.id
result                  String        pass / revision_required / blocked
artifact_id             String        产物 ID（如果有）
review_notes            Text          Review 备注
next_action             String        若 blocked 或 revision_required，下一步做什么
reviewed_by             String        "founder"（单人公司固定值）
created_at              DateTime
```

### 4.5 learning_candidates

```
字段名                  类型          说明
─────────────────────────────────────────────────────────
id                      Integer PK
source_type             String        failure / tool_gap / context_update
                                      / rule_update / asset_candidate
source_id               String        关联来源 ID（如 alert_id / task_id）
source_summary          Text          来源摘要
candidate_type          String        failure_pattern / tool_gap / context_update
                                      / rule_update / sop_update / asset
summary                 Text          候选项摘要
recommendation          Text          建议操作
approval_status         String        pending_approval / approved / rejected
                                      / approved_for_knowledge_update
approved_by             String        nullable, "founder" 时填写
approved_at             DateTime
created_at              DateTime
```

**生成规则：**
- Review = `blocked` 或 `revision_required` → 自动建议生成 Learning Candidate
- Review = `pass` → 默认不生成，除非 Founder 手动创建 `asset_candidate`

---

## 五、API 端点

| 端点 | 方法 | 功能 |
|:-----|:----:|:-----|
| `/api/v1/task-pool` | GET | 任务列表（支持 status/business_line/source 筛选） |
| `/api/v1/task-pool` | POST | 创建任务 |
| `/api/v1/task-pool/{id}` | GET | 任务详情（含 Context Pack + Approval + Review） |
| `/api/v1/task-pool/{id}` | PATCH | 更新任务状态 |
| `/api/v1/task-pool/{id}/context-pack` | GET | 获取 Context Pack |
| `/api/v1/task-pool/{id}/context-pack` | POST | 创建/更新 Context Pack |
| `/api/v1/approvals` | GET | 待审批列表 |
| `/api/v1/approvals` | POST | 创建审批申请 |
| `/api/v1/approvals/{id}/decide` | PATCH | Founder 决策（approve/revise/reject/defer） |
| `/api/v1/reviews` | POST | 提交 Review |
| `/api/v1/reviews/{id}` | GET | Review 详情 |
| `/api/v1/learning-candidates` | GET | Learning Candidate 列表 |
| `/api/v1/learning-candidates` | POST | 创建 Candidate |
| `/api/v1/learning-candidates/{id}/decide` | PATCH | Founder 审批 Candidate |
| `/api/v1/loop-stats` | GET | 闭环总览指标 |
| `/api/v1/alert-to-task` | POST | 手动触发告警入池（含自动入池逻辑） |

---

## 六、前端页面

### 6.1 TASK-POOL / 任务总览（升级 /tasks）

- 展示所有任务：状态、来源、风险、业务线、审批状态
- 筛选：status / business_line / source / priority
- 快速操作：创建任务、进入任务详情
- 状态标签：颜色区分（draft=灰, ready=蓝, approval_required=黄, approved=绿, running=青, review=紫, done=灰勾）
- 空状态："暂无任务。系统正在监听告警，发现失败将自动创建任务。"

### 6.2 Task Detail / 任务详情（新页面）

- 任务基本信息：标题、描述、状态、来源、优先级、风险
- Context Pack 面板：展开/收起，引用知识库链接
- Approval 面板：审批状态、Founder 决策记录
- Review 面板：Review 结果、关联 artifact
- 关联数据：关联的 Alerts / Runs / Artifacts
- 操作按钮：提交审批、执行（跳转 Command Center）、提交 Review

### 6.3 Approval Center / 审批中心（新页面 /approvals）

- 一人公司自确认设计：不是企业审批流
- 展示：待审批项、已决审批历史
- 每项显示：来源（来自 Alert？Command？）、风险等级、系统推荐理由、
  关联历史、影响范围
- 操作按钮：Approve / Revise / Reject / Defer
- 决策留痕：每次选择记录到 approvals 表

### 6.4 Loop Dashboard / 闭环总览（新页面 /loop）

- 展示闭环指标：
  - 本周任务总数
  - 告警入池数
  - 审批通过率
  - Review 结果分布（PASS % vs REVISION % vs BLOCKED %）
  - Learning Candidate 生成数
  - Learning Candidate 批准数
- 趋势图：任务创建趋势、闭环完成趋势
- 当前瓶颈："当前有 X 个任务等待审批"或"X 个 Candidate 待处理"

---

## 七、冷启动链路（关键）

v0.2 不是从空系统开始。已有数据需要迁移：

### 7.1 首批数据来源

| 数据源 | 当前数量 | 迁移目标 |
|:-------|:--------:|:---------|
| **alerts**（未解决） | 6 | 自动生成 6 条 Task + 6 个 Context Pack（含失败上下文） |
| **alerts**（已解决） | 2 | 标记为已处理的 Learning Candidate |
| **command_logs** | 4 | 首批事件记录（扩展 command_logs 的用途，不新建 task_events 表） |
| **execution_records** | 14 | 关联到已完成任务的 Review 数据 |

### 7.2 自动入池逻辑

```
POST /api/v1/refresh 之后新增一步:
  ↓
alert_detector 扫描到 unresolved alerts
  ↓
对每个未解决的 alert:
  a. 检查是否已有关联 task (避免重复)
  b. 若无，自动创建 Task (status=approval_required, source=alert, source_id=alert.id)
  c. 自动生成 Context Pack 草稿
     - founder_intent = "修复{alert.title}，恢复正常执行"
     - related_runs = 从 execution_records 匹配的业务线运行记录
     - known_failures = alert.description
     - auto_generated = True
  d. 自动创建 Approval (target_type=task, status=approval_requested)
  e. Alert 标记 resolved=2 (表示"已入池")
```

---

## 八、补充约束

| # | 约束 | 说明 |
|:-:|:-----|:------|
| 1 | `alerts.resolved` 状态码 | `0` = unresolved（未处理）, `1` = resolved（已解决）, `2` = pooled_to_task（已入池） |
| 2 | Alert 自动入池去重 | 必须按 `source_type=alert` + `source_id` 检查唯一性，避免同一告警生成重复 task |
| 3 | Context Pack auto_generated 标记 | `auto_generated=True` 的 Context Pack 在前端必须标记为 **Draft**，Founder 确认后才能变为 active |
| 4 | Approval 通过 ≠ 可执行 | Approval 通过后，执行仍需经过 Command Center safety gate（dry-run → ALLOW_ALPHA_WRITE → X-Confirm） |

---

## 九、安全边界

| 边界 | 实现方式 |
|:-----|:---------|
| Approval Center 不绕过 Command Center safety gate | Approval 通过后，执行仍走 Command Center dry-run → execute 流程 |
| Learning Candidate 不自动执行 | 只生成 + 审批，不写入知识库，不调 Agent |
| Context Pack 不自动生成完整版 | 系统生成的标记 `auto_generated=True`，Founder 需确认 |
| Alert 入池不覆盖人工创建 | 自动入池检查 `alert_id` 是否已有关联 task |

---

## 九、不做清单（速查）

```
❌ CEO Agent
❌ Monitor Agent
❌ Agent Meeting Session
❌ 多 Runtime
❌ 自动修复
❌ 自动写知识库
❌ RAG / 知识库搜索
❌ Tool Registry 新表
❌ Event Trace 新表
❌ 企业级多角色审批
❌ 权限系统
❌ 移动端适配
```

---

> **v0.2 Company Loop MVP / 公司闭环层 MVP**
>
> 验收标准只有一条：一个真实告警能否完整走完闭环？
>
> Alert → Task → Context → Approval → Execute → Review → Learning Candidate
>
> 这步做完，AI Company OS 从"看得见"进入"会运转"。
