# AI Company OS — 分阶段任务卡

> **说明：** 按 Phase 分拆的可执行任务卡片。每个 Task 标注预估工时、前置依赖、完成标准。
> **Phase 0-4 已完成**，以下是 **v0.2（Phase 5+）** 的任务卡。

---

## Phase 5 — 指挥台（Command Center）

**周期：** ~3 天
**依赖：** Phase 3（OpenClaw Adapter 数据源就绪）
**核心交付：** 给 Agent 发指令的能力

---

### Task 5.1：tasks + task_messages 表

**前置：** 无
**工时：** 0.5 天
**完成标准：** 两张 SQLAlchemy 表已定义，初始迁移已执行

**tasks 表结构：**
```sql
id:          UUID, PK
agent_id:    string, FK → agents.id
agent_name:  string
action:      string           -- "write_article", "analyze", ...
params:      JSON              -- 指令参数
required_skills: JSON          -- ["creative-writing", "fact-checking"]  ← 新增
success_criteria: string       -- "文章 > 2000字，3个来源"  ← 新增
status:      enum(pending, in_progress, completed, failed, cancelled)
result:      string, nullable
failure_reason: string, nullable  -- 失败原因  ← 新增
cost_usd:    float, default 0
created_at:  datetime
completed_at: datetime, nullable
```

**task_messages 表结构：**
```sql
id:          UUID, PK
task_id:     UUID, FK → tasks.id
role:        enum(user, agent)
content:     text
created_at:  datetime
```

---

### Task 5.2：Command API（后端）

**前置：** Task 5.1
**工时：** 0.5 天
**完成标准：** 以下 API 端点已实现并返回 200

| 方法 | 路径 | 说明 |
|:----|:-----|:-----|
| POST | `/api/v1/tasks` | 创建任务 |
| GET | `/api/v1/tasks` | 任务列表（支持 status 筛选） |
| GET | `/api/v1/tasks/:id` | 任务详情 + 消息历史 |
| POST | `/api/v1/tasks/:id/messages` | 追加消息 |

**POST /api/v1/tasks 请求体示例：**
```json
{
  "agent_id": "content-manager",
  "action": "write_article",
  "params": { "topic": "ACOS 优化实践" },
  "required_skills": ["creative-writing", "fact-checking"],
  "success_criteria": "文章 > 2000字，至少3个外部来源，可读性 > 60"
}
```

---

### Task 5.3：指挥台前端页面

**前置：** Task 5.2
**工时：** 1 天
**完成标准：** `/command` 页面可交互

**页面元素：**
- Agent 下拉选择器（从 `/api/v1/agents` 动态加载）
- 指令输入框
- 所需技能标签输入（自由输入 + 从现有技能自动补全）
- 验收标准输入框
- 发送按钮（POST → 跳转到任务详情）
- 对话历史面板（加载最近 N 条消息）
- 当 `required_skills` 中的技能匹配 Agent 数为 0 时，弹出 ⚠️ 提示

---

### Task 5.4：Agents 表加 skills 字段

**前置：** 无
**工时：** 0.25 天
**完成标准：** agents 表新增 `skills: JSON` 字段 + PATCH API

**改动：**
```python
# models.py
skills = Column(JSON, default=list)

# routers/agents.py
@router.patch("/api/v1/agents/{name}")
async def update_agent_skills(name: str, skills: list[str]):
    ...
```

**PATCH /api/v1/agents/content-manager 请求体：**
```json
{
  "skills": ["creative-writing", "editing", "fact-checking", "translation"]
}
```

---

### Task 5.5：任务执行跟踪

**前置：** Task 5.2
**工时：** 0.75 天
**完成标准：** 发出的任务能显示"执行中"状态变化

**实现方式（二选一，PRD 记录为开放问题）：**
- 方案 A：Mock — 创建任务后状态按固定时间线自动流转（pending → 5s → running → 10s → completed）
- 方案 B：调 Hermes CLI `hermes chat -q "指令"` 并解析 stdout

**推荐：** 先方案 A（mock），Phase 6 后升级到方案 B

---

## Phase 6 — 任务看板（Task Board）

**周期：** ~2 天
**依赖：** Phase 5
**核心交付：** 所有任务的执行状态可视化看板

---

### Task 6.1：看板组件

**前置：** Task 5.2
**工时：** 0.5 天
**完成标准：** 三列看板（待处理 / 进行中 / 已完成）可渲染

**列逻辑：**
- 待处理：status=pending
- 进行中：status=in_progress
- 已完成：status=completed + failed + cancelled

---

### Task 6.2：任务卡片

**前置：** Task 6.1
**工时：** 0.5 天
**完成标准：** 每张卡片展示完整任务信息

**卡片内容：**
- 图标 + Agent 名称（如 `📝 content-manager`）
- 任务标题 / 简短 action 描述
- 状态徽章（进行中/成功/失败）
- **验收标准展示** — `success_criteria` 字段内容
- 创建时间 + 耗时
- 执行成本（如果有）

---

### Task 6.3：失败原因分析卡片 ← 新增

**前置：** Task 6.2
**工时：** 0.5 天
**完成标准：** 每个失败任务可展开显示原因 + 建议

**展开视图：**
```
❌ amazon-seller · 2小时前
   更新 Listing
   
🔍 失败原因分析:
   ├─ 原因: API 限频（rate limit exceeded）
   ├─ 影响: Listing 未更新，搜索排名可能下降
   └─ 建议: 等待 15 分钟后重试，或降低更新频率

[重试] [忽略]
```

**数据来源：** `execution_records.failure_reason` + 人工/Agent 回填

---

### Task 6.4：筛选、排序、搜索

**前置：** Task 6.2
**工时：** 0.5 天
**完成标准：** 可按状态、Agent、日期范围筛选

**筛选器：**
- 状态：全部 / 进行中 / 成功 / 失败（按钮组）
- Agent：下拉选择
- 日期范围：日期选择器
- 关键字搜索：标题/指令内容

---

## Phase 6.5 — 技能地图（Skill Map）← 新增

**周期：** ~1 天
**依赖：** Phase 5（Agents 表 skills 字段）
**核心交付：** 全公司技能覆盖视图 + Token 趋势图

---

### Task 6.5.1：技能聚合 API

**前置：** Task 5.4
**工时：** 0.25 天
**完成标准：** GET /api/v1/skills 返回技能覆盖数据

```json
GET /api/v1/skills
{
  "skills": [
    { "name": "creative-writing", "agent_count": 3, "agents": ["content-manager", "writer", "story-editor"] },
    { "name": "data-analysis",    "agent_count": 2, "agents": ["finance-analyst", "research-agent"] },
    { "name": "translation",      "agent_count": 0, "agents": [] },
    { "name": "design",           "agent_count": 1, "agents": ["lead-sticker"] }
  ],
  "total_gaps": 2,
  "gap_skills": ["translation", "legal-compliance"]
}
```

---

### Task 6.5.2：Token 趋势 API

**前置：** 无（数据已存在 cost_snapshots 表）
**工时：** 0.25 天
**完成标准：** GET /api/v1/costs/trend 返回时序数据

```json
GET /api/v1/costs/trend?days=7
{
  "trend": [
    { "date": "2026-05-14", "total_usd": 0.0012, "by_agent": { "content-manager": 0.0008, "research-agent": 0.0004 } },
    { "date": "2026-05-15", "total_usd": 0.0015, "by_agent": { ... } },
    ...
  ],
  "total_7d": 0.0098,
  "avg_daily": 0.0014
}
```

---

### Task 6.5.3：技能地图前端页面

**前置：** Task 6.5.1
**工时：** 0.5 天
**完成标准：** `/skills` 页面可查看技能覆盖热力图

**页面元素：**
- 技能列表，每行一个技能 + Agent 数量圆点/进度条
- 颜色编码：🟢 ≥2 Agent / 🟡 =1 Agent / 🔴 =0 Agent
- 整体覆盖率百分比（如 "62% 技能已覆盖"）
- 缺口技能列表（红色突出）
- 点击技能行展开对应 Agent 列表 + 链接跳转

**缺口提示集成：** 在指挥台页面（Task 5.3），当用户输入的 `required_skills` 中有技能在技能地图中匹配数为 0 时，显示：
```
⚠️ "翻译"技能当前无 Agent 覆盖
💡 建议添加 Traducto Agent 或使用 DeepL API
```

---

### Task 6.5.4：总览页 Token 趋势图

**前置：** Task 6.5.2
**工时：** 0.5 天
**完成标准：** 总览页 `/` 顶部新增折线图

**实现：**
- 使用原生 SVG 或轻量图表库（recharts / chart.js）
- 替换当前静态成本数字：`$0.00498/month` → 折线图
- X 轴：日期，Y 轴：USD
- 可点击切换到"按 Agent"分组视图
- 显示 7 天 / 30 天切换

---

## Phase 7 — 闭环反馈（v0.3，规划中）

**周期：** 待定
**核心理念（来自 YC Tom Blomfield 演讲）：**

> "我们在顶层加了一个监控 Agent，观察每一次查询，看到失败时自动分析原因、写代码修复、提交 PR、合并部署。第二天人类再问同样的问题，已经好了。"

**规划功能：**
- 失败任务自动重试（可配置重试次数）
- 失败原因聚类分析 → 系统知道什么类型的任务经常失败
- 技能缺口自动提醒 → 某个技能缺口出现 N 次后推荐新 Agent
- 学习机制 → 系统记录每次修复方式，下次类似问题优先采用

---

## 总工期估算

| Phase | 天数 | 说明 |
|:------|:-----|:-----|
| Phase 5 | 3 天 | 指挥台（含 skills 字段） |
| Phase 6 | 2.5 天 | 任务看板（含失败分析） |
| Phase 6.5 | 1.5 天 | 技能地图 + Token 趋势 |
| **合计** | **~7 天** | |

> 注：Phase 6.5 与 Phase 6 部分并行（前端不同页面，可独立开发）
