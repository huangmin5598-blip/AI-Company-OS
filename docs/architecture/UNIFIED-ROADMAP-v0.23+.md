# AI Company OS — 统一路线图（v0.23+ 综合版）

> 本文件整合了三份输入：
> 1. **`ai-company-os` 仓库状态**（v0.23 刚完成：Run Ledger + Asset Registry）
> 2. **OS 能力建设路线图 docx**（双轨并行 + 6 个正式项目）
> 3. **外部借鉴优先级表**（Paperclip / PilotDeck / OpenAI / GitHub / Microsoft 分析）
>
> 最后更新：2026-05-30

---

## 一、当前基线

### 已完成的完整链路（`ai-company-os` 仓库）

```
CEO Brief → Review → Decision → Draft → Work Order
  → approve-dispatch → route → execute → callback → completed
    → result backfill → Run Ledger + Asset Registry
```

### 对应借鉴表的 5 条「现在做」

| 借鉴条目 | 我们在做的部分 | 缺口 |
|----------|--------------|------|
| ① Safe Outputs + 默认只读 + Capability Boundary | Skill Router + Runtime Governance 已有雏形 | **没有正式的 capability manifest、没有 read-only 默认模式** |
| ② Workflow-first | Work Orders + CEO Brief + Operating Loop ✅ | 继续强化 |
| ③ White-box Memory | Run Ledger + Asset Registry ✅（v0.23） | 需补 `source_refs`、`supersedes`、`confidence` |
| ④ WorkSpace / Deck 产品表达 | `projects/`、`reports/` 已按项目隔离 | **命名体系还偏工程内部语言** |
| ⑤ Thin Founder Console | CEO Agent 规划中（v0.24） | 还没开始 |

---

## 二、项目池映射

docx 定义的项目池跟 `ai-company-os` 仓库的关系：

| docx 项目 | 当前状态 | 映射到 ai-company-os 仓库 |
|-----------|---------|--------------------------|
| `gateway-lite-v1` | ✅ 稳定运行 | **独立系统**（OpenClaw 生态，不在本 repo） |
| `control-center-v1` | 🔵 P0 | **部分重叠**：CEO Agent Re-entry (v0.24) + `os_registry.py` CLI |
| `capability-registry-v1` | 🔵 P0 | **需要新建**：`docs/CAPABILITY-REGISTRY.md` |
| `preflight-diagnostics-v1` | 🟡 P1 | **部分重叠**：`runtime_health.py` + `failure_policy.py` |
| `os-radar + skills-gap` | ✅ 固定机制 | **独立机制**（OpenClaw 生态） |
| `evidence-dashboard-lite-v1` | 🟡 P1 | **可消费 Run Ledger + Asset Registry** 做对外展示 |

---

## 三、统一路线图（v0.24 ~ v1.0）

### v0.24 — CEO Agent Re-entry + Capability Registry ⬅️ 下一步

**周期**：1 周
**对应借鉴 ⑤ + docx `control-center-v1` P0 + `capability-registry-v1` P0**

#### 交付

**A. CEO Agent Re-entry（主线）**
- 集成 Hermes Skill + 后端 API
- 3 类意图：status_query / asset_query / draft_action
- 后端查询：Run Ledger + Asset Registry + Work Orders + Decision Log
- Founder 自然语言 → 回答/动作

**B. CAPABILITY-REGISTRY.md（新建）**
- 文档 `docs/CAPABILITY-REGISTRY.md`
- 记录当前所有 Agent + Runtime 的能力、边界、职责
- 为 "默认只读 + Safe Outputs" 打底

**C. Skill Registry 增强**
- 补 `preferred_for` / `cost_class` / `quality_class` 字段（对应借鉴 ⑧ "可解释路由"）

#### 不做
- 自动决策 / 自动调度 / 自动审批 / Paperclip
- Full GUI / 重交互 UI / 多 agent 会议
- gateway-lite-v1 改动

---

### v0.24.1 — White-box Memory + Safe Outputs

**周期**：1 周
**对应借鉴 ① ③**

#### 交付

**A. White-box Memory**
- Run Ledger 每条事件补：`source_refs` / `confidence` / `supersedes` / `superseded_by`
- Asset Registry 补：`status` (active/archived/superseded) / `linked_decisions` / `linked_assets`

**B. Capability Boundary（读/写/提升）**
- 在 Skill Registry 中引入等级制：
  - `read_capabilities`（默认有）
  - `safe_outputs`（写预览，不实际写）
  - `elevated_write_actions`（需批准）
  - `approval_required_actions`（关键操作）
- Router 根据等级分流

#### 不做
- 重做 Skill Router 架构
- 复杂权限系统
- durable execution / checkpoint

---

### v0.25 — Founder Console Thin

**周期**：1 周
**对应借鉴 ⑤ + docx `control-center-v1` P0 + `evidence-dashboard-lite-v1` 首版**

#### 交付

**A. Thin CLI Dashboard（扩展 `os_registry.py`）**
- `os status` — 系统概览（WO 统计 / 最近事件 / 资产数量）
- `os wo list` — WO 列表与状态
- `os assets lineage <id>` — 已有

**B. Evidence Dashboard Lite（纯 HTML 单页）**
- 从 Run Ledger + Asset Registry 生成外部可读的展示页
- 展示：项目状态 / Agent 状态 / Run Flow / Asset Growth / Gateway Summary
- 输出到 `docs/evidence/` 或 `reports/`

#### 不做
- 重 GUI 框架
- 多租户 / 复杂实时系统
- GitHub Pages 自动部署

---

### v0.26 — External Runtime + Plugin SDK 初探

**周期**：1 周
**对应借鉴 ⑦ ⑩**

#### 交付

**A. Plugin SDK Sketch**
- 定义 `Capability Manifest` 格式
- 外部 Runtime 声明 Capabilities 的接口
- 示例 manifest + 文档

**B. MCP / A2A 轻量兼容**
- Runtime Registry 添加 MCP/A2A 协议支持标记
- 非默认启用，只做接口预备

#### 不做
- 完整插件系统
- 完全 MCP/A2A 实现
- Agent mesh

---

### v1.0 — 公司决策层

**对应借鉴 ⑨ + docx "控制平面终局"**

#### 交付

- **Workflow Checkpointing**：长时 WO 可中断/恢复
- **Smart Routing**：基于 capability + cost + quality 的自动路由
- **Durable HITL**：创始人审批 + 可恢复的执行流
- **Agent Meeting Lite**：结构化多 Agent 协作（CEO 主持）

---

## 四、不做清单（当前阶段明确不做）

| 方向 | 原因 |
|------|------|
| Paperclip 接管治理内核 | 治理是自己的核心能力 |
| 整体迁移到 PilotDeck / Paperclip | 已有主路径，收益 < 风险 |
| 大而全 GUI / OS 桌面环境 | 把你拉回做平台，不是跑业务 |
| 多 Agent 自由 mesh / 会议 | 显式 workflow + guardrails 更优先 |
| Always-on / 后台自动整理 | 更可控、更可解释 优先于 更自动 |
| gateway-lite-v1 改造 | 独立系统，不进本 repo 主线 |
| 复杂实时系统 | P0~P1 阶段不需要 |

---

## 五、时间线总览

```
本周        v0.24   CEO Agent Re-entry + Capability Registry
下周        v0.24.1 White-box Memory + Safe Outputs
第 3 周     v0.25   Founder Console Thin + Evidence Dashboard Lite
第 4 周     v0.26   Plugin SDK Sketch + MCP/A2A 轻兼容
第 5-6 周   v1.0    公司决策层（Checkpointing + Smart Routing + HITL）
```

对应 docx 的 6-12 周路线：
- **2 周** ← v0.24 + v0.24.1（CEO Agent + Capability Registry + White-box Memory）
- **4-6 周** ← v0.25 + v0.26（Thin Console + Evidence Lite + Plugin Sketch）
- **8-12 周** ← v1.0（公司决策层）

对应借鉴表的优先级：
- **现在做** ← v0.24 + v0.24.1（Safe Outputs + Workflow-first + White-box Memory + WorkSpace + Thin Console）
- **后面做** ← v0.26 + v1.0（Plugin SDK + Smart Routing + Checkpoint + MCP/A2A）
- **现在不做** ← 全部遵守

---

## 六、项目状态矩阵（按 docx 规范）

| 项目 | stage | end_state | owner | next_step | freeze_rule |
|------|-------|-----------|-------|-----------|-------------|
| `CEO Agent Re-entry` | P0 | Founder 自然语言控制台 | Hermes | v0.24 编码实现 | 完成 P0 后升 P1 |
| `Capability Registry` | P0 | 能力地图/规划系统 | Hermes | 创建 `CAPABILITY-REGISTRY.md` | 完成 P0 后进入稳定维护 |
| `White-box Memory` | P0 | 可追溯记忆体系 | Hermes | v0.24.1 字段扩展 | 完成 P0 后进入稳定运行 |
| `Safe Outputs / Boundary` | P0 | 默认只读+分级操作 | Hermes | v0.24.1 Skill Registry 改造 | 完成 P0 后进入治理层 |
| `Founder Console Thin` | P0 | Founder 控制平面 | Hermes | v0.25 CLI + HTML 展示 | 完成 P0 后升 P1 |
| `Evidence Dashboard Lite` | P1 | 对外证据展示层 | Hermes | v0.25 首版 | 完成 Lite 后升 P1 |
| `Plugin SDK` | P2 | 插件/能力体系 | — | 暂不启动(v0.26) | 等待 Console 稳住 |
| `Smart Routing` | P2 | 可解释自动路由 | — | 暂不启动(v0.26+) | 等待 Capability Registry 完整 |
| `Agent Meeting` | — | 多 Agent 协作 | — | 暂不启动(v1.0) | 等待 Workflow First 做硬 |
