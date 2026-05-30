---
title: "Safe Output Policy — AI Company OS 安全输出策略"
domain: governance
---

# Safe Output Policy — 安全输出策略

> **版本**：v0.28 · 2026-05-17  
> **用途**：定义 AI Company OS 所有输出的格式规则、脱敏要求、审批条件  
> **机器可读版**：`config/safe-output-policy.yaml`  
> **与 Capability Boundary 的关系**：Boundary 管"能不能做"，Safe Output Policy 管"做了以后输出要长什么样"

---

## 1. 与 Capability Boundary 的分工

| 文件 | 管什么 | 问题 |
|:-----|:--------|:------|
| `capability-boundary.yaml` | 动作分类 | 这个 actor 能不能执行这个 action？ |
| `safe-output-policy.yaml` | 输出规则 | 如果允许输出，输出物必须满足什么安全要求？ |

两者互补但不重叠。Boundary 决定是否放行，Policy 决定放行后的输出格式。

---

## 2. 允许的输出类型

共 8 种允许的输出类型：

| 类型 | 说明 | 格式 | 脱敏 | Source Ref | Founder Review |
|:-----|:------|:-----|:-----|:-----------|:---------------|
| `markdown_report` | CEO Brief、研究报告 | Markdown | ✅ | ✅ 必填 | ❌ |
| `work_order_draft` | 工单草稿 | Markdown | ✅ | ✅ 必填 | ❌ |
| `decision_log_entry` | 决策日志条目 | Markdown Table | ❌ 已安全 | ✅ 必填 | ❌ |
| `evidence_summary` | 公开证据看板 | JSON/MD | ✅ | ❌ | ✅ 必须 |
| `patch_preview` | 代码变更预览 | Diff | ✅ | ❌ | ✅ 必须 |
| `command_dry_run` | Dry-run 预览输出 | Markdown | ✅ | ✅ 必填 | ❌ |
| `operating_kit_doc` | 运营套件文档 | Markdown | ✅ | ❌ | ✅ 必须 |
| `template_doc` | 可复用模板 | Markdown | ✅ | ❌ | ✅ 必须 |

---

## 3. 脱敏规则（Redaction Rules）

所有 `redact: true` 的输出类型在最终输出前必须经过以下脱敏处理：

### 必选规则（所有输出）

| 规则 | 替换 | 来源 |
|:-----|:------|:------|
| 本地绝对路径 | `<local_home>/` | v0.26 evidence allowlist |
| API Key / Token / Secret | `<redacted>` | v0.26 sanitize |
| 环境变量值 | `<env_var_redacted>` | 新增 v0.28 |
| 原始 LLM Prompt | `<prompt_redacted>` | 新增 v0.28 |

### 可选规则（仅公开文档）

| 规则 | 替换 | 适用场景 |
|:-----|:------|:---------|
| 私有项目名称 | `<project_name>` | Evidence Dashboard、Release Notes |

---

## 4. 输出要求

### Source Ref 要求

涉及运营流程的输出（Brief / Draft / Decision / Dry-run）必须包含源头引用：

```
_Source: reports/ceo-briefs/2026-05-30.md | Decision: DEC-20260530-001_
```

### Founder Review 要求

以下输出类型在公开前必须经 Founder 确认：

- `evidence_summary` — 公开证据看板
- `operating_kit_doc` — 方法论文档
- `template_doc` — 模板
- `patch_preview` — 代码变更

其他类型（Brief / Draft / Decision / Dry-run）不需要额外审批。

---

## 5. 与现有系统的关系

| 现有组件 | 关系 |
|:---------|:------|
| `backend/app/services/evidence_summary_service.py` | 实现了 v0.26 的 allowlist + sanitize，是 Safe Output Policy 的代码级实现 |
| `docs/evidence/EVIDENCE-DASHBOARD-LITE-v0.26.md` | 符合 Safe Output Policy — 已脱敏、不含敏感路径 |
| `docs/operating-kit/` | 符合 Safe Output Policy — 创建时已检查不泄露敏感信息 |
| `capability-boundary.yaml` | `safe_output` 类动作的产出物受 Safe Output Policy 约束 |

---

## 6. 当前限制

- 脱敏规则当前通过 `evidence_summary_service.py` 手工实现，无通用脱敏中间件
- 输出类型检查为非运行时强制（请通过 `scripts/manifest_validator.py` 校验）
- 未集成到 `capability_boundary.py`——目前 boundary 只检查"能否做"，不检查"输出是否合规"
- 未来应增加：输出类型自动标注 + 脱敏自动流水线
