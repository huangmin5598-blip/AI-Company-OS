# AI Company Control Center v0.1.1 — 稳定化报告

> **报告日期**: 2026-05-21
> **阶段**: P0 + P1 已完成
> **Tag**: `v0.1.1-p0` | `v0.1.1`（正式 tag）
> **下一步**: P2 成本数据修复 + Hermes 上下文（可选）

---

## 1. 数据真实状态

### 逐项评估

| 数据类型 | 行数 | real | mock | partial | 评估 |
|:---------|:----:|:----:|:----:|:-------:|:-----|
| **execution_records** | 30 | **14** | 16 | 0 | 🟢 **已有真实数据** — 14 条来自 production-flow-ledger.json 的 14 条真实运行记录。16 条 mock 来自 seed，API 默认过滤 |
| **artifacts** | 5 | **0** | 5 | 0 | 🔴 **仍无真实数据** — artifact-ledger.json 有 JSON 解析错误（已在 adapter 中容错处理，生成 alert 报告），等待源文件修复 |
| **cost_snapshots** | 61 | **19** | 42 | 0 | 🟡 **部分真实** — 19 条来自 gateway-lite 的真实成本（6 agents、2 models、3 projects），42 条 mock 已过滤 |
| **alerts** | 10 | **8** | 2 | 0 | 🟢 **主要真实** — 8 条由 alert_detector 从真实 cron 错误和运行失败中生成，2 条 mock 已过滤 |
| **cron_jobs** | 21 | **21** | 0 | 0 | 🟢 **完全真实** — 全部 21 条来自 `jobs.json`，精确匹配 |
| **agents** | 18 | — | — | — | 🟡 **多源合并** — 15 个目录 Agent + 3 个额外发现，1 个 CLI 注册 |

### 核心指标（API 默认视图，不含 mock）

| 指标 | 值 |
|:-----|:----|
| 真实执行记录 | 14 条 （来自 production-flow-ledger） |
| 真实成本条目 | 19 条 （来自 gateway-lite） |
| 活跃报警 | 6 条 （来自 cron 错误 + 执行失败） |
| Cron Jobs | 21 个 （全部真实，来自 jobs.json） |
| 真实 Agent | 1 个 CLI 注册（main），17 个目录发现 |

---

## 2. Agent 口径定义

### 三维状态模型

| 维度 | 状态 | 判定逻辑 |
|:-----|:-----|:---------|
| **discovery_status** | `registered` | `openclaw agents list` CLI 返回 |
| | `unregistered` | 目录 `~/.openclaw/agents/{name}/` 存在，但 CLI 未注册 |
| | `discovered` | 仅目录存在 |
| **activity_status** | `active` | 过去 7 天（`AGENT_ACTIVE_WINDOW_DAYS=7`）内有执行记录 |
| | `inactive` | 7 天内无任何运行记录 |
| **health_status** | `ok` | 关联运行正常 |
| | `warning` | 存在但近期无数据 |
| | `error` | 关联 cron job 或 execution_record 有 failed/error |

### 当前分布

```
registered/inactive/warning   x15    ← 目录存在 + 种子数据
unregistered/inactive/warning x3     ← 目录存在但 CLI 未注册
```

> ⚠️ 注意：种子数据中所有 Agent 默认为 `discovered`，refresh 后按 CLI 输出校正。当前 CLI 仅注册了 `main`。

---

## 3. Mock 数据隔离

| 措施 | 状态 | 说明 |
|:-----|:----:|:------|
| data_source 字段 | ✅ | 5 张表已加（execution_records, artifacts, cost_snapshots, alerts, cron_jobs） |
| API 默认过滤 | ✅ | 5 个路由器默认 `.filter(data_source != 'mock')` |
| 调试模式 | ✅ | 支持 `?include_mock=true` 查询参数（需前端配合） |
| refresh 清除策略 | ✅ | 每次 refresh 前清除旧 real 数据，防止混合 |
| 种子标记 | ✅ | seed.py 中所有数据标记为 `data_source='mock'` |

---

## 4. Command Center Alpha 安全门

| 安全措施 | 状态 | 说明 |
|:---------|:----:|:------|
| `ALLOW_ALPHA_WRITE=false` | ✅ | 总开关，v0.1.1 默认关闭 |
| dry-run 默认模式 | ✅ | `mode=dry-run` 返回分析不执行 |
| `X-Confirm: yes` 头 | ✅ | execute 模式必须带确认头 |
| command_logs 记录 | ✅ | 所有写操作记录到 `command_logs` 表 |
| 403 拒绝执行 | ✅ | `ALLOW_ALPHA_WRITE=false` 时所有 execute 请求被拒绝 |

### 完整的写操作安全流程

```
用户 POST /api/v1/command
  │
  ├── mode=dry-run（默认）
  │     → 返回分析 + command_log_id
  │     → 不创建任务，不调 Agent
  │
  └── mode=execute
        ├── ALLOW_ALPHA_WRITE=false → 403 + command_log(rejected)
        └── ALLOW_ALPHA_WRITE=true
              ├── 缺少 X-Confirm: yes → 400 + command_log(rejected)
              └── X-Confirm: yes → 执行 + command_log(executed)
```

---

## 5. 已知未解决问题

| # | 问题 | 影响 | 计划 |
|:-:|:-----|:-----|:-----|
| 1 | **artifact-ledger.json JSON 解析错误** | 5 条 artifact 仍为 mock | 等待源文件修复 |
| 2 | **仅 1 个 Agent (main) CLI 注册** | 其他 17 个 Agent 无法通过指挥台调度 | 业务决策 — 是否需全部注册 |
| 3 | **成本数据仅 1 天明细（2026-03-30）** | 每日成本趋势不可用 | P2 中处理 |
| 4 | **对话面板无上下文感知** | 每轮对话独立，不能理解当前页面状态 | P2 中处理 |
| 5 | **前端的 `?include_mock=true`** | 目前仅后端支持，前端尚未实现切换按钮 | 低优先级 |

---

## 6. v0.1.1 tag

| Tag | 状态 | 说明 |
|:----|:----:|:------|
| `v0.1.1-p0` | ✅ 已打 | P0 数据可信化中间 tag |
| `v0.1.1` | ✅ **已打** | 正式 tag，P0 + P1 均完成 |

---

## 7. P1 完成内容

| 工作项 | 状态 | 说明 |
|:-------|:----:|:------|
| AgentResponse schema 加三维状态 | ✅ | discovery_status / activity_status / health_status |
| 前端 Agent 页面 3D badge | ✅ | Registered/Unregistered + Active/Inactive + OK/Warning/Error |
| 写端点 safety gate (PATCH agents) | ✅ | dry-run 默认 + ALLOW_ALPHA_WRITE + X-Confirm |
| 写端点 safety gate (POST/PATCH tasks) | ✅ | 同上 |
| 写端点 safety gate (POST command) | ✅ | 同上 |
| command_logs 全覆盖 | ✅ | 所有写尝试记录 |
| 前端 Alpha 标识 | ✅ | 指挥台/对话 导航标注 Alpha |
| 分层 | ✅ | Stable Core: Dashboard/Agents/Runs/Costs/Alerts |
| | | Alpha: Command Center / Hermes Chat Panel |

---

## 8. 下一步（P2 — 可选）

| 工作项 | 预估 |
|:-------|:----:|
| 成本数据同步修复（补充近期每日成本） | 0.5 天 |
| Hermes Chat Panel 上下文感知 | 0.5 天 |

---

> **总结**: v0.1.1 稳定化完成。P0 真实数据可信 + P1 安全边界 + 前端分层标识。P2 为体验优化，不影响核心稳定性，可按需安排。
