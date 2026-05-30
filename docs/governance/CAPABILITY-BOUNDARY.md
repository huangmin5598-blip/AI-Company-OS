---
title: "Capability Boundary — AI Company OS 能力边界规则"
domain: governance
---

# Capability Boundary — AI Company OS 能力边界规则

> 版本：v0.1 · 2026-05-17  
> 用途：定义 AI Company OS 中所有 actor（Agent / CLI / API / Automation）的默认权限边界。  
> 核心原则：**默认只读、安全输出、审批写入、危险禁止**

---

## 1. 设计哲学

AI Company OS 的治理模型借鉴了操作系统级安全原则：

| 原则 | 含义 |
|:-----|:------|
| **默认只读** | 任何 actor 默认只能查询系统状态，不能修改 |
| **安全输出** | 允许生成仅供阅读的输出（Brief / Draft / Report），不产生副作用 |
| **审批写入** | 写入操作需要人工审批或明确授权 |
| **危险禁止** | 可能破坏系统完整性或泄露敏感数据的动作直接禁止 |

这四条是 AI Company OS 的**治理宪章**，所有能力边界规则由此推导。

---

## 2. 五类动作定义

### 2.1 `read_only` — 只读查询

无副作用的系统查询。允许任何 actor 不带审批执行。

**示例**：
- 查询系统状态（status_query）
- 查询资产（asset_query）
- 查询资产链路（lineage_query）
- 查询能力注册表（capability_lookup）
- 预检健康检查（preflight_check）

**限制**：仅返回已有数据，不产生新记录。

---

### 2.2 `safe_output` — 安全输出

生成仅供阅读的输出产品。允许自动化执行，无需人工审批，但输出不能包含敏感字段。

**示例**：
- 生成 CEO Brief（generate_ceo_brief）
- 生成 Review 模板（generate_review_template）
- 生成 Work Order Draft（generate_work_order_draft）
- 生成证据摘要（generate_evidence_summary）
- 生成 Operating Kit 文档（generate_operating_kit_doc）

**限制**：
- 输出必须经过 sanitize：不暴露 API key、绝对路径、原始 prompt、用户名
- 不修改任何系统状态

---

### 2.3 `approval_required` — 需审批写入

修改系统状态的动作，必须经过 Founder 审批或明确授权。

**示例**：
- 创建 Work Order（create_work_order）
- 批准派发（approve_dispatch）
- 执行 Work Order（execute_work_order）
- 代码变更应用（code_change_apply）
- 外部 Agent 执行（external_agent_execution）

**审批模型**：
- 当前：Founder 在 Review 阶段人工确认
- 未来：可扩展为 Capability Registry 中的 `approval_required` 字段

---

### 2.4 `elevated_write` — 提升写入

直接影响系统配置或基础设施的动作。仅限明确授权的 actor（如系统管理员或 Founder 本人）。

**示例**：
- 写仓库代码（write_to_repo）
- 更新系统配置（update_config）
- 修改预算策略（modify_budget_policy）
- 修改能力注册表（modify_capability_registry）
- 修改运行时清单（modify_runtime_manifest）

**限制**：
- 需要确认已记录到 Run Ledger
- 建议在 v0.28+ 中加入二次确认

---

### 2.5 `forbidden` — 禁止

直接禁止的动作。任何 actor 在任何模式下都不能执行。如果尝试执行，系统应该拒绝并记录告警。

**示例**：
- 未审批删除资产（delete_assets_without_approval）
- 暴露敏感数据（expose_sensitive_data）
- 发布内部日志（publish_internal_logs）
- 自动批准执行（auto_approve_execution）
- 绕过 Founder 审批（bypass_founder_review）
- 覆盖/篡改 Run Ledger 事件（overwrite_run_ledger_events）

**处理**：
- `--mode enforce` 下：直接拒绝，返回非零 exit code
- `--mode advisory` 下：输出告警但继续执行（用于测试和迁移期）

---

## 3. 动作分类速查表

| 类别 | 默认策略 | 需审批 | 可绕过 | 代表动作 |
|:-----|:---------|:-------|:-------|:---------|
| `read_only` | ✅ 允许 | ❌ | N/A | status_query, asset_query |
| `safe_output` | ✅ 允许 | ❌ | ❌ sanitize 必过 | generate_ceo_brief |
| `approval_required` | 🔒 拒绝 | ✅ | ❌ | create_work_order, approve_dispatch |
| `elevated_write` | 🔒 拒绝 | ✅ + 记录 | ❌ | write_to_repo, update_config |
| `forbidden` | 🚫 直接拒绝 | N/A | N/A | expose_sensitive_data |

---

## 4. Actor 映射（当前）

每个已知 actor 与其允许的动作集映射，记录在 `config/capability-boundary.yaml`。

| Actor | 允许类别 | 备注 |
|:------|:---------|:------|
| `hermes-main` | read_only, safe_output | 默认 Agent，不强写权限 |
| `ceo-cmd-interface` | read_only, safe_output, approval_required | CEO CLI，需审批才能写入 |
| `openclaw-worker` | read_only, safe_output, approval_required | 执行 Worker，需审批 |
| `daily-operating-loop` | safe_output | 自动化，只产出 Brief |
| `founder-console-api` | read_only, safe_output, approval_required | API 层，受 Founder 审批控制 |
| `system-admin` | read_only, safe_output, approval_required, elevated_write | 受信 actor |

---

## 5. 与 Capability Registry 的关系

| 概念 | Capability Registry | Capability Boundary |
|:-----|:--------------------|:---------------------|
| 定义 | 某个 actor **能做什么** | 某个动作 **属于什么类别、需要什么审批** |
| 粒度 | 按 skill / task_type | 按动作类别（5 类） |
| 控制点 | routing | 执行前检查 |
| 来源 | `skill_registry.yaml` | `capability-boundary.yaml` |
| 边界 | 任务路由 | 安全规则层 |

两者互补：Capability Registry 决定路由，Capability Boundary 决定是否允许执行。

---

## 6. 当前限制

- Advisory mode 下只告警不阻断（v0.27 默认）
- 无运行时自动拦截中间件（需手动调用 `capability_boundary.py check`）
- Actor 列表当前硬编码，未来应来自 Capability / Runtime Manifest
- 无 UI 配置页面，需编辑 YAML

---

## 7. 未来路线

| 版本 | 目标 |
|:-----|:------|
| v0.28 | 自动拦截中间件 + Actor 来自 Runtime Manifest |
| v0.29 | 策略可视化（Founder Console 展示当前边界状态） |
| v0.30 | 动态边界（按时间 / 预算 / 风险级别微调） |
