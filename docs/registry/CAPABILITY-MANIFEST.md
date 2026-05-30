---
title: "Capability Manifest — AI Company OS 能力声明"
domain: registry
---

# Capability Manifest

> **版本**：v0.28 · 2026-05-17  
> **用途**：声明所有 Actor（Agent / CLI / API / Automation）及其能力、边界、审批要求  
> **机器可读版**：`config/capability-manifest.yaml`  
> **详细注册表**：`config/capability-registry.yaml`（v0.24，含 workflow/project/skill 映射）  
> **动作边界规则**：`config/capability-boundary.yaml`（v0.27，5 类动作定义）

---

## 1. 什么是 Capability Manifest

Capability Manifest 是 AI Company OS 的能力声明层。它回答：

> 系统里有哪些 Actor？每个 Actor 能做什么、不能做什么、什么需要审批？

它与以下文件配合：

| 文件 | 管什么 | 
|:-----|:--------|
| `capability-manifest.yaml` | Actor 声明（actor_id / capabilities / boundaries / approval_required_actions） |
| `runtime-manifest.yaml` | 运行时声明（runtime_id / type / endpoint / capability_refs） |
| `capability-boundary.yaml` | 动作分类规则（read_only / safe_output / approval_required / elevated_write / forbidden） |

---

## 2. Actor 分类

共 **10 个 Actor**，分 4 层：

### Layer 1: Founder-facing（2 个）

| Actor ID | 类型 | Runtime | 说明 |
|:---------|:-----|:---------|:------|
| `hermes-main` | founder_facing_agent | hermes-local | 首席参谋——战略、规划、开发 |
| `founder-console-api` | system_api | hermes-local | Founder Console API 端点层 |

### Layer 2: System Command（1 个）

| Actor ID | 类型 | Runtime | 说明 |
|:---------|:-----|:---------|:------|
| `ceo-cmd-interface` | system_command_interface | hermes-local | CEO CLI——查询、草稿、审计 |

### Layer 3: Specialist Agents（4 个）

| Actor ID | 类型 | Runtime | 说明 |
|:---------|:-----|:---------|:------|
| `research-agent` | specialist_agent | openclaw-local | 研究与信息合成 |
| `finance-analyst` | specialist_agent | openclaw-local | 财务与成本分析 |
| `content-manager` | specialist_agent | openclaw-local | 多格式内容生产 |
| `codex` | developer_agent | codex-stub | 代码开发 |

### Layer 4: Runtime & Platform（2 个）

| Actor ID | 类型 | Runtime | 说明 |
|:---------|:-----|:---------|:------|
| `openclaw-gateway` | runtime_platform | openclaw-local | 模型网关与任务调度 |
| `openclaw-worker` | runtime_platform | openclaw-local | 后台任务执行 |

### Automated（1 个）

| Actor ID | 类型 | Runtime | 说明 |
|:---------|:-----|:---------|:------|
| `daily-operating-loop` | automation | hermes-local | 每日自动化循环 |

### Administration（1 个）

| Actor ID | 类型 | Runtime | 说明 |
|:---------|:-----|:---------|:------|
| `system-admin` | administration | hermes-local | 受信管理员 |

---

## 3. Capability Ref 总览

Manifest 中定义的所有 capability 标识，供 `runtime-manifest.yaml` 引用：

| Capability | 拥有者 |
|:-----------|:--------|
| `strategy_discussion` | hermes-main |
| `product_planning` | hermes-main |
| `architecture_design` | hermes-main |
| `research_coordination` | hermes-main |
| `code_development` | hermes-main |
| `status_query` | ceo-cmd-interface, founder-console-api |
| `asset_query` | ceo-cmd-interface, founder-console-api |
| `draft_from_decision` | ceo-cmd-interface |
| `web_research` | research-agent |
| `report_generation` | research-agent |
| `cost_analysis` | finance-analyst |
| `code_generation` | codex |
| `code_review` | codex |
| `model_routing` | openclaw-gateway |
| `task_execution` | openclaw-gateway, openclaw-worker |
| `ceo_brief_generation` | daily-operating-loop |
| `config_update` | system-admin |

---

## 4. boundary_profile 分类

Manifest 定义了 7 种 boundary profile：

| Profile | 示例 Actor | 说明 |
|:--------|:-----------|:------|
| `founder_facing_agent` | hermes-main | 高权限但不可绕过 Founder |
| `system_command_interface` | ceo-cmd-interface | 只读 + 草稿生成，不可执行 |
| `specialist_agent` | research-agent | 专精领域，沙箱受限 |
| `developer_agent` | codex | 代码变更，仅限 staging |
| `runtime_platform` | openclaw-gateway | 执行层，无自主决策 |
| `automation` | daily-operating-loop | 安全输出，不可写入 |
| `system_api` | founder-console-api | API 层，权限等同 CLI |
| `administration` | system-admin | 提升写入，但不可 forbidden |

---

## 5. 与 capability_boundary.py 的关系

`capability_boundary.py` 读取：

```
1. capability-boundary.yaml → action classification（必要）
2. capability-manifest.yaml → actor capabilities（可选）
```

如果 `capability-manifest.yaml` 存在，boundary.py 可以：
- 列出所有 actor 的 approval_required_actions
- 检查某 actor 的 boundary_profile
- 交叉引用 runtime_ref 以校验运行时是否存在

如果 `capability-manifest.yaml` 缺失，boundary.py 仍可正常执行基本的 action boundary 检查。

---

## 6. 当前限制

- Manifest 仅声明能力，不自动绑定到运行时（需 `company-instance.yaml` 选择启用）
- Manifest 不包含 Workflow 和 Project 映射（见 `capability-registry.yaml`）
- 多实例环境尚未支持
- Manifest 变更不热加载
