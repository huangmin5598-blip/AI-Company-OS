# v0.3 CEO Agent Lite — 执行计划

> **基于 PRD** `AI-COMPANY-CONTROL-CENTER-v0.3-CEO-AGENT-LITE-PRD.md`
> **预估工时**: 12-16h（约 2 天冲刺）
> **执行顺序**: Day 1（后端 + Schema）→ Day 2（Hermes CEO Skill + 前端 + 验收）

---

## 执行概览

```
Day 1 (6-8h)
├── 2 张新表: goal_sessions + ceo_action_logs
├── 5 个新端点: goal_sessions CRUD + commit-decomposition + action-logs
├── CEO Skill Schema 定义（Python 常量 + 类型校验）
└── v0.2 端点验证（确认 Hermes 可调用）

Day 2 (6-8h)
├── Hermes CEO Skill（goal decomposition + approval action）
├── 3 个前端页面: CEO Console / Goal Sessions / Action Logs
├── Task Detail 补充"Created by CEO"信息
├── 冷启动：无（v0.3 不需要数据迁移）
└── 验收：双闭环走通
```

---

## Day 1：后端 + Schema

### Step 1: 创建 goal_sessions 模型

文件: `backend/app/models/goal_session.py`

```python
from sqlalchemy import Column, String, Integer, Float, Text, DateTime
from sqlalchemy.sql import func
from app.models.base import Base

class GoalSession(Base):
    __tablename__ = "goal_sessions"

    id = Column(Integer, primary_key=True)
    source_channel = Column(String, default="cc_panel")  # cc_panel / feishu
    raw_goal = Column(Text, nullable=False)
    interpreted_goal = Column(String, nullable=True)
    goal_type = Column(String, nullable=True)      # repair / growth / research / build / review / ops
    business_line = Column(String, nullable=True)
    priority = Column(String, default="medium")
    risk_level = Column(String, default="medium")
    status = Column(String, default="draft")        # draft / decomposed / committed / cancelled / failed
    decomposition_json = Column(Text, nullable=True)
    task_ids_json = Column(Text, nullable=True)     # JSON array
    approval_ids_json = Column(Text, nullable=True) # JSON array
    model_used = Column(String, nullable=True)
    confidence = Column(Float, nullable=True)
    schema_version = Column(String, default="v0.3.0")
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
```

### Step 2: 创建 ceo_action_logs 模型

文件: `backend/app/models/ceo_action_log.py`

```python
from sqlalchemy import Column, String, Integer, Float, Text, Boolean, DateTime
from sqlalchemy.sql import func
from app.models.base import Base

class CeoActionLog(Base):
    __tablename__ = "ceo_action_logs"

    id = Column(Integer, primary_key=True)
    source_channel = Column(String, default="cc_panel")
    raw_user_message = Column(Text, nullable=False)
    intent_type = Column(String, nullable=False)    # goal_intake / approval_action
    target_type = Column(String, nullable=True)     # goal_session / task / approval / learning_candidate
    target_id = Column(Integer, nullable=True)
    action_taken = Column(String, nullable=True)    # decomposed / approved / rejected / ...
    payload_json = Column(Text, nullable=True)
    result_status = Column(String, default="success")  # success / failed / ambiguous / cancelled
    result_summary = Column(Text, nullable=True)
    confidence = Column(Float, nullable=True)
    requires_confirmation = Column(Boolean, default=False)
    confirmed_by_founder = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
```

### Step 3: 注册到 models/__init__.py

```python
from app.models.goal_session import GoalSession
from app.models.ceo_action_log import CeoActionLog
```

### Step 4: 创建 Pydantic Schemas

文件:
- `backend/app/schemas/goal_session.py`
- `backend/app/schemas/ceo_action_log.py`
- `backend/app/schemas/decomposition.py` — commit-decomposition 的 request/response schema

### Step 5: 创建 Router — goal_sessions

文件: `backend/app/routers/goal_sessions.py`

端点:
- `GET /api/v1/ceo/goal-sessions` — 列表（按 status/source_channel 筛选）
- `POST /api/v1/ceo/goal-sessions` — 创建
- `GET /api/v1/ceo/goal-sessions/{id}` — 详情

### Step 6: 创建 Router — ceo_action_logs

文件: `backend/app/routers/ceo_action_logs.py`

端点:
- `GET /api/v1/ceo/action-logs` — 列表（按 intent_type/target_type 筛选）
- `POST /api/v1/ceo/action-logs` — 创建

### Step 7: 创建 Router — commit-decomposition

文件: `backend/app/routers/ceo_commit.py`

端点:
- `POST /api/v1/ceo/commit-decomposition`

逻辑（原子事务，失败全回滚）:
1. 接收 Hermes 的结构化 goal decomposition JSON
2. 创建 goal_session（status=committed）
3. 遍历 tasks 数组，为每条创建 task_pool（status=approval_required）
4. 为每条 task 创建 context_pack（auto_generated=True）
5. 为每条 task 创建 approval
6. 写入 ceo_action_logs
7. 返回: { goal_session_id, task_ids[], approval_ids[], status }

错误处理:
- 任一创建失败 → 全部回滚
- 返回 error_message 和 status=failed

### Step 8: 注册到 routers/__init__.py

### Step 9: 定义 CEO Skill Schema（Python 常量 + 校验）

文件: `backend/app/ceo/schema_definitions.py`

这是给 Hermes 看的 schema 定义 + 给后端做校验用的：

```python
# 目标拆解 schema 版本
GOAL_DECOMPOSITION_SCHEMA_VERSION = "v0.3.0"

# 目标类型
GOAL_TYPES = ["repair", "growth", "research", "build", "review", "ops"]

# task_type
TASK_TYPES = ["diagnosis", "fix", "investigate", "optimize", "build", "review", "monitor"]

# Goal Intake 的 expected JSON schema 说明（用于 skill 文档）
GOAL_INTAKE_SCHEMA_DESCRIPTION = """
{
  "goal_summary": "...",
  "goal_type": "repair|growth|research|build|review|ops",
  "business_line": "...",
  "risk_level": "low|medium|high",
  "confidence": 0.0-1.0,
  "tasks": [
    {
      "title": "...",
      "why": "...",
      "task_type": "diagnosis|fix|investigate|...",
      "assigned_agent": "...",
      "risk_level": "low|medium|high",
      "priority": "low|medium|high|critical",
      "acceptance_criteria": "...",
      "context_pack": {
        "founder_intent": "...",
        "related_sources": ["..."],
        "known_failures": ["..."],
        "constraints": "..."
      }
    }
  ]
}
"""

# Approval Action 的 expected JSON schema
APPROVAL_ACTION_SCHEMA_DESCRIPTION = """
{
  "intent_type": "approval_action",
  "decision": "approved|rejected|revised|deferred",
  "target_type": "approval",
  "target_id": 123,
  "matched_targets_count": 1,
  "confidence": 0.0-1.0,
  "requires_confirmation": true|false,
  "founder_phrase": "..."
}
"""
```

### Step 10: 验证

```
cd backend && python -c "from app.database import init_db; init_db(); print('OK')"
cd backend && python -c "from app.main import app; print(len(app.routes))"
```

---

## Day 2：Hermes Skill + 前端 + 验收

### Step 11: 创建 Hermes CEO Skill

文件: `~/.hermes/skills/ceo-agent/skill.md`（Hermes skill 目录）

Skill 内容包含：

- **触发器**: 用户在对话中表达经营目标或审批意图
- **Goal Decomposition Prompt**: 带 few-shot 示例 + schema 的结构化拆解 prompt
- **Approval Action Prompt**: 带置信度/匹配逻辑的审批解析 prompt
- **安全规则**: confidence ≥ 0.85 + 唯一匹配 → 可执行；否则追问
- **工具集**: 调用 CC API 的 HTTP 工具（或直接 curl）
- **cc_api 工具的配置**: 
  - `POST /api/v1/ceo/commit-decomposition`
  - `GET /api/v1/approvals`
  - `PATCH /api/v1/approvals/{id}/decide`
  - `POST /api/v1/ceo/action-logs`

**注意**: Hermes 需要能调用 HTTP API。如果 Hermes 没有内置 HTTP 工具，需要：
1. 确认现有 tools 是否包含 `web` 工具集
2. 或在 terminal 中使用 curl 封装

### Step 12: CEO Workbench 前端页面

文件: `frontend/src/app/ceo/page.tsx`

v0.3 中 CEO Workbench 是 **工作台**，不是实时聊天入口。实际自然语言对话入口优先为飞书 / Hermes TUI。

- 创建 goal_session draft（简单表单：输入目标摘要 → POST goal_sessions → status=draft）
- 展示最新 goal_sessions 列表（状态标签、创建时间）
- 展示最新 ceo_action_logs
- 快速链接：前往 Approval Center、TASK-POOL

> 不要求 v0.3 实现"前端输入 → 触发 Hermes 推理 → 实时返回"的完整链路。

### Step 13: Goal Sessions 页面

文件: `frontend/src/app/ceo/goals/page.tsx`

- 列表渲染 goal_sessions
- 点击展开拆解结果 JSON
- 状态标签

### Step 14: Action Logs 页面

文件: `frontend/src/app/ceo/logs/page.tsx`

- 列表渲染 ceo_action_logs
- 按 intent_type 筛选
- 显示原始消息、执行结果

### Step 15: Task Detail 补充

在 `task-pool/[id]/page.tsx` 中：
- 检查 task 的 source 是否为 `goal` 或 `ceo`
- 如果是，显示 "Created by CEO Agent" + goal_session_id 链接

### Step 16: 更新 Navbar + Roadmap

- Navbar 添加: CEO（`/ceo`）
- Roadmap 更新: v0.3 → 执行中

### Step 17: 验收

#### 验收 1: Goal Intake

手动测试：
```
1. 构建一个 goal decomposition JSON（模拟 Hermes 输出）
2. 调用 POST /api/v1/ceo/commit-decomposition
3. 验证 goal_sessions 新增 1 条
4. 验证 task_pool 新增 2-5 条
5. 验证 context_packs 新增 2-5 条
6. 验证 approvals 新增 2-5 条
7. 验证 ceo_action_logs 新增 1 条
```

#### 验收 2: Approval Action

```
1. PATCH /api/v1/approvals/{id}/decide（模拟 CEO 调用）
2. 验证 approval 状态更新
3. 验证 ceo_action_logs 新增 1 条
```

---

## 执行顺序总表

```
Day 1 — Backend + Schema (6-8h)
  S1. goal_session.py 模型         (20min)
  S2. ceo_action_log.py 模型        (15min)
  S3. models/__init__.py 更新       (5min)
  S4. Pydantic schemas × 3         (30min)
  S5. goal_sessions router          (30min)
  S6. ceo_action_logs router        (20min)
  S7. commit-decomposition router   (45min)  ← 最复杂，含原子事务
  S8. routers/__init__.py 更新       (5min)
  S9. schema_definitions.py         (20min)
  S10. 验证: init_db + routes       (10min)
  ─────────────────────────────────
  总计: ~3h

Day 2 — Hermes Skill + Frontend + Acceptance (6-8h)
  S11. Hermes CEO Skill             (1.5h)  ← 最核心，需多轮调优
  S12. CEO Console 页面              (45min)
  S13. Goal Sessions 页面            (30min)
  S14. Action Logs 页面              (30min)
  S15. Task Detail 补充              (15min)
  S16. Navbar + Roadmap 更新         (10min)
  S17. 验收                          (1h)
  ─────────────────────────────────
  总计: ~5h
```

---

## 依赖与前置条件

| # | 依赖 | 状态 | 影响 |
|:-:|:-----|:----:|:-----|
| 1 | Hermes 能调 HTTP API (terminal + curl) | ✅ 已验证 | GitHub API 已验证可调 |
| 2 | v0.2 端点在运行 | ✅ | — |
| 3 | 后端 8001 端口可用 | ✅ | — |
| 4 | 前端 3001 端口可用 | ✅ | — |

### ✅ HTTP capability spike 结果

```bash
curl -s http://127.0.0.1:8001/api/v1/health
→ {"status":"ok","app":"AI Company Control Center","version":"0.1.1"}

curl -s http://127.0.0.1:8001/api/v1/approvals | python3 -c "import sys,json; print(len(json.load(sys.stdin)), 'items')"
→ 8 items
```

✅ Hermes 通过 `terminal` + `curl` 可正常调用 CC 后端 API。**不需要 hermes-bridge。**
CEO Skill 中封装为 `cc_api` 脚本或直接内联 curl 命令即可。

---

## 风险

| 风险 | 影响 | 缓解 |
|:-----|:-----|:------|
| Goal decomposition JSON 不稳定 | 任务质量差 | few-shot 示例 + schema 验证 + 重试 |
| Approval Action 误匹配 | 批准错误的任务 | confidence + matched_targets 双阈值 + 候选列表返回 |
| 飞书输入不稳定 | 验收卡住 | MVP 验收不依赖飞书 |
