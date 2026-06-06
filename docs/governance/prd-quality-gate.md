---
version: v0.46.5
status: Active
last_updated: 2026-06-05
---
# PRD Quality Gate — v0.46.4.3-B

> 版本：v0.46.4.3-B
> 更新：2026-06-05
> 关联：docs/governance/os-design-quality-gate.md / templates/prd/prd-template.md

---

## 概述

PRD 在提交执行前必须通过 PRD 专项 Quality Gate 检查。

---

## PRD 专项检查项（9项）

在 OS Design Quality Gate 基础上，PRD 需额外/重点检查以下项：

### PRD-Check 1：背景对齐检查

```
是否清晰说明了「为什么这个 PRD 重要」？
是否明确了「目标用户是谁」？
是否定义了「什么不算这个 PRD 的范围」？
```

### PRD-Check 2：数据模型完整性

```
是否定义了所有核心数据实体？
字段是否有类型和描述？
关系是否清晰？
```

### PRD-Check 3：状态机完整性

```
所有状态流转是否都有定义？
异常状态是否有处理？
是否有死路状态（无法到达终态）？
```

### PRD-Check 4：API / CLI / File Contract 完整性

```
所有接口是否都有输入/输出定义？
是否定义了错误码和错误处理？
参数是否有约束条件说明？
```

### PRD-Check 5：验收标准可验证性

```
每条验收标准是否可执行/可测试？
是否避免了模糊表述（如「用户友好」）？
是否覆盖了正向和异常路径？
```

### PRD-Check 6：Evidence / Memory / Asset 定义

```
是否定义了需要生成的 evidence？
是否定义了 memory candidate？
是否定义了需要沉淀的 asset？
```

### PRD-Check 7：依赖关系明确性

```
所有外部依赖是否都列出？
依赖项的负责人是否明确？
依赖项的风险是否评估？
```

### PRD-Check 8：PRD Review Workflow 合规

```
是否符合「GPT 初审 → Hermes 修 → GPT 终审」的流程？
review_status 是否正确更新？
execution_allowed 是否在 approved 后才改为 true？
```

---

## PRD 审核工作流

```
PRD Agent 写初稿
  → GPT 初审（9项检查）
  → Hermes 修（针对 blocking_issues）
  → GPT 终审（确认 blocking_issues 已修复）
  → Founder 批准（或驳回重写）
  → execution_allowed: true
  → 进入执行
```

---

## PRD quality_gate Block

```yaml
prd_quality_gate:
  version: v0.46.4.3-B
  checked_at: <timestamp>
  review_round: 1 | 2 | 3
  
  prd_check_1_background: pass | fail
  prd_check_2_data_model: pass | fail
  prd_check_3_state_machine: pass | fail
  prd_check_4_api_contract: pass | fail
  prd_check_5_acceptance_criteria: pass | fail
  prd_check_6_evidence_memory_asset: pass | fail
  prd_check_7_dependencies: pass | fail
  prd_check_8_workflow_compliance: pass | fail
  
  blocking_issues: []
  warnings: []
  
  review_status: pending_review | in_revision | approved | rejected
  execution_allowed: false
```
