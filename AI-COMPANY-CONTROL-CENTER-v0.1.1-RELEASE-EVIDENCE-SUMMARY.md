# AI Company Control Center v0.1.1 — Release Evidence Summary

> **Generated**: 2026-05-21
> **Version**: `v0.1.1` (Tags: `v0.1.1-p0` → `v0.1.1`)
> **Stack**: FastAPI + Next.js 14 + SQLite + OpenClaw Runtime
> **Location**: `~/Documents/Codex/ai-company-os/`

---

## 📦 Release Package

| # | 交付物 | 路径 | 状态 |
|:-:|:-------|:-----|:----:|
| 1 | Release Notes | `docs/releases/AI-COMPANY-CONTROL-CENTER-v0.1.1.md` | ✅ 已创建 |
| 2 | Build Log | `docs/build-logs/2026-05-21-control-center-v0.1.1.md` | ✅ 已创建 |
| 3 | Dashboard Screenshot | `docs/assets/screenshots/v0.1.1-dashboard.png` | ✅ 已截取 |
| 4 | Agents Screenshot | `docs/assets/screenshots/v0.1.1-agents.png` | ✅ 已截取 |
| 5 | Runs Screenshot | `docs/assets/screenshots/v0.1.1-runs.png` | ✅ 已截取 |
| 6 | Command Center Alpha Screenshot | `docs/assets/screenshots/v0.1.1-command-center-alpha.png` | ✅ 已截取 |
| 7 | README Updated | `README.md` (v0.1.1 状态块 + Releases 表 + Screenshots) | ✅ 已更新 |
| 8 | Roadmap Updated | `docs/AI-COMPANY-OS-ROADMAP.md` (v0.1.1 标记完成) | ✅ 已更新 |

---

## 📊 系统实时数据（取报告时刻）

### API 健康检查

```json
GET /api/v1/health
→ {"status": "ok", "app": "AI Company Control Center", "version": "0.1.1"}
```

### 总览统计

| 指标 | 值 |
|:-----|:----|
| Agent 总数 | 18 |
| 在线 Agent | 15 |
| 离线 Agent | 3 |
| 业务线 | 5（3 运行中, 1 异常） |
| 累计执行 | 14 |
| 失败执行 | 0 |
| 未解决告警 | 6 |
| 本月成本 | $0.00 |
| 总成本 (历史) | $0.0102 |

### 真实执行记录 (14 条)

```
scheduler-2026-04-22  | passed | 2026-04-22
test-run-v1           | passed | 2026-04-18
test-run-legacy       | passed | 2026-04-18
obs-1-deterministic   | passed | 2026-04-18
obs-2-deterministic   | passed | 2026-04-18
obs-3-deterministic   | passed | 2026-04-18
test-memory-writeback | passed | 2026-04-18
test-memory-recall-2  | passed | 2026-04-18
run-1-novel           | passed | 2026-04-18
run-2-novel           | passed | 2026-04-18
run-4-novel           | passed | 2026-04-18
test-flow-001         | passed | 2026-04-17
option-b-test-001     | passed | 2026-04-17
scheduler-2026-05-01  | passed | 2026-04-17
```

**来源**: `production-flow-ledger.json` (OpenClaw runtime)  
**通过率**: 14/14 = 100%

### 真实成本 (6 Agents, 19 calls)

| Agent | Calls | Cost (USD) | Avg/Call |
|:------|:-----:|:----------:|:--------:|
| story-editor | 6 | $0.00508 | $0.00085 |
| research-agent | 4 | $0.00150 | $0.00038 |
| finance-analyst | 3 | $0.00114 | $0.00038 |
| writer | 2 | $0.00086 | $0.00043 |
| lead-novel | 2 | $0.00082 | $0.00041 |
| review-editor | 2 | $0.00080 | $0.00040 |

**来源**: `gateway-lite/cost-view/by-agent.json`

### 真实告警 (6 条未解决)

| 级别 | 标题 | 原因 |
|:----:|:-----|:-----|
| 🔴 error | 外围市场动态-周末 执行失败 | 连续 3 次报错 |
| 🟡 warning | 金融摘要-交易日早间 执行失败 | Message failed |
| 🟡 warning | 亚马逊选品报告-周五 执行失败 | AxiosError 400 |
| 🟡 warning | 亚马逊选品报告-周二 执行失败 | AxiosError 400 |
| 🔴 error | 金融投资摘要 执行失败 | 连续 7 次报错 |
| 🟡 warning | 亚马逊选品报告 执行失败 | delivery failed |

**来源**: Alert Detector 自动扫描 cron error

### Command 安全验证

| 请求 | 模式 | 结果 |
|:-----|:----:|:----:|
| `POST /api/v1/command` | `dry-run` | ✅ 返回分析不执行 |
| `POST /api/v1/command` | `execute` (ALLOW_ALPHA_WRITE=false) | ✅ 403 Forbidden |

---

## ✅ P0 验收 (8/8)

| # | 检查项 | 结果 |
|:-:|:-------|:----:|
| 1 | GET /api/v1/runs → 真实数据 | ✅ 14 条 real |
| 2 | GET /api/v1/costs → 真实数据 | ✅ 19 条 real |
| 3 | GET /api/v1/alerts → 真实数据 | ✅ 6 条 real |
| 4 | Agent 三维状态 | ✅ discovery/activity/health |
| 5 | Refresh 不污染 mock | ✅ 先清后写 |
| 6 | Command 默认 dry-run | ✅ status=dry-run |
| 7 | ALLOW_ALPHA_WRITE=false 拒执行 | ✅ 403 |
| 8 | command_logs 记录 | ✅ 4 条记录 |

## ✅ P1 完成

| 模块 | 状态 |
|:-----|:----:|
| Agent 前端 3D Badge | ✅ |
| 写端点 Safety Gate (3 个) | ✅ |
| command_logs 全覆盖 | ✅ |
| 前端 Alpha 标识 | ✅ |
| Stable Core / Alpha 分层 | ✅ |

---

## 📂 文件变更清单

```
ai-company-os/
├── README.md                                    ← 更新：v0.1.1 状态块 + Releases + Screenshots
├── AI-COMPANY-CONTROL-CENTER-v0.1.1-RELEASE-EVIDENCE-SUMMARY.md  ← 新增（本文）
├── docs/
│   ├── AI-COMPANY-OS-ROADMAP.md                 ← 更新：v0.1.1 标记完成
│   ├── releases/
│   │   └── AI-COMPANY-CONTROL-CENTER-v0.1.1.md  ← 新增 Release Notes
│   ├── build-logs/
│   │   └── 2026-05-21-control-center-v0.1.1.md  ← 新增 Build Log
│   └── assets/
│       └── screenshots/
│           ├── v0.1.1-dashboard.png             ← 新增
│           ├── v0.1.1-agents.png                ← 新增
│           ├── v0.1.1-runs.png                  ← 新增
│           └── v0.1.1-command-center-alpha.png  ← 新增
```

---

## 🔮 下一步

| 版本 | 范围 | 状态 |
|:-----|:-----|:----:|
| v0.1.2 / P2-lite | 成本数据修复 + 对话上下文感知 + artifact 修复 | 候选，未排期 |
| v0.2 | TASK-POOL + Approval Center | 待 Founder 决策 |
| v0.3+ | CEO Agent → Memory 4 层 → Agent 会议 → 多 Runtime | 远期 |

---

> **v0.1.1 的核心信息：**
> 
> 从一个 "看起来有数据的演示" 变成了一个 "只说真话的运营工具"。
> 
> 这个版本的每一个数字都可以被验证。这不是终点，而是起点。
