# v0.2 Company Loop MVP — 执行计划

> **基于**: `docs/prd/AI-COMPANY-CONTROL-CENTER-v0.2-COMPANY-LOOP-MVP-PRD.md`
> **预估**: 14-18h（约 2-3 天）
> **顺序**: 数据层优先 → API 层 → 前端层 → 冷启动链路 → 验收
> **工具**: Codex CLI（主开发工具）、Hermes（架构/文档/验收）

---

## 总体原则

- Day 1：离线开发（后端 + 前端独立），不需要系统运行
- Day 2：联调 + 冷启动 + 验收，需要后端运行
- 验收标准只有一条：**一条真实告警完整走通闭环**
- 不优雅但可用（版本优先，重构后置）

---

## 执行顺序

### Day 1：数据层 + API 层（预估 8-10h）

**顺序原则：从底层往上。先搭数据骨架，再盖 API 层。**

#### 第 1 步：task_pool 模型（1h）

| 工作项 | 说明 |
|:-------|:------|
| 创建 `backend/app/models/task_pool.py` | 新 model，不沿用旧 tasks 表 |
| 字段 | 参考 PRD `task_pool` schema |
| 预留字段 | `execution_runtime`, `execution_mode`, `execution_workspace` |
| 状态机 | 实现状态校验：`draft → ready → approval_required → approved → running → review → done` |
| 外键 | `context_pack_id` 暂不设严格 FK（先 nullable），`department`/`project_id` 后置 |
| 迁移 | 旧 `tasks` 表不动（Phase 5 指挥台在用），新 `task_pool` 表独立 |

**验收**：`python3 -c "from app.models.task_pool import TaskPool; print('OK')"`

#### 第 2 步：context_packs 模型（0.5h）

| 工作项 | 说明 |
|:-------|:------|
| 创建 `backend/app/models/context_pack.py` | 新 model |
| 关键字段 | `referenced_knowledge`（JSON, 知识库引用） |
| | `auto_generated`（系统生成标记） |
| 关系 | `task_id` → task_pool.id |

**验收**：`python3 -c "from app.models.context_pack import ContextPack; print('OK')"`

#### 第 3 步：approvals 模型（0.5h）

| 工作项 | 说明 |
|:-------|:------|
| 创建 `backend/app/models/approval.py` | 新 model |
| 多人审批设计 | `target_type`（task/command/learning_candidate）+ `target_id` |
| 决策字段 | `founder_decision`, `founder_notes`, `decision_context` |
| 状态 | `approval_requested → approved/rejected/expired → executed/cancelled` |

**验收**：`python3 -c "from app.models.approval import Approval; print('OK')"`

#### 第 4 步：reviews 模型（0.5h）

| 工作项 | 说明 |
|:-------|:------|
| 创建 `backend/app/models/review.py` | 新 model |
| 三态 | `result: pass / revision_required / blocked` |
| 关联 | `artifact_id` 链接到产物 |

**验收**：`python3 -c "from app.models.review import Review; print('OK')"`

#### 第 5 步：learning_candidates 模型（0.5h）

| 工作项 | 说明 |
|:-------|:------|
| 创建 `backend/app/models/learning_candidate.py` | 新 model |
| 类型 | `source_type: failure / tool_gap / context_update / rule_update / asset_candidate` |
| 审批 | `approval_status: pending_approval / approved / rejected / approved_for_knowledge_update` |

**验收**：`python3 -c "from app.models.learning_candidate import LearningCandidate; print('OK')"`

#### 第 6 步：注册 5 个新 model 到 database.py（0.5h）

- 全部 5 个 model 导入 `app/database.py` 的 `__init__` 或确保 `init_db()` 创建表
- 执行 `python3 -m app.main` 验证 5 张新表自动创建

**验收**：`sqlite3 backend/data/ai_company_os.db ".tables" | grep -E "task_pool|context_pack|approval|review|learning_candidate"`

#### 第 7 步：TASK-POOL CRUD API（2h）

| 端点 | 方法 | 功能 |
|:-----|:----:|:------|
| `/api/v1/task-pool` | GET | 列表（支持 status/business_line/source/assigned_agent 筛选） |
| `/api/v1/task-pool` | POST | 创建（含 `requires_approval` 默认 true） |
| `/api/v1/task-pool/{id}` | GET | 详情（含 Context Pack + Approval + Review 关联） |
| `/api/v1/task-pool/{id}` | PATCH | 更新状态（带状态机校验） |

**关键实现点**：
- GET list 支持 `?status=approval_required&business_line=amazon`
- PATCH status 做状态机校验：`draft→ready` 允许，但 `running→draft` 拒绝
- POST 时若 `source=alert` 且 `source_id` 已存在则报重复

**验收**：`curl -s .../task-pool | python3 -m json.tool`

#### 第 8 步：Context Pack API（1h）

| 端点 | 方法 | 功能 |
|:-----|:----:|:------|
| `/api/v1/task-pool/{id}/context-pack` | GET | 获取 Context Pack |
| `/api/v1/task-pool/{id}/context-pack` | POST | 创建/更新（upsert） |

**关键实现点**：
- POST 时若已存在则 PATCH（1:1 关系）
- `referenced_knowledge` 存 JSON 格式

**验收**：`curl -s .../context-pack | python3 -c "..."`

#### 第 9 步：Approval API（1h）

| 端点 | 方法 | 功能 |
|:-----|:----:|:------|
| `/api/v1/approvals` | GET | 待审批列表（支持 filter pending 的） |
| `/api/v1/approvals` | POST | 创建审批申请 |
| `/api/v1/approvals/{id}/decide` | PATCH | Founder 决策 |

**关键实现点**：
- `decide` 操作接收 `decision` + `notes` 参数
- 决策后同步更新 `target_id` 对应的主状态（如 Task 状态流转）

**验收**：创建一个 approval → decide → 检查 task 状态变化

#### 第 10 步：Review API（1h）

| 端点 | 方法 | 功能 |
|:-----|:----:|:------|
| `/api/v1/reviews` | POST | 提交 Review |
| `/api/v1/reviews/{id}` | GET | Review 详情 |

**关键实现点**：
- 提交 Review 时同步更新 Task 状态（review → done / revision_required / blocked）
- `revision_required` 时自动更新 Task 状态回 `approval_required`

**验收**：提交 review → 检查 task 状态变更

#### 第 11 步：Learning Candidate API（1h）

| 端点 | 方法 | 功能 |
|:-----|:----:|:------|
| `/api/v1/learning-candidates` | GET | 列表（支持 status 筛选） |
| `/api/v1/learning-candidates` | POST | 创建 |
| `/api/v1/learning-candidates/{id}/decide` | PATCH | Founder 审批 |

**关键实现点**：
- POST 时可自动从 task 的 `failure_reason` / review notes 生成候选内容
- `decide` 同步更新 `approval_status`

**验收**：创建 candidate → decide → 检查状态

#### 第 12 步：Loop Dashboard API（0.5h）

| 端点 | 方法 | 功能 |
|:-----|:----:|:------|
| `/api/v1/loop-stats` | GET | 闭环指标 |

**响应结构**：
```json
{
  "total_tasks": 12,
  "pending_approvals": 3,
  "completed_loops": 5,
  "review_pass_rate": 0.8,
  "review_revision_rate": 0.15,
  "review_blocked_rate": 0.05,
  "learning_candidates": 4,
  "approved_candidates": 2,
  "alert_to_pool_count": 6,
  "avg_cycle_time_hours": 4.5
}
```

**验收**：GET /loop-stats 返回合理指标

---

### Day 2：前端 + 冷启动 + 验收（预估 6-8h）

#### 第 13 步：前端 TASK-POOL 页面（2h）

- 升级现有 `/tasks` 页面为 TASK-POOL 风格
- 展示：状态颜色标签、来源图标、风险标记、审批状态
- 筛选器：status / business_line / source
- 空状态："系统正在监听告警..."

#### 第 14 步：前端 Task Detail 页面（2h）

- 新页面 `/tasks/[id]`
- 展示：任务基本信息 + Context Pack 面板 + Approval 面板 + Review 面板
- Context Pack：可展开/收起，引用知识库页面链接
- 操作按钮：提交审批 → 执行（跳转 Command Center） → 提交 Review

#### 第 15 步：前端 Approval Center 页面（1.5h）

- 新页面 `/approvals`
- 展示：待审批任务列表 + 已决历史
- 每项：来源、风险等级、系统建议、关联信息
- 操作：Approve / Revise（带输入框） / Reject / Defer

#### 第 16 步：前端 Loop Dashboard 页面（1h）

- 新页面 `/loop`
- 展示：4 个核心指标卡片 + 简版趋势图 + 瓶颈提示

#### 第 17 步：冷启动链路实现（2h）

**在 `refresh_orchestrator.py` 中新增步骤：**

```
refresh 完成后 → alert_to_pool 步骤:

for each unresolved alert (resolved=0):
  1. 检查 task_pool 是否已有 source_id = alert.id 的记录
  2. 若无，自动创建 Task (status=approval_required)
  3. 自动创建 Context Pack (auto_generated=true)
  4. 自动创建 Approval (status=approval_requested)
  5. 标记 alert.resolved = 2（已入池）
```

**迁移脚本**（一次性）：
- 已有的 6 个 unresolved alerts → 执行上述逻辑
- 已有的 14 条 execution_records → 创建对应的 review 数据

#### 第 18 步：验收（1h）

**运行完整验收脚本**：

```
1. 启动 backend
2. POST /api/v1/refresh（触发 alert 自动入池）
3. GET /api/v1/task-pool?status=approval_required（应有 >= 1 条自动生成的 task）
4. GET /api/v1/task-pool/{id}/context-pack（检查 Context Pack 内容）
5. GET /api/v1/approvals（待审批列表）
6. PATCH /api/v1/approvals/{id}/decide（approve）
7. 验证 task 状态变为 approved
8. POST /api/v1/reviews（提交 review）
9. 验证 task 状态变为 done / revision_required
10. POST /api/v1/learning-candidates（生成 candidate）
11. GET /api/v1/learning-candidates（验证生成了候选）
12. GET /api/v1/loop-stats（验证闭环指标）
```

---

## 文件清单

### 新建文件

```
backend/
├── app/models/task_pool.py           ← 新 model
├── app/models/context_pack.py        ← 新 model
├── app/models/approval.py            ← 新 model
├── app/models/review.py              ← 新 model
├── app/models/learning_candidate.py  ← 新 model
└── app/routers/task_pool.py          ← 新 router（含 context pack / approval / review / learning）

frontend/src/
└── app/
    ├── tasks/page.tsx                ← 升级
    ├── tasks/[id]/page.tsx           ← 新页面
    ├── approvals/page.tsx            ← 新页面
    └── loop/page.tsx                 ← 新页面

docs/
└── prd/AI-COMPANY-CONTROL-CENTER-v0.2-COMPANY-LOOP-MVP-PRD.md ← 已完成
```

### 修改文件

```
backend/
├── app/routers/__init__.py           ← 注册新 router
├── app/refresh_orchestrator.py       ← 增加 alert_to_pool 步骤
├── app/database.py                   ← 注册 5 个新 model（若需要）
└── app/models/__init__.py            ← 导出新 model
```

---

## 风险点

| 风险 | 概率 | 影响 | 缓解 |
|:-----|:----:|:-----|:------|
| 旧 tasks 表和新 task_pool 表关系混乱 | 中 | 中 | 旧表不动，新表独立，指挥台仍用旧表 |
| 自动入池逻辑堵塞 refresh 流程 | 低 | 中 | 设 `ALERT_TO_POOL_MAX=5` 限制单次入池数量 |
| 前端 4 个新页面开发耗时超预期 | 中 | 低 | 优先完成 TASK-POOL 和 Approval Center，Loop Dashboard 可降级为简单指标卡片 |
| 验收时 Alert 数据被 refresh 覆盖 | 低 | 中 | 自动入池后标记 `resolved=2`，不影响原始 alert 数据 |

---

## 验收检查清单

```
[ ] Day 1 全部完成
    [ ] 5 张新 model 创建 + database.py 注册 + 自动建表
    [ ] TASK-POOL CRUD API（4 端点）
    [ ] Context Pack API（2 端点）
    [ ] Approval API（3 端点）
    [ ] Review API（2 端点）
    [ ] Learning Candidate API（3 端点）
    [ ] Loop Dashboard API（1 端点）

[ ] Day 2 全部完成
    [ ] TASK-POOL 前端页面
    [ ] Task Detail 前端页面
    [ ] Approval Center 前端页面
    [ ] Loop Dashboard 前端页面
    [ ] Alert 自动入池逻辑
    [ ] 已有数据迁移

[ ] 验收链路
    [ ] Alert → Task（自动入池）
    [ ] Task → Context Pack
    [ ] Approval Center（approve/revise/reject/defer）
    [ ] Command Center 执行（dry-run + execute）
    [ ] Review（PASS / REVISION / BLOCKED）
    [ ] Learning Candidate 生成 + 审批
    [ ] Loop Dashboard 指标正常
```

---

> **执行人**: Codex CLI（主要开发）+ Hermes（架构验收）  
> **单人 Founder 原则**: 如果某一步阻塞超过 30 分钟，降级为最小可用版本
