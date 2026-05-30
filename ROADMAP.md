     1|# AI Company OS — 路线图
     2|
     3|> 最后更新：2026-05-17（v0.27 Sprint 1）
     4|> 五层架构：Execution Spine / Governance Kernel / Memory & Asset Layer / Founder Control Plane / Productization & Evidence
     5|
     6|---
     7|
| 里程碑总览

```
v0.02 ─ v0.10  基础框架 ── Loop / CEO Agent / Memory / Runtime / Monitor    🏁
v0.10 ─ v0.14  委派层 ── Work Order / Skill Router / Execution Mode / Bridge  🏁
v0.15 ─ v0.23  治理 + 决策到执行闭环 ── Governance / Ledger / Asset Registry  🏁
v0.24 ─ v0.25  系统级能力建设 ── CEO Cmd / Founder Console / Preflight        🏁
v0.26          证据层 ── Evidence Summary / GitHub Refresh                    🏁
v0.27 ─ v0.29  产品化 ── Operating Kit / Capability Boundary / Workflow       🏗️
v1.0+           发布 ── Product Launch                                        🔮
```
    19|
    20|---
    21|
    22|## 已完成
    23|
    24|### v0.02 — Company Loop MVP
    25|- 基础公司循环机制
    26|
    27|### v0.03 — CEO Agent Lite
    28|- CEO Agent 原型
    29|
    30|### v0.04 — Company Memory MVP
    31|- 公司记忆系统
    32|
    33|### v0.05 — Monitor Framework Lite
    34|- 监控框架轻量版
    35|
    36|### v0.06 — Runtime Layer MVP
    37|- Runtime 层概念验证
    38|
    39|### v0.07 — Controlled Self-Improvement Proposal MVP
    40|- 受控自我改进提案
    41|
    42|### v0.08 — Controlled Execution Bridge MVP
    43|- 受控执行桥
    44|
    45|### v0.09 — Code-Capable Runtime Bridge MVP
    46|- 代码能力 Runtime 桥
    47|
    48|### v0.09.2 — External Runtime Connector MVP
    49|- 外部 Runtime 连接器
    50|
    51|### v0.10 — Work Delegation Layer MVP
    52|- Work Order 创建/路由/执行闭环
    53|- Execution Mode 矩阵
    54|- Skill Router 概念验证
    55|
    56|### v0.13 — OpenClaw Bridge Callback MVP
    57|- OpenClawBridge 对接 OpenClaw 外部 Agent
    58|- Inbox/Outbox 协议
    59|- Task Card 生成
    60|- Callback API (POST /openclaw-callback)
    61|- 幂等 / force 覆盖 / API Key 校验
    62|
    63|### v0.14 — Bridge Reference Worker
    64|- 参考 Worker 实现 (bin/openclaw_worker.py)
    65|- inbox → working → result.json 闭环
    66|- LocalLLMExecutor 本地执行 (Ollama / deepseek-r1:8b)
    67|- EchoExecutor 规则快速路径
    68|- **叙事修正前**：错误地称为"OpenClaw 原生执行"
    69|
    70|### v0.14.1 — OpenClaw Native Executor Integration
    71|- **叙事修正**：v0.14 是 Reference Worker，v0.14.1 才是 OpenClaw 原生执行
    72|- Executor 抽象接口 (base.py / factory.py)
    73|- OpenClawAgentExecutor：调用 `openclaw agent --json`
    74|- Agent 映射：research-agent / finance-analyst / amazon-seller / content-manager / main
    75|- Feature Flag：`OPENCLAW_EXECUTOR_MODE = auto | openclaw_native | local_llm | echo`
    76|- Result Manifest 完整 Provenance：executor_type / model_name / token_usage / duration_ms / openclaw_run_id
    77|
    78|### v0.14.2 — OpenClaw Native Executor Hardening ✅ (当前)
    79|- **E2E 测试拆分**：主套件 80/80 + Callback API Contract Test 21/21
    80|- **Result Manifest 工具证据字段**：tool_calls_detected / inferred_tools / tool_call_summary / tool_call_evidence_source / tool_trace_available
    81|- **extract_inferred_tools()**：从 Agent 输出文本推断工具调用
    82|- **Evidence 文档**：docs/evidence/openclaw-native-agent-tool-execution-v0.14.2.md
    83|- **诚实记录限制**：CLI 无 tool trace / session 未复用 / 文本推断
    84|
    85|---
    86|
    87|## 下一阶段：治理 + 自动化 (v0.15 ~ v0.18)
    88|
    89|### v0.15 — Skill Registry & Routing Contract Lite ✅ (已完成)
    90|
    91|**版本**：v0.15 · 2026-05-30
    92|
    93|**目标**：让 AI Company OS 知道"该让谁干什么活"
    94|
    95|**交付**：
    96|1. **Skill Registry YAML** (`backend/config/skill_registry.yaml`)
    97|   - 5 skills: research_summary / finance_analysis / amazon_seller_analysis / opportunity_scan / code_change
    98|   - 每个 skill 含 skill_id / description / task_types / default_agent / runtime / executor / risk_level / approval_required / output_schema / allowed_tools / budget_class
    99|2. **Skill Registry Loader** (`backend/app/services/skill_registry.py`)
   100|   - YAML 加载 + 校验 + 缓存 + fail-fast
   101|   - `get_contract(task_type) → RoutingContract` 查询接口
   102|   - `extract_inferred_tools()` 工具推断函数
   103|3. **Router 改造** (`backend/app/services/skill_router.py`)
   104|   - 从硬编码 dict + DB 表 → YAML-backed
   105|   - 输出兼容旧字段名 (owner_agent / runtime_id / execution_mode)
   106|4. **WO 路由元数据**
   107|   - route handler 记录 assigned_agent / approval_required / routing_reason
   108|   - task card 包含 skill_id / selected_agent / routing_reason
   109|   - result.json 包含 skill_id / selected_agent / routing_reason
   110|5. **未知 task_type** → **needs_review**（非 blocked）
   111|6. **17 task_types 映射**（含兼容旧值）
   112|7. **测试**：60/60 Skill Registry + 80/80 E2E + 21/21 Callback API
   113|
   114|**不做**：Paperclip / Heartbeat / Budget / Cron / 大 UI / Agent Meeting / Skill Marketplace / 自动高风险任务
   115|
   116|### v0.16 — Runtime Governance Lite ✅ (已完成)
   117|
   118|**版本**：v0.16 · 2026-05-30
   119|
   120|**目标**：在 v0.17 Operating Loop 自动运行前，给 AI Company OS 加最小安全网。
   121|
   122|**交付**：
   123|1. **Runtime Health Check** (`backend/app/services/runtime_health.py`)
   124|   - 按需检查 OpenClaw CLI / Codex CLI / Ollama API 可用性
   125|   - 返回 healthy / degraded / unhealthy
   126|   - 不做常驻 daemon
   127|2. **Failure Policy** (`backend/app/services/failure_policy.py`)
   128|   - unknown_task_type → needs_review
   129|   - runtime_unhealthy → needs_review
   130|   - executor_timeout → retry (低风险) / needs_review (中高风险)
   131|   - 连续失败 2 次 → escalation_required
   132|3. **Cost Summary** (`backend/app/services/cost_summary.py`)
   133|   - 扫描 artifacts/ 中所有 result.json
   134|   - 按 work_order / agent / runtime / skill 汇总 token
   135|   - estimated_cost（非 actual billing）
   136|   - Markdown 报告生成
   137|4. **Soft Budget Guard** (`backend/config/budget_policy.yaml`)
   138|   - 每个 skill 的 token 阈值
   139|   - action: warn / needs_review（不做硬 kill）
   140|   - YAML 缺失时使用默认值
   141|5. **API 端点**
   142|   - GET /api/v1/governance/health
   143|   - GET /api/v1/governance/cost-summary
   144|   - GET /api/v1/governance/cost-report
   145|   - POST /api/v1/governance/budget-check
   146|6. **测试**：29/29 Governance + 80/80 E2E + 21/21 Callback + 60/60 Skill Registry
   147|
   148|### v0.17 — Daily Operating Loop MVP ✅ (已完成)
   149|
   150|**版本**：v0.17 · 2026-05-30
   151|
   152|**目标**：验证 Operating Loop 机制——系统能从 scheduled_work_orders.yaml 读取配置，按 cadence 创建并执行 Work Order，生成 CEO Brief。
   153|
   154|**范围（收窄版）**：只配 1 个任务（daily-system-health-brief），手动 `--once` 模式，不下 launchd。
   155|
   156|**交付**：
   157|1. **Scheduler** (`backend/app/services/scheduler.py`)
   158|   - 从 YAML 加载 scheduled_work_orders（daily/weekly/monthly cadence）
   159|   - 到期判断 + 防重复创建（同一天同 scheduled_id 只跑一次，除非 --force）
   160|   - ScheduledWorkOrder 数据类
   161|2. **CEO Brief** (`backend/app/services/ceo_brief.py`)
   162|   - 8 段式 Markdown 生成器：运行摘要 / Runtime Health / Work Orders / Cost / Budget & Failure Warnings / 重要发现 / Founder 决策 / 下一步建议
   163|   - 自动收集 Health Check、Cost Summary、Budget Guard 数据
   164|   - 自动推断 Founder 决策事项（unhealthy runtime、failed WO、needs_review、budget overflow）
   165|3. **run_operating_loop.py** CLI
   166|   - `--dry-run`：预览任务、Health、Cost，不执行
   167|   - `--once`：完整执行——读 YAML → 到期判断 → 去重 → Health Check → Budget Guard → 创建 Work Order → OpenClaw 派单 → Failure Policy → CEO Brief
   168|   - `--force`：跳过同天去重
   169|   - `--scan-pending`：预留（默认 False，v0.17 不扫 pending）
   170|4. **配置**：`backend/config/scheduled_work_orders.yaml` · 1 个任务
   171|5. **测试**：190/190 通过（29 governance + 60 skill_registry + 21 callback + 80 e2e）
   172|
   173|**不做**：launchd / crontab / 3+ scheduled tasks / 扫 pending / Web UI / Paperclip / 自动批准
   174|
   175|**明确边界**：
   176|- `--dry-run`：不创建任何 Work Order，但输出完整的 CEO Brief（含 DRY-RUN 标记）
   177|- 防重复：基于 route_reason 的前缀匹配 "scheduled:{id}:YYYY-MM-DD"
   178|- 执行前必做 Health Check，unhealthy 时跳过执行
   179|
   180|### v0.18 — CEO Brief Review & Decision Layer Lite ✅ (已完成)
   181|
   182|**版本**：v0.18-0.18.3 · 2026-05-30
   183|
   184|**目标**：让 Founder 能 Review Brief → 做 Decision → 生成 Work Order Draft，完成 CEO 决策闭环前 3 步（不涉及 WO 执行）。
   185|
   186|**交付**：
   187|1. **`scripts/review_brief.py`** — 纯 Markdown 规则解析，零 LLM
   188|   - `index` — 扫描 `reports/ceo-briefs/` 生成 INDEX.md
   189|   - `review <brief>` — 提取 Decision Items + 生成 Review 模板
   190|   - `decide <review>` — 读取勾选的决策 → 写入 DECISION-LOG.md（去重 + 冲突检测）
   191|   - `create-work-order <draft>` — 校验 Draft 必填字段 → 生成预览
   192|   - `status` — 所有 Brief 概览面板
   193|2. **Draft 生成** — decide 中 `create_work_order_later` → 自动生成 WO-DRAFT 文件
   194|3. **三方去重** — 同 Brief + 同 ID + 同 Decision 任一匹配则跳过
   195|4. **冲突检测** — 一个 Decision Item 勾了多个选项 → 标记 invalid_review
   196|
   197|**不做**：LLM / API 调用 / WO 创建 / 自动执行
   198|
   199|### v0.19 — Work Order Draft to API Integration ✅ (已完成)
   200|
   201|**版本**：v0.19-0.19.1 · 2026-05-30
   202|
   203|**目标**：打通 Draft → 真实 Work Order API 调用。
   204|
   205|**交付**：
   206|1. **create-work-order 升级** — 从 preview-only → 真实 `POST /api/v1/work-orders`
   207|2. **Draft Footer** — WO 创建后回写 `work_order_id` / `status`
   208|3. **Draft INDEX** — 更新状态 + WO ID 列
   209|4. **去重防护** — 已创建 WO 的 Draft 不可重复创建
   210|5. **必填校验** — task_type / proposed_prompt / expected_output 缺一不可
   211|
   212|### v0.20 — Work Order Route & Approval Gate ✅ (已完成)
   213|
   214|**版本**：v0.20 · 2026-05-30
   215|
   216|**目标**：Work Order 从 created → 可 approve-dispatch。
   217|
   218|**交付**：
   219|1. **`POST /work-orders` API** — 接收 `source_brief` / `source_decision` / `source_draft` / `approval_required` 元数据
   220|2. **WO 状态机** — `created`（非 `draft`）不自动 route/dispatch
   221|3. **`scripts/work_order_control.py approve-dispatch <WO_ID>`**
   222|   - 校验 status=created & approval_required=true
   223|   - 写入 `approved_for_dispatch_at` + `approval_id`
   224|   - 拒绝 6 种非法状态
   225|4. **测试**：190/190 通过
   226|
   227|### v0.21 — Work Order Route & Execute Gate ✅ (已完成)
   228|
   229|**版本**：v0.21 · 2026-05-30
   230|
   231|**目标**：approve-dispatch → `/route` → `/execute` 全链路。
   232|
   233|**交付**：
   234|1. **approve-dispatch 升级** — 批准后依次调用 `POST /route` → `POST /execute`
   235|2. **route 端点** — `POST /work-orders/{id}/route` 填充 skill_id / runtime / risk 等
   236|3. **execute 端点** — `POST /work-orders/{id}/execute` 状态迁移
   237|4. **`approved_for_dispatch_at` 字段** — DB migration + 幂等写入
   238|5. **测试**：21 approve-dispatch 测试通过
   239|
   240|### v0.22 — Work Order Executor Integration ✅ (已完成)
   241|
   242|**版本**：v0.22 · 2026-05-30
   243|
   244|**目标**：`POST /execute` 真正调用 `WorkOrderExecutor`，WO 从 routed → executed。
   245|
   246|**交付**：
   247|1. **`POST /{id}/execute` 重写** — 调用 `WorkOrderExecutor.execute_work_order(wo_id)`
   248|2. **同步模式** — `direct_delegate` / `local_script` 立即完成
   249|3. **异步模式** — `openclaw_agent` 写入 inbox task card，status=in_progress
   250|4. **幂等保护** — status!=routed 时拒绝二次执行
   251|5. **`wait-result <WO_ID>`** — 轮询至 completed/failed/cancelled
   252|6. **openclaw_agent handler 别名映射** — 修复 `research-agent` 等映射
   253|7. **全链路实测** — WO-B565EE14 28s, WO-15D55075 15s
   254|
   255|### v0.22.1 — Decision-to-Execution Result Backfill ✅ (已完成)
   256|
   257|**版本**：v0.22.1 · 2026-05-30
   258|
   259|**目标**：WO completed 后，把执行结果回写到 source Draft + INDEX + DECISION-LOG。
   260|
   261|**交付**：
   262|1. **`wait-result --sync-source <WO_ID>`** — WO completed 后三重回写
   263|   - Draft Footer 追加 `## Execution Result`（幂等）
   264|   - Draft INDEX.md 更新为 completed
   265|   - DECISION-LOG.md 追加 Execution Completed 行
   266|2. **Source Metadata 保留** — route 端点不再覆盖 `routing_log_json` 中的 source 字段
   267|3. **幂等** — 重复 `--sync-source` 不重复写入
   268|
   269|### v0.23 — Run Ledger MVP + Asset Registry MVP ✅ (已完成)
   270|
   271|**版本**：v0.23 · 2026-05-30
   272|
   273|**目标**：把 v0.18-v0.22 产生的事件和资产统一记录，让系统知道自己发生了什么、产出了什么。
   274|
   275|**交付**：
   276|1. **`RunLedgerEvent` 模型** (`run_ledger_events` 表) — append-only OS 级事件日志
   277|   - 10 种事件类型：brief_generated → review_created → decision_logged → draft_created → work_order_created → approved_for_dispatch → routed → executed → callback_completed → result_synced
   278|   - 分层幂等 key：文件类 `event_type+source_id` / WO 类 `+work_order_id` / Decision 类 `+decision_id`
   279|2. **`AssetRecord` 模型** (`asset_registry` 表) — 6 种资产类型
   280|   - ceo_brief / ceo_brief_review / decision_log_entry / work_order_draft / work_order / execution_result
   281|3. **写入点** — 6 个链路节点追加（`run_operating_loop.py` / `review_brief.py` 3 节点 / `work_order_control.py` 2 节点）
   282|4. **`scripts/os_registry.py`** CLI — `ledger recent` / `assets list` / `lineage <asset_id>`
   283|5. **同 SQLite，不新建数据库** — 1 张 `run_ledger_events` 表 + 1 张 `asset_registry` 表
   284|---
   285|## 下一阶段：系统级能力建设 (v0.24 ~ v1.0)
   286|
   287|### v0.24 — CEO Command Interface + Capability Registry P0 ✅ (已完成)

> 2026-05-30
   288|
   289|**五层归属**：Founder Control Plane + Governance Kernel
   290|
   291|**目标**：给 Hermes / Founder 一个可审计的 OS 操作接口（CEO Command Interface），同时建立能力地图 P0。
   292|
   293|**Sprint A — Capability Registry P0**
   294|- `docs/registry/CAPABILITY-REGISTRY.md` + 可选 `config/capability-registry.yaml`
   295|- 记录：agent_id / role / runtime / capabilities / boundaries / supported_workflows / risk_level / cost_class / approval_required_actions
   296|- 至少登记 5 个 agent/runtime：research-agent / finance-analyst / amazon-seller / codex / ceo-cmd-interface / openclaw_agent
   297|- 明确区分 `hermes-main`（Founder-facing Chief of Staff）和 `ceo-cmd-interface`（System-facing 操作接口）
   298|
   299|**Sprint B — CEO Command Interface**
   300|- `scripts/ceo_cmd.py` — status / assets / lineage / draft-from-decision / draft-from-asset
   301|- 数据源：Run Ledger / Asset Registry / Work Orders / CEO Brief / Decision Log / Capability Registry
   302|- 所有动作写入 Run Ledger 或 ceo_action_log
   303|
   304|**边界**：
   305|- ✅ 查询系统状态 / 查询资产 / 查询 lineage / 查询能力地图 / 生成 Draft
   306|- ❌ 不能 create Work Order / 不能 approve-dispatch / 不能 execute
   307|- ❌ 不能自动审批 / 不能绕过 Founder / 不能自动批量派工
   308|
   309|**不做**：自动执行 / 自动审批 / 复杂目标拆解 / Agent Meeting / Web UI / 向量搜索 / launchd 改动 / worker 改动 / WO 主链路改动
   310|
   311|---
   312|
   313|### v0.25 — Founder Control Plane — 5-Tab IA + Founder Console + Preflight 11/11 ✅ (已完成)

> 2026-05-30
   314|
   315|**五层归属**：Founder Control Plane + Governance Kernel
   316|
   317|**目标**：一眼看清系统状态，同时具备基础自检能力。
   318|
   319|**交付**：
   320|1. **Thin Console CLI** — `scripts/founder_console.py {status,health,decisions,assets}`
   321|   - 复用 Run Ledger / Asset Registry / Work Orders / CEO Brief / Runtime Health
   322|   - 不新建数据源，不重写查询链路
   323|2. **Preflight Checks** — Console 的 health section
   324|   - 检查：DB path / launchd / OpenClaw / Codex / Ollama / Run Ledger writable / Asset Registry writable / reports path writable / budget config valid
   325|3. **输出格式**：Markdown 摘要，不做 Web UI
   326|
   327|**不做**：重 GUI / 复杂交互 / 多租户 / 实时系统 / 大而全后台
   328|
   329|---
   330|
   331|### v0.26 — Evidence Dashboard Lite + GitHub Refresh 🏗️ (进行中)

> 2026-05-30
   332|
   333|**五层归属**：Productization & Evidence
   334|
   335|**目标**：对外展示系统在运行、资产在增长、机制在工作。
   336|
   337|**交付**：
   338|1. **Evidence Dashboard Lite**（纯 HTML / Markdown）
   339|   - 输入：Run Ledger / Asset Registry / CEO Brief / Decision Log / Work Orders / Cost Summary
   340|   - 展示：Run Flow / Asset Growth / Agent Status / Decision-to-Execution Evidence / Gateway Summary
   341|2. **GitHub 刷新**
   342|   - README 更新
   343|   - Release note 同步
   344|   - 证据页面输出到 `docs/evidence/`
   345|
   346|**不做**：重交互产品 / 复杂实时系统 / 多租户 / 独立站搭建
   347|
   348|---
   349|
   350|### v0.27 — Operating Kit v0.1 + Capability Boundary 🔮 (计划中)
   351|
   352|**五层归属**：Governance Kernel + Productization & Evidence
   353|
   354|**目标**：把跑通的流程整理成可复用的 Operating Kit，同时引入安全边界体系。
   355|
   356|**交付**：
   357|1. **Operating Kit v0.1**
   358|   - Decision-to-Execution Kit / Daily Operating Loop Kit / CEO Brief Review Template / Work Order Template
   359|2. **Capability Boundary**
   360|   - 正式引入等级制：`read_capabilities` / `safe_outputs` / `elevated_write_actions` / `approval_required_actions`
   361|   - 对应借鉴：GitHub Agentic Workflows "默认只读 + Safe Outputs"、v0.8/v0.9 安全原则统一抽象
   362|
   363|**不做**：商业打包 / 完整安全系统 / 多租户权限
   364|
   365|---
   366|
   367|### v0.28 — Company Instance Config + Runtime Manifest 🔮 (计划中)
   368|
   369|**五层归属**：Productization & Evidence + Governance Kernel
   370|
   371|**目标**：OS Core 与个人配置分离，Runtime/Capability Manifest 正式化。
   372|
   373|**交付**：
   374|1. **Company Instance Config**
   375|   - `company-instance.yaml` — 个人配置与 OS Core 分离
   376|2. **Runtime Manifest**
   377|   - `runtime-manifest.yaml` — Runtime 声明格式
   378|   - `capability-manifest.yaml` — Capability 声明格式
   379|   - `safe-output-policy.yaml` — 安全输出策略
   380|3. 延续 v0.4.1 Productization & Runtime Readiness 方向
   381|
   382|**不做**：多租户 / 云部署 / 计费 / 模板市场
   383|
   384|---
   385|
   386|### v0.29 — Workflow Composition 🔮 (计划中)
   387|
   388|**五层归属**：Execution Spine
   389|
   390|**目标**：显式工作流编排，取代 Agent Meeting。
   391|
   392|**交付**：
   393|1. **WO depends_on** — Work Order 之间的依赖关系
   394|2. **WO chain** — A → B → C 顺序执行
   395|3. **multi-step workflow** — 带 checkpoint 的多步流程
   396|4. **parent/child WO** — 父子 WO 关系
   397|5. **handoff artifact** — WO 之间的产物交接
   398|
   399|**示例**：Research WO → Opportunity Card WO → Validation Plan WO → Landing Page WO
   400|
   401|**不做**：Agent Meeting / 自由多 Agent mesh / 复杂 DAG 编辑器
   402|
   403|---
   404|
   405|### v1.0 — Product Launch / Operating Kit Productization 🔮 (计划中)
   406|
   407|**五层归属**：Productization & Evidence
   408|
   409|**目标**：AI Company OS 从自用系统走向可售。
   410|
   411|**交付**：
   412|1. GitHub / 独立站 / 销售页
   413|2. Operating Kit 案例页
   414|3. AI Company OS 方法论文档
   415|4. Solo Founder Operating Kit（可售）
   416|
   417|**注意**：v1.0 不再是 Agent Meeting。Agent Meeting 已被删除，替换为 v0.29 Workflow Composition。
   418|
   419|---
   420|
   421|## 已删除概念
   422|
   423|| 旧概念 | 删除原因 | 替代方案 |
   424||--------|---------|---------|
   425|| Agent Meeting Session | Workflow-first 优于 Multi-agent Society | v0.29 Workflow Composition（WO depends_on / WO chain） |
   426|| Research-to-Opportunity 独立版本 | 已跑过一轮验证，不需要重复做 | Asset Registry + Weekly OS Review 机制承载 |
   427|| Run Ledger Dashboard Lite | 被 v0.25 Thin Console + v0.26 Evidence Dashboard 吸收 | — |
   428|
   429|---
   430|
   431|## 五层架构
   432|
   433|```
   434|AI Company OS — 五层能力架构
   435|
   436|1. Execution Spine（执行脊柱）
   437|   Work Order → Route → Execute → Callback → Result
   438|   关键技术：WorkOrderExecutor / Skill Router / OpenClaw / Codex Adapters
   439|
   440|2. Governance Kernel（治理内核）
   441|   Approval / Budget / Failure Policy / Capability Boundary / Safe Outputs
   442|   关键技术：Budget Guard / Failure Policy / Skill Registry / Capability Registry
   443|
   444|3. Memory & Asset Layer（记忆资产层）
   445|   Run Ledger / Asset Registry / Company Memory / Lineage
   446|   关键技术：run_ledger_events / asset_registry / CEO Action Log
   447|
   448|4. Founder Control Plane（Founder 控制平面）
   449|   CEO Brief / Review / Decision / CEO Command Interface / Thin Console
   450|   关键技术：ceo_brief.py / review_brief.py / ceo_cmd.py / founder_console.py
   451|
   452|5. Productization & Evidence Layer（产品化与证据层）
   453|   Evidence Dashboard / Operating Kit / GitHub / 独立站 / 可售包
   454|   关键技术：证据展示层 / Company Instance Config / Runtime Manifest
   455|```
   456|
   457|---
   458|
   459|## 版本文档索引
   460|
   461|| 版本 | PRD | 关键代码 |
   462||------|-----|---------|
   463|| v0.13 | `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.13-OPENCLAW-BRIDGE-REAL-CALLBACK-PRD.md` | `openclaw_bridge.py`, `openclaw_callback.py` |
   464|| v0.14 | (无独立 PRD，参考 v0.13) | `openclaw_worker/` `executors/` |
   465|| v0.14.1 | (同上) | `executors/openclaw_agent_executor.py`, `base.py`, `factory.py` |
   466|| v0.14.2 | (同上) | `base.py` (tool evidence), `test_callback_api_contract.py` |
   467|| v0.15 | (无独立 PRD) | `skill_registry.yaml`, `skill_router.py`, `skill_registry.py` |
   468|| v0.16 | (无独立 PRD) | `runtime_health.py`, `failure_policy.py`, `cost_summary.py`, `budget_policy.yaml` |
   469|| v0.17 | (无独立 PRD) | `scheduler.py`, `ceo_brief.py`, `run_operating_loop.py`, `scheduled_work_orders.yaml` |
   470|| v0.18 | (无独立 PRD) | `scripts/review_brief.py` |
   471|| v0.19 | (同上) | `scripts/review_brief.py` (create-work-order API 调用) |
   472|| v0.20 | (同上) | `work_order_control.py`, `work_orders.py` (route 端点) |
   473|| v0.21 | (同上) | `work_order_control.py` (approve-dispatch), `work_orders.py` (execute 端点) |
   474|| v0.22 | (同上) | `work_order_executor.py`, `work_order_control.py` (wait-result) |
   475|| v0.22.1 | (同上) | `work_order_control.py` (--sync-source) |
|| v0.23 | (无独立 PRD) | `run_ledger_event.py`, `asset_record.py`, `run_ledger_service.py`, `scripts/os_registry.py` |
|| v0.24 | (无独立 PRD) | `scripts/ceo_cmd.py`, `docs/registry/CAPABILITY-REGISTRY.md` |
|| v0.25+ | (待定) | 见本文件「下一阶段」章节 |

> 🔗 **本路线图已被五层架构（Execution Spine / Governance Kernel / Memory & Asset Layer / Founder Control Plane / Productization & Evidence）正式结构化。**
>
> 详细的外部借鉴分析（Paperclip / PilotDeck / OpenAI / GitHub / Microsoft）见 [`docs/architecture/UNIFIED-ROADMAP-v0.23+.md`](docs/architecture/UNIFIED-ROADMAP-v0.23+.md)
   485|