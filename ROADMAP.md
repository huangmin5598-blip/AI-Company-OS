# AI Company OS — 路线图

> 最后更新：2026-05-31（v0.34 已发布 🏁）
> 定位：AI Company OS 是一个 **AI Agent Native Company Operating System**。
> 主线：**7 层公司闭环**——从机会发现到产品、增长、销售、客户反馈、组织学习，每条真实产品线必须跑通端到端闭环才算验证通过。
> 所有 Connector / UI / Cron / 第三方竞品对标 都只能作为增强项，不能偏离主线。
> 五层架构：Execution Spine / Governance Kernel / Memory & Asset Layer / Founder Control Plane / Productization & Evidence

---

## 7 层公司闭环（主线全景）

| # | Loop | 功能 | 状态 |
|:--|:-----|:-----|:-----|
| 1 | **Opportunity Discovery** | 信号发现 → 富化 → Candidate → 评估 | 🟢 v0.31–v0.34 |
| 2 | **Opportunity Operating** | 发现变成每周经营动作 | 🔴 v0.35 | 
| 3 | **Growth & Content** | 从产品/机会生成内容、销售页、冷启动 | 🔴 v0.36 |
| 4 | **GTM / Sales** | 定价、线索、付费验证、交付 | 🔴 v0.37 |
| 5 | **Customer Feedback** | 反馈收集、需求分类、产品迭代 | 🔴 v0.38 |
| 6 | **Company Learning** | 全线数据回流到 Context / Skill / Policy / Strategy | 🔴 v0.39 |
| 7 | **Founder Console 2.0** | 7 层闭环可视化控制面 | 🔴 v0.40 |

横向内核：Governance / Runtime / Skill Registry / Policy / Ledger / Asset Registry

### v1.0 证伪/证实标准

**至少一条真实产品线跑通从机会→产品→增长→销售→反馈→学习的端到端闭环。** 在此之前不追求 Connector 数量、UI 美观度、第三方对标。

---

## 里程碑总览

```
v0.02 ─ v0.14  基础框架 ── Loop / CEO Agent / Memory / Runtime / Bridge    🏁
v0.15 ─ v0.23  治理 + 决策到执行闭环 ── Governance / Ledger / Asset       🏁
v0.24 ─ v0.30  系统级能力 ── Console / Evidence / Operating Kit / Workflow 🏁
v0.31 ─ v0.34  机会发现层 ── Opportunity Engine / Connectors / Enrichment   🏁
v0.35              机会评估方法论升级（内部开发，核心商业资产）                   🔒
v0.36 ─ v0.40  7 层公司闭环全建设                                      🏗️
v1.0+           端到端闭环验证 + 产品化                                    🔮
```

---

## 已完成

### v0.02 — Company Loop MVP
- 基础公司循环机制

### v0.03 — CEO Agent Lite
- CEO Agent 原型

### v0.04 — Company Memory MVP
- 公司记忆系统

### v0.05 — Monitor Framework Lite
- 监控框架轻量版

### v0.06 — Runtime Layer MVP
- Runtime 层概念验证

### v0.07 — Controlled Self-Improvement Proposal MVP
- 受控自我改进提案

### v0.08 — Controlled Execution Bridge MVP
- 受控执行桥

### v0.09 — Code-Capable Runtime Bridge MVP
- 代码能力 Runtime 桥

### v0.09.2 — External Runtime Connector MVP
- 外部 Runtime 连接器

### v0.10 — Work Delegation Layer MVP
- Work Order 创建/路由/执行闭环
- Execution Mode 矩阵
- Skill Router 概念验证

### v0.13 — OpenClaw Bridge Callback MVP
- OpenClawBridge 对接 OpenClaw 外部 Agent
- Inbox/Outbox 协议
- Task Card 生成
- Callback API (POST /openclaw-callback)
- 幂等 / force 覆盖 / API Key 校验

### v0.14 — Bridge Reference Worker
- 参考 Worker 实现 (bin/openclaw_worker.py)
- inbox → working → result.json 闭环
- LocalLLMExecutor 本地执行 (Ollama / deepseek-r1:8b)
- EchoExecutor 规则快速路径
- **叙事修正前**：错误地称为"OpenClaw 原生执行"

### v0.14.1 — OpenClaw Native Executor Integration
- **叙事修正**：v0.14 是 Reference Worker，v0.14.1 才是 OpenClaw 原生执行
- Executor 抽象接口 (base.py / factory.py)
- OpenClawAgentExecutor：调用 `openclaw agent --json`
- Agent 映射：research-agent / finance-analyst / amazon-seller / content-manager / main
- Feature Flag：`OPENCLAW_EXECUTOR_MODE = auto | openclaw_native | local_llm | echo`
- Result Manifest 完整 Provenance：executor_type / model_name / token_usage / duration_ms / openclaw_run_id

### v0.14.2 — OpenClaw Native Executor Hardening ✅ (当前)
- **E2E 测试拆分**：主套件 80/80 + Callback API Contract Test 21/21
- **Result Manifest 工具证据字段**：tool_calls_detected / inferred_tools / tool_call_summary / tool_call_evidence_source / tool_trace_available
- **extract_inferred_tools()**：从 Agent 输出文本推断工具调用
- **Evidence 文档**：docs/evidence/openclaw-native-agent-tool-execution-v0.14.2.md
- **诚实记录限制**：CLI 无 tool trace / session 未复用 / 文本推断

---

## 下一阶段：治理 + 自动化 (v0.15 ~ v0.18)

### v0.15 — Skill Registry & Routing Contract Lite ✅ (已完成)

**版本**：v0.15 · 2026-05-30

**目标**：让 AI Company OS 知道"该让谁干什么活"

**交付**：
1. **Skill Registry YAML** (`backend/config/skill_registry.yaml`)
   - 5 skills: research_summary / finance_analysis / amazon_seller_analysis / opportunity_scan / code_change
   - 每个 skill 含 skill_id / description / task_types / default_agent / runtime / executor / risk_level / approval_required / output_schema / allowed_tools / budget_class
2. **Skill Registry Loader** (`backend/app/services/skill_registry.py`)
   - YAML 加载 + 校验 + 缓存 + fail-fast
   - `get_contract(task_type) → RoutingContract` 查询接口
   - `extract_inferred_tools()` 工具推断函数
3. **Router 改造** (`backend/app/services/skill_router.py`)
   - 从硬编码 dict + DB 表 → YAML-backed
   - 输出兼容旧字段名 (owner_agent / runtime_id / execution_mode)
4. **WO 路由元数据**
   - route handler 记录 assigned_agent / approval_required / routing_reason
   - task card 包含 skill_id / selected_agent / routing_reason
   - result.json 包含 skill_id / selected_agent / routing_reason
5. **未知 task_type** → **needs_review**（非 blocked）
6. **17 task_types 映射**（含兼容旧值）
7. **测试**：60/60 Skill Registry + 80/80 E2E + 21/21 Callback API

**不做**：Paperclip / Heartbeat / Budget / Cron / 大 UI / Agent Meeting / Skill Marketplace / 自动高风险任务

### v0.16 — Runtime Governance Lite ✅ (已完成)

**版本**：v0.16 · 2026-05-30

**目标**：在 v0.17 Operating Loop 自动运行前，给 AI Company OS 加最小安全网。

**交付**：
1. **Runtime Health Check** (`backend/app/services/runtime_health.py`)
   - 按需检查 OpenClaw CLI / Codex CLI / Ollama API 可用性
   - 返回 healthy / degraded / unhealthy
   - 不做常驻 daemon
2. **Failure Policy** (`backend/app/services/failure_policy.py`)
   - unknown_task_type → needs_review
   - runtime_unhealthy → needs_review
   - executor_timeout → retry (低风险) / needs_review (中高风险)
   - 连续失败 2 次 → escalation_required
3. **Cost Summary** (`backend/app/services/cost_summary.py`)
   - 扫描 artifacts/ 中所有 result.json
   - 按 work_order / agent / runtime / skill 汇总 token
   - estimated_cost（非 actual billing）
   - Markdown 报告生成
4. **Soft Budget Guard** (`backend/config/budget_policy.yaml`)
   - 每个 skill 的 token 阈值
   - action: warn / needs_review（不做硬 kill）
   - YAML 缺失时使用默认值
5. **API 端点**
   - GET /api/v1/governance/health
   - GET /api/v1/governance/cost-summary
   - GET /api/v1/governance/cost-report
   - POST /api/v1/governance/budget-check
6. **测试**：29/29 Governance + 80/80 E2E + 21/21 Callback + 60/60 Skill Registry

### v0.17 — Daily Operating Loop MVP ✅ (已完成)

**版本**：v0.17 · 2026-05-30

**目标**：验证 Operating Loop 机制——系统能从 scheduled_work_orders.yaml 读取配置，按 cadence 创建并执行 Work Order，生成 CEO Brief。

**范围（收窄版）**：只配 1 个任务（daily-system-health-brief），手动 `--once` 模式，不下 launchd。

**交付**：
1. **Scheduler** (`backend/app/services/scheduler.py`)
   - 从 YAML 加载 scheduled_work_orders（daily/weekly/monthly cadence）
   - 到期判断 + 防重复创建（同一天同 scheduled_id 只跑一次，除非 --force）
   - ScheduledWorkOrder 数据类
2. **CEO Brief** (`backend/app/services/ceo_brief.py`)
   - 8 段式 Markdown 生成器：运行摘要 / Runtime Health / Work Orders / Cost / Budget & Failure Warnings / 重要发现 / Founder 决策 / 下一步建议
   - 自动收集 Health Check、Cost Summary、Budget Guard 数据
   - 自动推断 Founder 决策事项（unhealthy runtime、failed WO、needs_review、budget overflow）
3. **run_operating_loop.py** CLI
   - `--dry-run`：预览任务、Health、Cost，不执行
   - `--once`：完整执行——读 YAML → 到期判断 → 去重 → Health Check → Budget Guard → 创建 Work Order → OpenClaw 派单 → Failure Policy → CEO Brief
   - `--force`：跳过同天去重
   - `--scan-pending`：预留（默认 False，v0.17 不扫 pending）
4. **配置**：`backend/config/scheduled_work_orders.yaml` · 1 个任务
5. **测试**：190/190 通过（29 governance + 60 skill_registry + 21 callback + 80 e2e）

**不做**：launchd / crontab / 3+ scheduled tasks / 扫 pending / Web UI / Paperclip / 自动批准

**明确边界**：
- `--dry-run`：不创建任何 Work Order，但输出完整的 CEO Brief（含 DRY-RUN 标记）
- 防重复：基于 route_reason 的前缀匹配 "scheduled:{id}:YYYY-MM-DD"
- 执行前必做 Health Check，unhealthy 时跳过执行

### v0.18 — CEO Brief Review & Decision Layer Lite ✅ (已完成)

**版本**：v0.18-0.18.3 · 2026-05-30

**目标**：让 Founder 能 Review Brief → 做 Decision → 生成 Work Order Draft，完成 CEO 决策闭环前 3 步（不涉及 WO 执行）。

**交付**：
1. **`scripts/review_brief.py`** — 纯 Markdown 规则解析，零 LLM
   - `index` — 扫描 `reports/ceo-briefs/` 生成 INDEX.md
   - `review <brief>` — 提取 Decision Items + 生成 Review 模板
   - `decide <review>` — 读取勾选的决策 → 写入 DECISION-LOG.md（去重 + 冲突检测）
   - `create-work-order <draft>` — 校验 Draft 必填字段 → 生成预览
   - `status` — 所有 Brief 概览面板
2. **Draft 生成** — decide 中 `create_work_order_later` → 自动生成 WO-DRAFT 文件
3. **三方去重** — 同 Brief + 同 ID + 同 Decision 任一匹配则跳过
4. **冲突检测** — 一个 Decision Item 勾了多个选项 → 标记 invalid_review

**不做**：LLM / API 调用 / WO 创建 / 自动执行

### v0.19 — Work Order Draft to API Integration ✅ (已完成)

**版本**：v0.19-0.19.1 · 2026-05-30

**目标**：打通 Draft → 真实 Work Order API 调用。

**交付**：
1. **create-work-order 升级** — 从 preview-only → 真实 `POST /api/v1/work-orders`
2. **Draft Footer** — WO 创建后回写 `work_order_id` / `status`
3. **Draft INDEX** — 更新状态 + WO ID 列
4. **去重防护** — 已创建 WO 的 Draft 不可重复创建
5. **必填校验** — task_type / proposed_prompt / expected_output 缺一不可

### v0.20 — Work Order Route & Approval Gate ✅ (已完成)

**版本**：v0.20 · 2026-05-30

**目标**：Work Order 从 created → 可 approve-dispatch。

**交付**：
1. **`POST /work-orders` API** — 接收 `source_brief` / `source_decision` / `source_draft` / `approval_required` 元数据
2. **WO 状态机** — `created`（非 `draft`）不自动 route/dispatch
3. **`scripts/work_order_control.py approve-dispatch <WO_ID>`**
   - 校验 status=created & approval_required=true
   - 写入 `approved_for_dispatch_at` + `approval_id`
   - 拒绝 6 种非法状态
4. **测试**：190/190 通过

### v0.21 — Work Order Route & Execute Gate ✅ (已完成)

**版本**：v0.21 · 2026-05-30

**目标**：approve-dispatch → `/route` → `/execute` 全链路。

**交付**：
1. **approve-dispatch 升级** — 批准后依次调用 `POST /route` → `POST /execute`
2. **route 端点** — `POST /work-orders/{id}/route` 填充 skill_id / runtime / risk 等
3. **execute 端点** — `POST /work-orders/{id}/execute` 状态迁移
4. **`approved_for_dispatch_at` 字段** — DB migration + 幂等写入
5. **测试**：21 approve-dispatch 测试通过

### v0.22 — Work Order Executor Integration ✅ (已完成)

**版本**：v0.22 · 2026-05-30

**目标**：`POST /execute` 真正调用 `WorkOrderExecutor`，WO 从 routed → executed。

**交付**：
1. **`POST /{id}/execute` 重写** — 调用 `WorkOrderExecutor.execute_work_order(wo_id)`
2. **同步模式** — `direct_delegate` / `local_script` 立即完成
3. **异步模式** — `openclaw_agent` 写入 inbox task card，status=in_progress
4. **幂等保护** — status!=routed 时拒绝二次执行
5. **`wait-result <WO_ID>`** — 轮询至 completed/failed/cancelled
6. **openclaw_agent handler 别名映射** — 修复 `research-agent` 等映射
7. **全链路实测** — WO-B565EE14 28s, WO-15D55075 15s

### v0.22.1 — Decision-to-Execution Result Backfill ✅ (已完成)

**版本**：v0.22.1 · 2026-05-30

**目标**：WO completed 后，把执行结果回写到 source Draft + INDEX + DECISION-LOG。

**交付**：
1. **`wait-result --sync-source <WO_ID>`** — WO completed 后三重回写
   - Draft Footer 追加 `## Execution Result`（幂等）
   - Draft INDEX.md 更新为 completed
   - DECISION-LOG.md 追加 Execution Completed 行
2. **Source Metadata 保留** — route 端点不再覆盖 `routing_log_json` 中的 source 字段
3. **幂等** — 重复 `--sync-source` 不重复写入

### v0.23 — Run Ledger MVP + Asset Registry MVP ✅ (已完成)

**版本**：v0.23 · 2026-05-30

**目标**：把 v0.18-v0.22 产生的事件和资产统一记录，让系统知道自己发生了什么、产出了什么。

**交付**：
1. **`RunLedgerEvent` 模型** (`run_ledger_events` 表) — append-only OS 级事件日志
   - 10 种事件类型：brief_generated → review_created → decision_logged → draft_created → work_order_created → approved_for_dispatch → routed → executed → callback_completed → result_synced
   - 分层幂等 key：文件类 `event_type+source_id` / WO 类 `+work_order_id` / Decision 类 `+decision_id`
2. **`AssetRecord` 模型** (`asset_registry` 表) — 6 种资产类型
   - ceo_brief / ceo_brief_review / decision_log_entry / work_order_draft / work_order / execution_result
3. **写入点** — 6 个链路节点追加（`run_operating_loop.py` / `review_brief.py` 3 节点 / `work_order_control.py` 2 节点）
4. **`scripts/os_registry.py`** CLI — `ledger recent` / `assets list` / `lineage <asset_id>`
5. **同 SQLite，不新建数据库** — 1 张 `run_ledger_events` 表 + 1 张 `asset_registry` 表
---
## 下一阶段：系统级能力建设 (v0.24 ~ v1.0)

### v0.24 — CEO Command Interface + Capability Registry P0 ✅ (已完成)

> 2026-05-30

**五层归属**：Founder Control Plane + Governance Kernel

**目标**：给 Hermes / Founder 一个可审计的 OS 操作接口（CEO Command Interface），同时建立能力地图 P0。

**Sprint A — Capability Registry P0**
- `docs/registry/CAPABILITY-REGISTRY.md` + 可选 `config/capability-registry.yaml`
- 记录：agent_id / role / runtime / capabilities / boundaries / supported_workflows / risk_level / cost_class / approval_required_actions
- 至少登记 5 个 agent/runtime：research-agent / finance-analyst / amazon-seller / codex / ceo-cmd-interface / openclaw_agent
- 明确区分 `hermes-main`（Founder-facing Chief of Staff）和 `ceo-cmd-interface`（System-facing 操作接口）

**Sprint B — CEO Command Interface**
- `scripts/ceo_cmd.py` — status / assets / lineage / draft-from-decision / draft-from-asset
- 数据源：Run Ledger / Asset Registry / Work Orders / CEO Brief / Decision Log / Capability Registry
- 所有动作写入 Run Ledger 或 ceo_action_log

**边界**：
- ✅ 查询系统状态 / 查询资产 / 查询 lineage / 查询能力地图 / 生成 Draft
- ❌ 不能 create Work Order / 不能 approve-dispatch / 不能 execute
- ❌ 不能自动审批 / 不能绕过 Founder / 不能自动批量派工

**不做**：自动执行 / 自动审批 / 复杂目标拆解 / Agent Meeting / Web UI / 向量搜索 / launchd 改动 / worker 改动 / WO 主链路改动

---

### v0.25 — Founder Control Plane — 5-Tab IA + Founder Console + Preflight 11/11 ✅ (已完成)

> 2026-05-30

**五层归属**：Founder Control Plane + Governance Kernel

**目标**：一眼看清系统状态，同时具备基础自检能力。

**交付**：
1. **Thin Console CLI** — `scripts/founder_console.py {status,health,decisions,assets}`
   - 复用 Run Ledger / Asset Registry / Work Orders / CEO Brief / Runtime Health
   - 不新建数据源，不重写查询链路
2. **Preflight Checks** — Console 的 health section
   - 检查：DB path / launchd / OpenClaw / Codex / Ollama / Run Ledger writable / Asset Registry writable / reports path writable / budget config valid
3. **输出格式**：Markdown 摘要，不做 Web UI

**不做**：重 GUI / 复杂交互 / 多租户 / 实时系统 / 大而全后台

---

### v0.26 — Evidence Dashboard Lite + GitHub Refresh 🏗️ (进行中)

> 2026-05-30

**五层归属**：Productization & Evidence

**目标**：对外展示系统在运行、资产在增长、机制在工作。

**交付**：
1. **Evidence Dashboard Lite**（纯 HTML / Markdown）
   - 输入：Run Ledger / Asset Registry / CEO Brief / Decision Log / Work Orders / Cost Summary
   - 展示：Run Flow / Asset Growth / Agent Status / Decision-to-Execution Evidence / Gateway Summary
2. **GitHub 刷新**
   - README 更新
   - Release note 同步
   - 证据页面输出到 `docs/evidence/`

**不做**：重交互产品 / 复杂实时系统 / 多租户 / 独立站搭建

---

### v0.27 — Operating Kit v0.1 + Capability Boundary 🔮 (计划中)

**五层归属**：Governance Kernel + Productization & Evidence

**目标**：把跑通的流程整理成可复用的 Operating Kit，同时引入安全边界体系。

**交付**：
1. **Operating Kit v0.1**
   - Decision-to-Execution Kit / Daily Operating Loop Kit / CEO Brief Review Template / Work Order Template
2. **Capability Boundary**
   - 正式引入等级制：`read_capabilities` / `safe_outputs` / `elevated_write_actions` / `approval_required_actions`
   - 对应借鉴：GitHub Agentic Workflows "默认只读 + Safe Outputs"、v0.8/v0.9 安全原则统一抽象

**不做**：商业打包 / 完整安全系统 / 多租户权限

---

### v0.28 — Company Instance Config + Runtime / Capability Manifest 🏁 (已完成)

**五层归属**：Productization & Evidence + Governance Kernel

**目标**：OS Core 与个人配置分离，Runtime/Capability Manifest 正式化。

**交付**：
1. **Company Instance Config**
   - `company-instance.example.yaml` — 实例配置模板
   - `docs/configuration/COMPANY-INSTANCE-CONFIG.md` — Core vs Instance 边界文档
   - `.gitignore` 添加真实实例配置文件
2. **Runtime Manifest**
   - `config/runtime-manifest.yaml` — 4 个运行时声明
3. **Capability Manifest**
   - `config/capability-manifest.yaml` — 10 个 actor 声明
   - `capability_boundary.py` 可选合并读取（不强依赖）
4. **Safe Output Policy**
   - `config/safe-output-policy.yaml` — 8 种输出类型 + 4 条脱敏规则
5. **Manifest Validator**
   - `scripts/manifest_validator.py` — 11 项检查
6. **CAPABILITY-REGISTRY-TEMPLATE**（v0.27 延迟）

**不做**：多租户 / 云部署 / 计费 / 模板市场

---

### v0.29 — Manifest-Governed Execution Lite 🏁 (已完成)

**五层归属**：Governance Kernel

**目标**：让 v0.27 的 Capability Boundary 和 v0.28 的 Manifest 真正参与执行前判断。

**交付**：
1. ✅ **Policy Resolver** (`scripts/policy_resolver.py`)
   - 合并读取 boundary / runtime / capability / safe-output policy
   - 输出：allowed / boundary_class / requires_approval / safe_output_required
   - CLI `resolve`（无 ledger） + `check`（带 ledger 记录）子命令
   - 双模式：advisory（默认） / enforce（forbidden hard block exit 1）
2. ✅ **接入 3 个关键入口**
   - `ceo_cmd.py` — draft_from_decision / draft_from_asset 检查策略
   - `review_brief.py` — Work Order 创建检查策略
   - `work_order_control.py` — approve-dispatch 检查策略
3. ✅ **Safe Output Check** — 扫描文本中的本地路径、API Key、环境变量
4. ✅ **Policy Decision 写入 Run Ledger**
   - policy_checked / policy_allowed / policy_blocked / safe_output_validated
5. ✅ **Hygiene**
   - config/launchd/ 加入 .gitignore（保护本地路径）
   - manifest_validator 11/11 passed
   - 所有已有测试通过

**不做**：Workflow Composition / 多租户 / Web UI 大改 / 插件系统 / Paperclip / MCP / A2A / 云部署

---

### v0.30 — Workflow Composition Lite with Asset Handoff 🏁 (已完成)

**五层归属**：Execution Spine

**目标**：把多个 Work Order 通过显式依赖关系和资产交接串成轻量 workflow；每一步仍然保留 Founder approval、Policy Resolver 和现有 Work Order 生命周期。

**交付**：
1. **Workflow Schema + Asset Handoff**
   - metadata_json 扩展：workflow_id / step_id / depends_on / outputs / consumes_asset
   - 每个 step 声明 outputs（asset_type），后续 step 声明 consumes_asset
   - 不做 DB 迁移，全部走 metadata_json
2. **2 个 Workflow Template**
   - `decision_followup_workflow` — Decision → Draft → WO → Execute
   - `opportunity_followup_workflow` — 已有机会信号 → Research → Validation → Execute
   - 不做文章摄入/OCR/反爬模板
3. **Workflow Runner CLI** (`scripts/workflow_runner.py`)
   - `create` — 读取模板 + 生成 workflow record + Step 1 Draft
   - `status` — 显示各 step 进度
   - `next` — 检查依赖 + 读前置 asset + 注入 context + 生成下一步 Draft
   - `resolve` / `skip` / `cancel` — 阻塞处理
4. **Run Ledger / Asset Registry / Policy 接入**
   - 9 类 workflow 事件类型（created / step_created / step_completed / unlocked / blocked / block_resolved / skipped / cancelled / completed）
   - 3 种 asset type（workflow_plan / workflow_step_context / workflow_step_output）
   - Policy Resolver 在 create / next / approve-dispatch 保持生效

**不做**：Agent Meeting / 自由 multi-agent mesh / 拖拽 DAG / 复杂 workflow engine / 自动 approve / 自动 execute 全流程 / 并行 workflow / 条件分支 / 文章抓取 / OCR / 外部内容摄入 / Web UI 大改 / Paperclip / MCP / A2A

---

### v0.30.1 — Private Instance Data Cleanup 🏁 (已完成)

**五层归属**：Governance + Infrastructure

**目标**：从公开仓库历史中移除私有实例研究数据，强化可复用 OS 模块与公司实例数据之间的边界。

**交付**：
1. Git 历史重写：`git filter-repo --path research/ --invert-paths`，191 commits 清理
2. 重建 26 个 tag + 25 个 GitHub Release
3. 三层 Git 边界永久生效（AI-Knowledge-OS / research/ / OS Module）
4. Release skill 升级 v2.0：历史交叉检查 + 中性叙事规则

---

### v0.31 — Opportunity Module Lite 🏁 (已完成)

**五层归属**：Founder Control Plane + Execution Spine

**目标**：把「机会」从个人 markdown 文件升级为 OS 原生对象。

**交付**：
1. **三层数据边界**：`docs/opportunity/OPPORTUNITY-DATA-BOUNDARY.md`
2. **3 种资产类型**：opportunity_signal / opportunity_card / opportunity_decision
3. **6 个 Run Ledger 事件**：signal_created / card_created / approved / parked / rejected / workflow_created
4. **Opportunity CLI**：`scripts/opportunity.py` + `ceo_cmd.py opportunity` 集成
5. **Workflow Bridge**：approve → 自动创建 opportunity_followup_workflow
6. **示例配置**：opportunity.example.yaml（真实配置被 .gitignore 保护）

**不做**：文章抓取 / OCR / 反爬 / 主动扫描 / 评分模型 / 自动执行 / 公开真实机会数据

---

### v0.32 — Opportunity Discovery Engine Lite 🏁 (已发布 🏁)

**五层归属**：Founder Control Plane（机会发现层）

**定位**：AI Company OS 作为创业发动机，持续发现可生出产品实例的创业机会。

**目标**：把机会发现方法论工程化——从 5 类信号源（用户抱怨优先）、5 类机会引擎、10 维评分模型、多产品线映射中，运行规则驱动的机会发现流程。

**3 Sprint 结构**：

| Sprint | 内容 | 关键交付 |
|:-------|:-----|:---------|
| **A** | 大脑完整化 | Candidate Signal Schema / Evidence Gate / Platform Profiles / Product Line Mapping / Skill 更新 |
| **B** | Runner P0 | `opportunity_scout.py` — manual_source_note + internal_asset_scan + source-file 输入 |
| **C** | Founder Review + Fixtures | promote-signal / dismiss-signal / request-card 分流 + 5 golden fixtures + validate 脚本 |

**核心范围**：
- 5 类机会引擎：Cash / Attention / Platform / Content / Knowledge Asset
- 5 类信号源：用户抱怨（第一优先）/ AI 能力 / 市场热点 / 平台生态 / 自身资产
- 10 维评分 + Evidence Gate + Founder Fit
- 8 条产品线映射
- Platform Profile 覆盖 reddit / product_hunt / g2 / app_store / roblox / wechat / zhihu / github / rss / internal_assets

**第一版 Connector**：
- manual_source_note（支持 source-file 输入）
- internal_asset_scan（限 docs/operating-kit, evidence, governance, opportunity, Asset Registry）

**不做**：
- RSS / GitHub search / Product Hunt / Reddit / G2 / App Store / Roblox 正式 connector
- 微信/知乎反爬
- cron / launchd 自动调度
- Web UI
- 自动生成正式 opportunity_card
- 自动 approve / 自动触发 workflow
- 不保存完整原文
| 不做循环扫描 | 否 | — |

---

## 下一阶段：7 层公司闭环 (v0.33 ~ v1.0)

> 主线定位：不再用 Connector / UI / 第三方对标 定义进展。
> 每层闭环的目标是：**该层跑通真实数据流 + Founder 可操作**，不走自动化偏执。

### v0.33 — 信号源层 🏁 (已完成)

**五层归属**：Founder Control Plane（机会发现层）

**目标**：把外部信号接入成结构化 SourceNote，解决"Connector 产出 Candidate"的错误假设。

**交付**：
1. SourceNote Contract — 统一输入格式
2. Search Query Connector — Tavily + DuckDuckGo 双后端
3. GitHub Connector — repo_search / topic_search / release_search
4. Smoke Test — 全管线 mock 验证
5. 关键洞察：SourceNote 天然缺 target_user/pain → 需要 v0.34 Enrichment

### v0.34 — 信号富化与证据审查层 🏁 (已完成)

**五层归属**：Founder Control Plane（机会发现层）

**目标**：把缺 target_user/pain 的 SourceNote 富化成带证据状态的 Enriched Signal，不降低 Evidence Gate。

**4 Sprint 结构**：

| Sprint | 内容 | 交付 |
|:-------|:-----|:-----|
| **A** | Enriched Signal Schema | `ENRICHED-SIGNAL-SCHEMA.md` + JSON Schema |
| **B** | Rule-Based Enricher | `opportunity_enricher.py`（enrich / enrich-batch / review-needed） |
| **C** | Founder Review Patch | `ENRICHMENT-REVIEW-TEMPLATE.md` + generate-review / apply-review / dismiss |
| **D** | Enriched → Candidate 集成 | scout.py `scan-enriched` — reviewed ES → Candidate |

### v0.34.1 — AI Seller Finance 真实信号验证 🏗️ (当前)

**五层归属**：Founder Control Plane

**目标**：跑通第一条真实产品线的端到端信号管线。

**交付**：
1. ⬜ 配 `opportunity-source-queries.yaml`：AI Seller Finance 方向的真实搜索词
2. ⬜ 跑 Search Query → 产出来源 SourceNote
3. ⬜ `enrich-batch` → 产出 Enriched Signal
4. ⬜ Founder 在飞书 review → `apply-review`
5. ⬜ `scan-enriched` → 产出 Candidate
6. ⬜ 验证管线可用性，记录发现

**不做**：新 Connector / 新功能 / 自动化 / 新 UI

---

### v0.35 — Opportunity Evaluation Methodology v2 🔒 (内部私有模块)

**五层归属**：Founder Control Plane（机会评估层）

**状态**：核心商业资产，在私有工作区开发，不进公开仓库。公开仓库仅保留模块名称和定位声明。

**公开可见的信息**：
- 模块名称和定位
- 输入输出边界
- 公开声明文档：[PROPRIETARY-MODULES.md](docs/opportunity/PROPRIETARY-MODULES.md)

---

### v0.36 — Growth & Content Loop 🏗️ (计划中)

**五层归属**：Execution Spine + Founder Control Plane

**目标**：从已确认的产品/机会生成内容、销售页、冷启动材料。

**交付**：
1. 内容生成管线：产品描述 → 博客 / 推文 / 销售页草稿
2. 分发策略模板：每个产品线匹配渠道（GitHub / 知乎 / 小红书 / 公众号）
3. Founder 审核发布
4. 内容效果跟踪（阅读量 / 转化线索）

**不做**：自动发布 / SEO 自动化 / 付费投放

---

### v0.37 — GTM / Sales Loop 🏗️ (计划中)

**五层归属**：Execution Spine + Founder Control Plane

**目标**：记录 Offer、定价、线索、付费验证、交付。

**交付**：
1. Offer Registry — 每个产品线的 Offer 定义（定价 / 价值主张 / 目标用户）
2. Lead Capture — 线索记录（来源 / 跟进状态 / 转化）
3. Payment Verification — 付费验证（收款确认 / 交付触发）
4. Delivery Tracking — 交付完成记录

**不做**：支付网关集成 / CRM 大系统 / 发票自动生成

---

### v0.38 — Customer Feedback Loop 🏗️ (计划中)

**五层归属**：Governance Kernel + Founder Control Plane

**目标**：记录客户反馈、需求分类、驱动产品迭代。

**交付**：
1. Feedback Registry — 每条反馈可追溯来源和上下文
2. 需求分类：bug / feature request / pain / delight
3. 反馈 → 产品线影响评估
4. 反馈 → Opportunity Discovery 回流（发现新信号）

**不做**：NPS 自动调查 / 客服聊天机器人 / 退款工单

---

### v0.39 — Company Learning Loop 🏗️ (计划中)

**五层归属**：Memory & Asset Layer + Governance Kernel

**目标**：把机会、增长、销售、客户反馈和 OS 运行结果回流到 Company Context / Skill / Policy / Product Strategy。

**交付**：
1. Company Context 自动更新 — 从运行数据中发现的模式写回 config
2. Skill 自动调优 — 高频执行的 Workflow → 固化 Skill
3. Policy 进化 — 失败模式和成功模式更新 Policy
4. Product Strategy 更新 — 信号 → 产品线优先级调整

**不做**：完全自动驾驶 / 无 Founder 审批的策略变更

---

### v0.40 — Founder Console 2.0 🏗️ (计划中)

**五层归属**：Founder Control Plane

**目标**：把 7 层闭环做成 Founder 可视化控制面。

**交付**：
1. 各层闭环状态面板（每层的吞吐 / 阻塞 / 待决策）
2. 信号到收入的端到端追溯（一个信号 → 哪个产品 → 多少收入）
3. 每周经营仪表盘
4. 决策压力指示器（哪里需要 Founder 决策却被堵住了）

**不做**：移动端 App / 实时推送 / 复杂图表

---

### v1.0 — 端到端闭环验证 🔮 (计划中)

**五层归属**：全部

**证伪/证实标准**：

> **至少一条真实产品线跑通从机会→产品→增长→销售→反馈→学习的端到端闭环。**

具体指标：
- ✅ 至少 1 条产品线有完整信号 → Candidate → Offer → Sale → Feedback 链条
- ✅ 该产品线的 Founder Console 面板能展示全链条数据
- ✅ 至少 1 次 Company Learning 回流（Context / Skill / Policy 因闭环数据发生可验证的变化）
- ✅ GitHub 公共仓库展示架构 + 方法论（不开源核心引擎）
- ✅ Solo Founder Operating Kit 可售版本可用


## 已删除概念

| 旧概念 | 删除原因 | 替代方案 |
|--------|---------|---------|
| Agent Meeting Session | Workflow-first 优于 Multi-agent Society | v0.29 Workflow Composition（WO depends_on / WO chain） |
| Research-to-Opportunity 独立版本 | 已跑过一轮验证，不需要重复做 | Asset Registry + Weekly OS Review 机制承载 |
| Run Ledger Dashboard Lite | 被 v0.25 Thin Console + v0.26 Evidence Dashboard 吸收 | — |

---

## 五层架构

```
AI Company OS — 五层能力架构

1. Execution Spine（执行脊柱）
   Work Order → Route → Execute → Callback → Result
   关键技术：WorkOrderExecutor / Skill Router / OpenClaw / Codex Adapters

2. Governance Kernel（治理内核）
   Approval / Budget / Failure Policy / Capability Boundary / Safe Outputs
   关键技术：Budget Guard / Failure Policy / Skill Registry / Capability Registry

3. Memory & Asset Layer（记忆资产层）
   Run Ledger / Asset Registry / Company Memory / Lineage
   关键技术：run_ledger_events / asset_registry / CEO Action Log

4. Founder Control Plane（Founder 控制平面）
   CEO Brief / Review / Decision / CEO Command Interface / Thin Console
   关键技术：ceo_brief.py / review_brief.py / ceo_cmd.py / founder_console.py

5. Productization & Evidence Layer（产品化与证据层）
   Evidence Dashboard / Operating Kit / GitHub / 独立站 / 可售包
   关键技术：证据展示层 / Company Instance Config / Runtime Manifest
```

---

## 版本文档索引

| 版本 | PRD | 关键代码 |
|------|-----|---------|
| v0.13 | `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.13-OPENCLAW-BRIDGE-REAL-CALLBACK-PRD.md` | `openclaw_bridge.py`, `openclaw_callback.py` |
| v0.14 | (无独立 PRD，参考 v0.13) | `openclaw_worker/` `executors/` |
| v0.14.1 | (同上) | `executors/openclaw_agent_executor.py`, `base.py`, `factory.py` |
| v0.14.2 | (同上) | `base.py` (tool evidence), `test_callback_api_contract.py` |
| v0.15 | (无独立 PRD) | `skill_registry.yaml`, `skill_router.py`, `skill_registry.py` |
| v0.16 | (无独立 PRD) | `runtime_health.py`, `failure_policy.py`, `cost_summary.py`, `budget_policy.yaml` |
| v0.17 | (无独立 PRD) | `scheduler.py`, `ceo_brief.py`, `run_operating_loop.py`, `scheduled_work_orders.yaml` |
| v0.18 | (无独立 PRD) | `scripts/review_brief.py` |
| v0.19 | (同上) | `scripts/review_brief.py` (create-work-order API 调用) |
| v0.20 | (同上) | `work_order_control.py`, `work_orders.py` (route 端点) |
| v0.21 | (同上) | `work_order_control.py` (approve-dispatch), `work_orders.py` (execute 端点) |
| v0.22 | (同上) | `work_order_executor.py`, `work_order_control.py` (wait-result) |
| v0.22.1 | (同上) | `work_order_control.py` (--sync-source) |
|| v0.23 | (无独立 PRD) | `run_ledger_event.py`, `asset_record.py`, `run_ledger_service.py`, `scripts/os_registry.py` |
|| v0.24 | (无独立 PRD) | `scripts/ceo_cmd.py`, `docs/registry/CAPABILITY-REGISTRY.md` |
|| v0.25+ | (待定) | 见本文件「下一阶段」章节 |

> 🔗 **本路线图已被五层架构（Execution Spine / Governance Kernel / Memory & Asset Layer / Founder Control Plane / Productization & Evidence）正式结构化。**
>
> 详细的外部借鉴分析（Paperclip / PilotDeck / OpenAI / GitHub / Microsoft）见 [`docs/architecture/UNIFIED-ROADMAP-v0.23+.md`](docs/architecture/UNIFIED-ROADMAP-v0.23+.md)
