# AI Company OS — Capability Registry

> **能力地图：Agent → Capability → Project 的映射。**
> 不是 OpenClaw Skills 安装机制，而是 AI Company OS 的业务层能力索引。
>
> 机器可读版本：`config/capability-registry.yaml`
> 技术 Skills 注册：`backend/config/skill_registry.yaml`

---

## 总览

```
Layer 1: Founder-facing Chief of Staff
  └─ hermes-main — 战略讨论 / 产品规划 / 开发 / 调度

Layer 2: System-facing CEO Command Interface
  └─ ceo-cmd-interface — 查询状态 / 资产 / 能力 / 生成 Draft

Layer 3: Specialist Executors
  ├─ research-agent  (OpenClaw) — 研究与信息合成
  ├─ finance-analyst (OpenClaw) — 财务与成本分析
  ├─ amazon-seller   (OpenClaw) — 电商运营分析
  ├─ content-manager (OpenClaw) — 内容生产
  └─ codex           (Codex)    — 代码开发

Layer 4: Runtime & Platform
  └─ openclaw-gateway / openclaw-worker — 模型网关与任务执行
```

---

## 各 Agent 详情

### Layer 1 — hermes-main

| 字段 | 值 |
|------|-----|
| **Agent ID** | `hermes-main` |
| **角色** | Founder-facing Chief of Staff |
| **Runtime** | Hermes |
| **风险等级** | Critical |
| **成本等级** | Moderate |
| **质量等级** | Premium |

**能力：**
- 开放式战略讨论与判断
- 产品架构规划
- 研发协调与子 Agent 调度
- 代码开发
- 临时问题处理
- PRD / Plan / 路线图编写

**边界：**
- ❌ 不能绕过 Founder 批准执行 OS 操作
- ❌ 不能自动派发 Work Orders
- ❌ 不能自动批准 OS 动作
- ❌ 不能未经 Founder 审查修改治理内核

**需要批准的動作：**
- `create_work_order` — 创建 Work Order
- `approve_dispatch` — 批准派发
- `execute_work_order` — 执行 Work Order
- `modify_governance_kernel` — 修改治理内核

---

### Layer 2 — ceo-cmd-interface

| 字段 | 值 |
|------|-----|
| **Agent ID** | `ceo-cmd-interface` |
| **角色** | System-facing CEO Command Interface |
| **Runtime** | System（内建） |
| **风险等级** | Low |
| **成本等级** | Cheap |
| **质量等级** | Standard |

**能力：**
- `status_query` — 查询系统状态（Run Ledger + WO + Decisions）
- `asset_query` — 查询最近资产
- `lineage_query` — 查询资产来源链
- `capability_lookup` — 查询能力地图
- `draft_from_decision` — 基于 Decision 生成 Work Order Draft
- `draft_from_asset` — 基于 Asset 生成 follow-up Draft
- `ceo_action_logging` — 所有操作写入审计日志

**边界：**
- ❌ 不能直接创建 Work Order
- ❌ 不能 approve-dispatch
- ❌ 不能 execute Work Orders
- ❌ 不能自动批准
- ❌ 不能绕过 Founder

---

### Layer 3 — Specialist Agents

#### research-agent

| 字段 | 值 |
|------|-----|
| **Runtime** | OpenClaw |
| **Skills** | `research_summary`, `opportunity_scan` |
| **风险等级** | Low |
| **成本等级** | Moderate |

**能力：** 网络研究 / 信息合成 / 报告生成 / 机会扫描 / 竞品分析 / 趋势监测

**边界：** 不能执行沙箱外文件操作 / 不能部署 / 不能接触财务数据

#### finance-analyst

| 字段 | 值 |
|------|-----|
| **Runtime** | OpenClaw |
| **Skills** | `finance_analysis` |
| **风险等级** | Low |
| **成本等级** | Cheap |

**能力：** 成本分析 / 预算追踪 / 财务报表 / Token 用量分析 / 开支模式分析

**边界：** 不能修改预算策略 / 不能批准支出 / 不能访问外部金融账户

#### amazon-seller

| 字段 | 值 |
|------|-----|
| **Runtime** | OpenClaw |
| **Skills** | `amazon_seller_analysis` |
| **风险等级** | Medium |
| **成本等级** | Moderate |

**能力：** 亚马逊市场分析 / 产品研究 / Listings 优化分析 / 竞品跟踪 / 销售数据分析

**边界：** 不能直接修改卖家账户 / 不能执行订单 / 不能访问敏感 API 凭据

#### content-manager

| 字段 | 值 |
|------|-----|
| **Runtime** | OpenClaw |
| **风险等级** | Low |
| **成本等级** | Cheap |

**能力：** 文章写作 / 内容规划 / 格式转换 / 多语言内容 / 质量检查

**边界：** 不能自动发布到外部平台 / 战略性内容需 Founder 审查

#### codex

| 字段 | 值 |
|------|-----|
| **Runtime** | Codex CLI |
| **Skills** | `code_change` |
| **协议** | ACP (Agent Communication Protocol) |
| **风险等级** | High |
| **成本等级** | Expensive |
| **质量等级** | Premium |

**能力：** 代码生成 / 代码审查 / 重构 / 功能开发 / 测试编写 / Bug 修复

**边界：** 不能部署到生产 / 不能访问生产数据库 / 不能修改安全敏感文件 / 仅限 Staging 工作区

**需要批准的動作：** Generate Plan / Apply Patch / 生产检查 / 提交主分支

---

### Layer 4 — Runtime & Platform

#### openclaw-gateway

| 字段 | 值 |
|------|-----|
| **Runtime** | OpenClaw |
| **风险等级** | Critical |
| **成本等级** | Expensive |

**能力：** 模型路由 / 成本追踪 / Fallback 处理 / 警告生成 / 任务执行 / Agent 生命周期管理

**边界：** 不做战略决策 / 不批准动作 / 仅执行分配的 Work Orders

#### openclaw-worker

| 字段 | 值 |
|------|-----|
| **Runtime** | OpenClaw |
| **风险等级** | Medium |
| **成本等级** | Moderate |

**能力：** Inbox 任务处理 / 结果回调 / 产物生产 / 进度上报

**边界：** 仅跟随 OpenClaw Gateway 调度 / 无自主决策

---

## 能力与 Workflow 映射

| 能力 | 所属 Agent | 关联 Workflow | 关联项目 |
|------|-----------|--------------|---------|
| status_query | ceo-cmd-interface | ceo_query | ai-company-os |
| asset_query | ceo-cmd-interface | ceo_query | ai-company-os |
| lineage_query | ceo-cmd-interface | ceo_query | ai-company-os |
| draft_action | ceo-cmd-interface | decision_to_draft | ai-company-os |
| web_research | research-agent | daily_system_health_brief, research_to_opportunity | ai-company-os, ai-knowledge-os |
| cost_analysis | finance-analyst | cost_analysis, budget_reporting | ai-company-os, ai-business-os |
| amazon_market_analysis | amazon-seller | amazon_seller_analysis, market_opportunity_scouting | ai-business-os |
| content_production | content-manager | content_production, content_calendar_management | ai-knowledge-os |
| code_generation | codex | code_change, feature_development, bug_fix | ai-company-os, ai-knowledge-os, ai-business-os |
| model_routing | openclaw-gateway | all | all |
| task_execution | openclaw-gateway | all | all |

---

## 缺口与补齐策略

| 能力缺口 | 当前状态 | 补齐方案 |
|---------|---------|---------|
| 外部 Runtime Plugin SDK | ❌ 未开始 | v0.28 Runtime Manifest |
| Capability Boundary (read/safe/elevated/approval) | ❌ 未开始 | v0.27 Capability Boundary |
| Workflow Composition (WO depends_on) | ❌ 未开始 | v0.29 Workflow Composition |
| Agent Meeting | ❌ 已删除 | 替换为 v0.29 Workflow Composition |
| Smart Routing (cost/quality routing) | ❌ 未开始 | 预留字段已注册 |

---

> **维护者**：Hermes / Founder
> **更新频率**：每次新增 Agent / Runtime / Capability 时更新
