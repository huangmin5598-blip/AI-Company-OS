---
version: v0.46.5
status: Active
last_updated: 2026-06-05
---
# OS Design Quality Gate — v0.46.4.3-B

> 版本：v0.46.4.3-B
> 更新：2026-06-05
> 状态：Active
> 关联：docs/architecture/agent-role-architecture.md / AI-COMPANY-OS-ROADMAP.md
> 自检：✅ 已通过 quality_gate v0.46.4.3 自检

---

## quality_gate Self-Check（v0.46.4.3 自检）

```yaml
quality_gate:
  version: v0.46.4.3
  checked_at: 2026-06-05T15:35:00+08:00
  self_check: true

  role_boundary_check: pass
    note: 本文档定义 Quality Gate 检查项，未定义 executor 角色

  source_of_truth_check: pass
    note: 所有检查项指向 os-skills/skill-registry.yaml / os-agents/agent-registry.yaml

  registered_skill_check: pass
    note: prd-reviewer skill 存在于 os-skills/prd/prd-reviewer.yaml

  task_card_governance_check: N/A
    note: 本文档为 Quality Gate 文档，非 Task Card

  file_boundary_check: pass
    note: 文档明确 inbox read-only / outbox write-only 规范

  p0_p1_p2_scope_check: pass
    note: P0 Governance 文档，无 P1/P2 执行内容

  context_access_boundary_check: pass
    note: Check 8 定义了 Context Access Matrix

  decision_authority_check: pass
    note: Check 9 定义了 Decision Authority Matrix

  blocking_issues: []
  warnings: []

  execution_allowed: true
  note: v0.46.4.3-B 为 Governance 文档，本身即为落地交付物
```

---

## 概述

所有 PRD / Task Card / Dispatch Plan / Architecture Patch / Roadmap Patch，在执行前必须通过质量门检查。

**不在此模块：** 代码校验器、数据库、UI、自动审批、复杂 policy engine（P1/P2 做）。

---

## 适用对象

- PRD（产品需求文档）
- Task Card（任务卡）
- Dispatch Plan（派工计划）
- Architecture Patch（架构变更）
- Roadmap Patch（路线调整）
- Memory Governance Rule（记忆治理规则）
- Release Plan（发布计划）

---

## 完整检查项（9项）

### Check 1：Role Boundary Check

```yaml
description: 检查 Hermes / OpenClaw / Agent 是否出现在错误角色位置

checks:
  - Hermes 是否出现在 executor 位置？
  - OpenClaw main 是否在做业务判断？
  - sub-agent 是否在做业务决策？
  - Coding Center 是否在做产品决策？

对应历史错误：
  - "Hermes 执行 RT-001/RT-002" → 应被拦截

blocking_issue_template: "<Agent> appears as <wrong_role> in <section>"
```

### Check 2：Source of Truth Check

```yaml
description: skill source 必须来自 os-skills/skill-registry.yaml

checks:
  - skill source 是否来自 os-skills/skill-registry.yaml？
  - manifest_ref 是否存在？

对应历史错误：
  - "source: hermes_skills_registry" → 应被拦截

blocking_issue_template: "skill source is <source>, must be os-skills/skill-registry.yaml"
```

### Check 3：Registered Skill Check

```yaml
description: required_skills 必须存在于 os-skills/skill-registry.yaml

checks:
  - required_skills 是否存在于 registry？
  - manifest_ref 是否存在？

对应历史错误：
  - "临时发明 campaign_experiment_planner" → 应被拦截

blocking_issue_template: "skill <skill_name> not found in os-skills/skill-registry.yaml"
```

### Check 4：Task Card Governance Field Check

```yaml
description: Task Card 必须包含所有治理字段

required_fields:
  - view_a_stage
  - view_b_layer
  - maturity
  - sensitivity
  - execution_boundary
  - value_check
  - assigned_to
  - review_required
  - expected_output_ref
  - required_skills
  - manifest_ref

blocking_issue_template: "Task Card missing governance field: <field>"
```

### Check 5：File Boundary Check

```yaml
description: 文件命名和边界规范

checks:
  - REQ 文件在 inbox/，RES 文件在 outbox/？
  - expected_output_ref 与 actual result 是否一致？
  - inbox 是否 read-only（Executor 不修改）？
  - outbox 是否 write-only？

对应历史错误：
  - 设计预期 REQ-001-result.yaml，实际 RES-001.yaml → warning

blocking_issue_template: "inbox file modified by executor"
warning_template: "expected_output: <filename>, actual: <filename> (naming inconsistency)"
```

### Check 6：P0/P1/P2 Scope Check

```yaml
description: 检查是否有 scope creep

checks:
  - P0 是否偷偷加了 Cron Poller？
  - P0 是否加了 API Gateway？
  - P0 是否把 ComfyUI/TTS/视频工具塞进 OS Core？
  - 是否跳级做了 P1 的内容？

对应历史错误：
  - v0.46.4.2 被写成 P1 Dispatch Worker → 应被拦截

blocking_issue_template: "scope creep detected: <feature> belongs to <phase>, not <current_phase>"
```

### Check 7：Evidence / Memory Candidate Check

```yaml
description: milestone 后必须生成 evidence / memory candidate

checks:
  - milestone 完成后是否有 internal record？
  - 是否有 evidence candidate？
  - 是否有 public narrative candidate？

blocking_issue_template: "milestone <id> completed but no evidence/memory candidate generated"
```

### Check 8：Context Access Boundary Check（新增）

```yaml
description: 检查每个 Agent 是否读取了超出权限的上下文

checks:
  - OpenClaw main 是否读了 Task Card 业务全文？
  - sub-agent 是否读了 Memory Core / Roadmap？
  - Coding Center 是否访问了未授权 repo？
  - PRD Agent 是否读了执行层日志？

reference: |
  | Agent | Can Read | Must Not Read |
  |-------|----------|---------------|
  | Hermes CEO | 完整上下文 | sub-agent scratchpad |
  | OpenClaw main | Execution Envelope + skill registry | Task Card 业务全文 |
  | sub-agent | Envelope + request + manifest | Memory Core / Roadmap |
  | Coding Center | Coding Task Card + repo | 非相关 repo |

blocking_issue_template: "<Agent> read context beyond its scope: <context>"
```

### Check 9：Decision Authority Check（新增）

```yaml
description: 检查每个 Agent 是否做了超出自己权限的决策

checks:
  - Hermes 是否在做执行？（应只有 Dispatch/Review）
  - OpenClaw main 是否在做业务判断？（应只有技术路由）
  - sub-agent 是否改了任务范围/优先级？
  - Coding Center 是否在做产品/业务决策？

reference: |
  | Agent | Can Decide | Must Not Decide |
  |-------|-----------|----------------|
  | Hermes CEO | 业务/战略/派工 | 执行/技术路由 |
  | OpenClaw main | 技术路由 | 业务/战略 |
  | sub-agent | 执行方式 | 任务范围/优先级 |
  | Coding Center | 代码实现 | 产品/业务 |

blocking_issue_template: "<Agent> exercised unauthorized decision authority: <action>"
```

---

## quality_gate Block 格式

每份方案输出前必须附此 block：

```yaml
quality_gate:
  version: v0.46.4.3-B
  checked_at: <timestamp>
  
  role_boundary_check: pass | fail
  source_of_truth_check: pass | fail
  registered_skill_check: pass | fail | N/A
  task_card_governance_check: pass | fail | N/A
  file_boundary_check: pass | warning | fail
  p0_p1_p2_scope_check: pass | fail
  evidence_memory_candidate_check: pass | fail | N/A
  context_access_boundary_check: pass | fail
  decision_authority_check: pass | fail
  
  blocking_issues: []
  warnings: []
  
  execution_allowed: true | false
```

**execution_allowed: false 时，方案不能进入执行。须修复所有 blocking_issues 后重新输出。**

---

## 分阶段交付

```
v0.46.4.3-A：Agent Role Architecture Contract（已完成）
v0.46.4.3-B：Quality Gate Contract（本文档）
