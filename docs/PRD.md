# AI Company OS — 产品需求文档（PRD）

> **产品名：** AI Company Control Center（Dashboard）
> **系统名：** AI Company OS
> **版本：** v0.2（规划中）
> **最后更新：** 2026-05-20

---

## 1. 产品愿景

一人公司的 AI 操作系统。让创始人通过一个 Dashboard 看到所有 AI Agent 的运行状态、执行结果、成本消耗，并通过指挥台给 Agent 发指令、跟踪任务进展，最终形成"人发指令→Agent 执行→系统反馈→闭环改进"的自动化回路。

## 2. 目标用户

- 单人创业者（一人公司）
- 管理 5-20 个 AI Agent 的小团队
- 需要通过 Dashboard 而非命令行管理 Agent 的用户

## 3. 核心原则

- **只读不写（v0.1）→ 可读写（v0.2 起）**
- **数据永久，软件可丢弃** — 所有业务数据存在 SQLite，前端可随时重生成
- **预留扩展** — Anthropic 兼容字段、agent_type、runtime_id 等已在 schema 中
- **API 优先** — 所有功能通过 REST API 暴露

## 4. 技术栈

| 层 | 技术 | 版本/说明 |
|:---|:-----|:----------|
| 前端 | Next.js + Tailwind CSS | 14+，`--port 3001` |
| 后端 | FastAPI + SQLAlchemy | Python 3.11，`--port 8001` |
| 数据库 | SQLite | 文件 `backend/data/ai_company_os.db` |
| 外网穿透 | Cloudflare Named Tunnel | `ai-company-os.com` → `localhost:3001` |

> ⚠️ Docker Desktop 占用 3000/8000 端口，故使用 3001/8001。

## 5. 数据源（OpenClaw Adapter）

| 数据源 | 类型 | 位置 |
|:-------|:-----|:-----|
| Agent 列表 | CLI | `openclaw agents list` |
| Cron Jobs | JSON | `~/.openclaw/cron/jobs.json` |
| 执行记录 | JSON | `~/.openclaw/workspace/run-ledger/` |
| 生产成本 | JSON | `~/.openclaw/workspace/` |
| 每日成本 | JSON | `~/.openclaw/daily/` |

## 6. 数据库结构（9 张表）

| 表名 | 说明 | v0.2 新增字段 |
|:-----|:-----|:--------------|
| `agents` | Agent 信息 | **`skills: string[]`** |
| `business_lines` | 业务线 | — |
| `cron_jobs` | 定时任务 | — |
| `execution_records` | 执行记录 | **`success_criteria: string`**, **`failure_reason: string`** |
| `artifacts` | 产出物 | — |
| `cost_snapshots` | 成本快照 | — |
| `alerts` | 告警 | — |
| `session_events` | 会话事件 | — |
| `refresh_log` | 刷新日志 | — |
| **`tasks`**（新增） | 指挥台任务 | v0.2 Phase 5 |
| **`task_messages`**（新增） | 任务对话 | v0.2 Phase 5 |

## 7. API 端点

### v0.1 已有（15 个）

```
GET    /api/v1/stats
GET    /api/v1/agents
GET    /api/v1/agents/:name
GET    /api/v1/business-lines
GET    /api/v1/business-lines/:id/runs
GET    /api/v1/runs
GET    /api/v1/runs/:id
GET    /api/v1/costs
GET    /api/v1/cron-jobs
GET    /api/v1/alerts
GET    /api/v1/artifacts
POST   /api/v1/refresh
```

### v0.2 新增（7 个）

```
GET    /api/v1/tasks              # Phase 5 — 任务列表
POST   /api/v1/tasks              # Phase 5 — 创建任务
GET    /api/v1/tasks/:id          # Phase 5 — 任务详情
POST   /api/v1/tasks/:id/messages # Phase 5 — 发送消息
GET    /api/v1/skills             # Phase 6.5 — 技能聚合
PATCH  /api/v1/agents/:name       # Phase 6.5 — 更新 Agent 技能
GET    /api/v1/costs/trend        # 总览页 — Token 趋势
```

---

## 8. v0.1 已完成（回顾）

### Phase 0 — 项目脚手架
- [x] Git 初始化、后端 FastAPI 骨架、前端 Next.js 骨架
- [x] SQLite + SQLAlchemy ORM（9 表）

### Phase 1 — 后端核心
- [x] 15 个 API 端点
- [x] Mock 数据种子
- [x] CORS 配置（允许 3001 端口）

### Phase 2 — 前端 Dashboard
- [x] 3 个页面：总览 / Agents / 执行记录
- [x] Tailwind 暗色主题
- [x] 刷新按钮

### Phase 3 — OpenClaw Adapter
- [x] 5 个适配器：Agent CLI / Cron Jobs JSON / Ledger / Cost / Alert
- [x] 从真实路径同步数据

### Phase 4 — 验收与完善
- [x] 端到端 API 测试（全部 200）
- [x] CORS 修复
- [x] 刷新状态指示
- [x] README

---

## 9. 架构图

```
手机/外网 → https://ai-company-os.com
                    ↓ (Cloudflare Tunnel)
            Mac Mini :3001 (Next.js)
                    ↓ (rewrite /api/v1/*)
            Mac Mini :8001 (FastAPI)
                    ↓
            SQLite (ai_company_os.db)
                    ↓
            OpenClaw 数据源（5 个 Adapter）
```

---

## 10. v0.2 路线图：从监视器到指挥中心

v0.2 的核心升级：

```
┌───────────────────────────────────────────────────┐
│  v0.1（只读监视器）          v0.2（指挥中心）      │
│                                                    │
│  Dashboard 显示 15 个 Agent  │  + 指挥台：发指令    │
│  显示执行历史                │  + 任务看板：跟踪进展  │
│  显示成本、告警、业务线       │  + 技能地图：能力缺口  │
│                              │  + Token 趋势图      │
│  你看到问题，手动去修         │  + 失败原因分析      │
└───────────────────────────────────────────────────┘
```

---

## 11. 总览页升级（v0.2）

### 当前状态
- 静态数字：`15 Agents`, `$0.00498/month`, `30 executions`
- 刷新按钮触发全量同步

### v0.2 升级
- **Token 趋势折线图** — 按天/按 Agent 聚合，数据来源 `cost_snapshots` 表（已有数据）
- **Agent 状态卡片** — 在线/忙碌/错误状态一目了然
- **快速操作入口** — 一键跳转到指挥台发指令

---

## 12. 新增页面设计

### 12.1 指挥台 `/command`（Phase 5）

**用途：** 给特定 Agent 发指令，跟 Agent 对话式交互。

**页面布局：**
```
┌─────────────────────────────────────────┐
│  指挥台                                   │
│  ──────────────────────────────────────  │
│  选择 Agent: [▼ content-manager       ]  │
│  指令内容: [___________________________] │
│  所需技能: [creative-writing, editing ]  │  ← 新增
│  验收标准: [文章 > 2000字, 3个来源   ]  │  ← 新增
│  [发送]                                   │
│  ──────────────────────────────────────  │
│  对话历史:                                 │
│  ┌─ 我 ─────────────────────────────┐    │
│  │ 写一篇关于 ACOS 优化的文章        │    │
│  └──────────────────────────────────┘    │
│  ┌─ content-manager ──────────────┐      │
│  │ 好的，预计需要 5 分钟...       │      │
│  └──────────────────────────────────┘    │
└─────────────────────────────────────────┘
```

**API：**
```json
POST /api/v1/tasks
{
  "agent_id": "content-manager",
  "action": "write_article",
  "params": { "topic": "ACOS 优化" },
  "required_skills": ["creative-writing", "editing", "fact-checking"],
  "success_criteria": "文章 > 2000字，至少引用3个来源"
}
```

### 12.2 任务看板 `/tasks`（Phase 6）

**用途：** 跟踪所有任务的执行状态、结果、耗时、成本。

**页面布局：**
```
┌──────────────────────────────────────────┐
│  📋 任务看板                              │
│  ───────────────────────────────────────  │
│  筛选: [全部] [进行中] [成功] [失败]       │
│                                          │
│  ┌─ 进行中 ──────────────────────────┐   │
│  │ 📝 content-manager · 5分钟前      │   │
│  │   写 ACOS 优化文章                │   │
│  │   验收: 文章>2000字, 3个来源      │   │
│  │   ████████░░ 80%                 │   │
│  ├─ 失败 ───────────────────────────┤   │
│  │ ❌ amazon-seller · 2小时前        │   │
│  │   更新 Listing                    │   │
│  │   🔍 失败原因: API 限频           │   │  ← 新增
│  │   💡 建议: 等待 15 分钟后重试      │   │
│  └──────────────────────────────────┘   │
└──────────────────────────────────────────┘
```

### 12.3 技能地图 `/skills`（Phase 6.5）

**用途：** 查看全公司 Agent 技能覆盖情况，发现能力缺口。

**页面布局：**
```
┌──────────────────────────────────────────┐
│  🧠 技能地图                              │
│  ───────────────────────────────────────  │
│                                          │
│  🟢 写作        3 Agents ● ● ●           │
│  🟢 数据分析     2 Agents ● ●             │
│  🟡 设计         1 Agent  ●              │
│  🔴 翻译         0 Agent                  │ ← 缺口！
│  🟢 研究         3 Agents ● ● ●           │
│  🔴 法律合规     0 Agent                  │ ← 缺口！
│  🟡 视频制作     1 Agent  ●              │
│                                          │
│  ───────────────────────────────────────  │
│  最近 7 天执行的任务技能分布:               │
│  ┌─ 条形图 ────────────────────────┐     │
│  │ 写作      ████████████  12次    │     │
│  │ 研究      ████████      8次     │     │
│  │ 数据分析   ████          4次    │     │
│  │ 翻译      ░░             0次    │     │  ← 缺口
│  └──────────────────────────────────┘     │
└──────────────────────────────────────────┘
```

**技能缺口提示：** 用户在指挥台发指令时，如果 `required_skills` 中有技能的匹配 Agent 数为 0，前端弹出提示：⚠️ "翻译技能当前无 Agent 覆盖，建议添加或使用外部 API"

---

## 13. 分阶段开发计划

| Phase | 名称 | 时间 | 依赖 |
|:------|:-----|:-----|:-----|
| 0-4 | v0.1 基础（已完成） | — | — |
| **5** | **指挥台（Command Center）** | **3 天** | Phase 3 |
| **6** | **任务看板（Task Board）** | **2 天** | Phase 5 |
| **6.5** | **技能地图（Skill Map）** | **1 天** | Phase 5 |
| 7 | 闭环反馈（v0.3） | 规划中 | Phase 6 |

### Phase 5 — 指挥台（3 天）

| Task | 说明 |
|:-----|:-----|
| 5.1 | tasks + task_messages 表 |
| 5.2 | POST /api/v1/tasks + GET /api/v1/tasks |
| 5.3 | 指挥台前端页面（选择 Agent + 输入指令 + 对话历史） |
| 5.4 | agents 表加 `skills` 字段 + PATCH API |
| 5.5 | 任务执行跟踪（Hermes 命令行调用或 mock） |

### Phase 6 — 任务看板（2 天）

| Task | 说明 |
|:-----|:-----|
| 6.1 | 看板前端组件（三列：待处理/进行中/已完成） |
| 6.2 | 任务卡片（标题、Agent、状态、时间、成本、**验收标准**） |
| 6.3 | 任务详情展开 + **失败原因分析卡片** |
| 6.4 | 筛选、排序、搜索 |

### Phase 6.5 — 技能地图（1 天）← 新增

| Task | 说明 |
|:-----|:-----|
| 6.5.1 | GET /api/v1/skills 聚合 API |
| 6.5.2 | GET /api/v1/costs/trend Token 趋势 API |
| 6.5.3 | 技能地图前端页面（热力图 + 缺口标记） |
| 6.5.4 | 总览页 Token 趋势图（折线图组件） |

### Phase 7 — 闭环反馈（v0.3，规划中）

- 自动重试失败任务
- 监控 Agent 分析失败原因并提议修复
- 技能缺口自动建议新 Agent

---

## 14. 非功能性需求

- 响应时间：前端页面加载 < 2s
- 数据刷新：手动触发（当前），后续支持 WebSocket 推送
- 外网访问：Cloudflare Tunnel（`ai-company-os.com`）
- 数据持久性：SQLite 文件，每日自动备份（v0.2 不实现，预留）

---

## 15. 开放问题

1. Phase 5 的"任务执行"——是调 Hermes CLI 还是 mock？
2. 技能数据从哪里来？自动从 OpenClaw workspace 扫描 vs 手动录入？
3. Token 趋势图的粒度是否需要按 Agent 拆分？
