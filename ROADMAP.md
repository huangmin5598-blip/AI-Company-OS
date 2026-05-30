# AI Company OS — 路线图

> 最后更新：2026-05-30

---

## 里程碑总览

```
v0.02 ─ v0.10  基础框架 ── Loop / CEO Agent / Memory / Runtime / Monitor
v0.10 ─ v0.12  委派层 ── Work Order / Skill Router / Execution Mode
v0.13 ─ v0.14.2 Agent 真实执行 ── OpenClaw Bridge → Reference Worker → Native Executor
v0.15 ─ v0.18  治理 + 自动化 ── Skill Registry / Governance / Operating Loop / Console
v1.0+           决策层 ── Agent Meeting / 多Agent 协作 / 公司级闭环
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

### v0.17 — Operating Loop MVP

**目标**：系统定期自动创建 Work Orders，执行后生成 CEO Brief

**交付**：
- Scheduled Work Orders (基于 cron)
- Weekly Research Brief (research-agent 自动产出)
- OP-006 Validation Review (自动验证项目状态)
- System Health Brief (Runtime/Agent 状态汇总)
- Founder Decision Queue (待审批 Work Orders)

**前提**：v0.15 (Skill Registry) + v0.16 (Governance) 完成后再做

### v0.18 — CEO Console Lite

**目标**：轻量可视化界面查看系统运行状态

**交付**：
- Work Order 状态面板
- Agent 执行结果摘要
- Token/成本可视化
- Founder Decision 队列

---

## v1.0+ 展望

### v1.0 — Decision Session / Agent Meeting
- 多个 Agent 协同决策
- 冲突解决机制
- 公司级目标对齐

---

## 架构原则

```
AI Company OS                       ← 操作系统（核心能力内建）
├── Governance (Heartbeat/Budget/Approval)  ← OS 自己做
├── Skill Registry                  ← OS 自己做
├── Memory / Evidence               ← OS 自己做
├── Decision / Founder Console      ← OS 自己做
└── Runtime Adapters                ← 可插拔外部执行层
    ├── OpenClaw                    ← 已集成
    ├── Hermes                      ← 未来
    ├── Codex / Claude Code         ← 未来
    └── Paperclip                   ← 参考/可选，不做治理核心
```

---

## 版本文档索引

| 版本 | PRD | 关键代码 |
|------|-----|---------|
| v0.13 | `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.13-OPENCLAW-BRIDGE-REAL-CALLBACK-PRD.md` | `openclaw_bridge.py`, `openclaw_callback.py` |
| v0.14 | (无独立 PRD，参考 v0.13) | `openclaw_worker/` `executors/` |
| v0.14.1 | (同上) | `executors/openclaw_agent_executor.py`, `base.py`, `factory.py` |
| v0.14.2 | (同上) | `base.py` (tool evidence), `test_callback_api_contract.py` |
