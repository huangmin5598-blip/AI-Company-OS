---
version: v0.46.5
status: Active
last_updated: 2026-06-05
---
# Agent Role Architecture — v0.46.4.3-A

> 版本：v0.46.4.3-A
> 更新：2026-06-05
> 状态：Active
> 自检：✅ 已通过 quality_gate v0.46.4.3 自检

---

## quality_gate Self-Check（v0.46.4.3 自检）

```yaml
quality_gate:
  version: v0.46.4.3
  checked_at: 2026-06-05T15:35:00+08:00
  self_check: true

  role_boundary_check: pass
    note: Hermes CEO 定义为 Business Dispatcher，无 executor 角色

  source_of_truth_check: pass
    note: 所有 skill reference 指向 os-skills/skill-registry.yaml

  registered_skill_check: pass
    note: role-contracts 引用的 skill 全部存在于 os-skills/

  task_card_governance_check: N/A
    note: 本文档为架构文档，非 Task Card

  file_boundary_check: pass
    note: Execution Envelope 明确 inbox read-only / outbox write-only

  p0_p1_p2_scope_check: pass
    note: P0 架构合同，无 P1/P2 执行内容

  context_access_boundary_check: pass
    note: 每个 role contract 明确 can_read / must_not_read

  decision_authority_check: pass
    note: Business Decision / Technical Routing / Execution 三层分离清晰

  blocking_issues: []
  warnings: []

  execution_allowed: true
  note: v0.46.4.3-A 为架构文档，本身即为落地交付物
```

---

## 核心架构原则（三层职责分离）

```
Business Decision  → Hermes CEO
Technical Routing  → OpenClaw main
Execution → sub-agents / Coding Center / Specialist Agents
```

**谁读什么 + 谁决定什么 + 谁写什么结果 → 三权分离**

---

## Execution Envelope 概念

### 定义

```
Task Card = 给 Hermes / Lead / Reviewer 看的业务派工卡
Execution Envelope = 给 OpenClaw main 看的最小执行包
```

**目的：**
- Hermes 不做人肉转发（完整 Task Card 在 Hermes）
- OpenClaw main 只读技术参数，不读业务上下文
- 未来 Cron Poller 可直接扫描 Execution Envelope

### Schema

```yaml
execution_envelope_id: EE-{id}
task_id: RT-{id}
request_id: REQ-{id}
created_by: hermes-ceo

required_skills:
  - {skill_name}

skill_registry_ref: os-skills/skill-registry.yaml

manifest_ref:
  - os-skills/{category}/{skill-name}.yaml

input_ref: private/capability-requests/inbox/REQ-{id}.yaml
output_ref: private/capability-requests/outbox/RES-{id}.yaml

allowed_actions:
  - read_execution_envelope
  - read_capability_request
  - read_relevant_skill_manifest
  - write_outbox_result
  - update_execution_status

forbidden_actions:
  - modify_inbox
  - make_business_decision
  - change_task_priority
  - rewrite_task_scope
  - read_business_context
  - access_private_memory

# 执行后填写
executed_by: <sub-agent-id>
child_session_id: <if spawned>
execution_time_ms: <measured>
status: done | error
written_by: <sub-agent | openclaw-main-on-behalf-of-subagent>
```

---

## Agent 分层架构

```
Layer 1：公司经营层
├── Founder（战略目标 / 最终批准 / 重大边界）
└── Hermes CEO Agent（战略 / 派工 / Review / 治理 / 风险升级）

Layer 2：产品线 Lead Agents
├── AI Music Lead
├── AI Novel Lead
├── OS Infrastructure Lead
├── Growth Lead（规划中）
└── Narrative Lead（规划中）

Layer 3：共享能力中心 / Specialist Agents
├── PRD Agent
├── Research Agent
├── Content Agent
├── Reviewer Agent
├── Evidence / Memory Agent
└── Coding Center（Codex + Claude Code）

Layer 4：Executor Runtime
├── OpenClaw main（Technical Router / Executor Gateway）
└── OpenClaw sub-agents
```

---

## 执行链路

```
Founder
  ↓战略目标
Hermes CEO
  → 创建完整 Task Card（业务上下文）
  → 生成 Execution Envelope
  → 调用 OpenClaw main（发送 Execution Envelope，不发 Task Card 全文）
  → OpenClaw main：只读 Execution Envelope + required_skills
  → 查 skill-registry.yaml → sessions_spawn 到对应 sub-agent
  → sub-agent：读 Execution Envelope + capability request + manifest + output schema
  → sub-agent 写 outbox result
  → OpenClaw main 更新 Execution Envelope status
  → Hermes Review 最终结果
```

---

## sub-agent spawn 触发规则

```yaml
触发条件：
  required_skills 匹配 os-skills/skill-registry.yaml 中的 capability

spawn 路径：
  1. OpenClaw main 读取 Execution Envelope.required_skills
  2. 查 skill-registry.yaml 获取 agent_id
  3. sessions_spawn(runtime="subagent", agent=<agent_id>)
  4. sub-agent 执行
  5. sub-agent 写 RES 到 outbox
  6. OpenClaw main 更新 Execution Envelope status

适合场景：
  - 明确需要某种 skill（codex / prd-review / memory）
  - 可并行拆解
  - 需要隔离执行环境

不适合场景：
  - 需要多轮对话澄清的业务决策 → Hermes 处理
  - 需要跨多个 agent 协调的工作流 → 用 taskflow
```

---

## Context Access Matrix

| Agent | Can Read | Must Not Read |
|-------|----------|---------------|
| Hermes CEO | 完整 Task Card / Memory Core / Roadmap / 所有产品线上下文 / finalized outbox result | sub-agent internal session / scratchpad |
| OpenClaw main | Execution Envelope / skill-registry / relevant manifest | Task Card 业务全文 / Memory / Roadmap |
| Lead Agent | 本产品线 Task Card / 本线 Memory / OS Skill Registry | 其他产品线私密数据 |
| PRD Agent | PRD brief / requirements | 执行层私有日志 |
| Research Agent | Research brief / OS Research Capability Layer / signal data | 其他产品线私密 roadmap |
| Reviewer Agent | PRD / Task Card / Quality Gate / evidence | 不必要的账号/密钥/私人数据 |
| Evidence Agent | records / evidence / memory candidates | 任务执行中间状态 |
| Codex | repo / coding task / tests | 非相关 repo / Memory Core |
| Claude Code | repo / coding task / local context / MCP tools | 非相关 repo |

---

## Coding Center — 两条调用路径

```yaml
Route A（当前 P0 enabled）:
  Hermes / Lead → OS Task Card → Coding Center Adapter → Codex / Claude Code
  status: enabled
  note: P0 主要路径

Route B（P1 验证）:
  Hermes / Lead → Execution Envelope → OpenClaw main → required_skills=codex/claude-code → coding sub-agent
  status: P1 待验证
  note: P1 再验证是否统一走 OpenClaw main

deployment:
  current: local CLI（Codex + Claude Code）
  future: cloud mode / GitHub mode 作为 adapter profile
```

---

## OS Research Capability Layer 与 Research Agent 关系

```
OS Research Capability Layer（OS 拥有，方法论+工具+流程+数据结构）
    ↑ 被调用
Research Agent（执行具体研究任务）

Feedback 路径：
Research Agent → 反馈优化建议 → OS Governance approval → 更新 OS Research Capability Layer

约束：Research Agent 不得在未经 Architecture/Governance approval 的情况下私自修改方法论。
```

---

## 分阶段交付

```
v0.46.4.3-A：Agent Role Architecture Contract（本文件）
v0.46.4.3-B：Quality Gate Contract（docs/governance/os-design-quality-gate.md）
```

关联文件：
- os-agents/agent-registry.yaml
- os-agents/execution-envelope-schema.yaml
- role-contracts/hermes-ceo.yaml
- role-contracts/openclaw-main.yaml
- role-contracts/research-agent.yaml
- role-contracts/coding-center.yaml