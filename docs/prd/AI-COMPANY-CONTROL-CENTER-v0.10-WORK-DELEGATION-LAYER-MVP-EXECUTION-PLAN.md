# AI Company Control Center v0.10 — Work Delegation Layer MVP 执行计划

> **基于**: v0.10 PRD
> **预估总工时**: 10-14h
> **时间盒**: 2-3 天
> **优先级**: Sprint A（表结构 + Router + CEO Prompt）→ Sprint B（执行回传 + Bridge）→ Sprint C（验收场景）

---

## 文件清单

```
backend/app/
├── models/
│   ├── skill_registry.py        新增：Skill Registry 模型
│   ├── product_line_registry.py  新增：Product Line Registry 模型
│   └── work_order.py            新增：Work Order 模型
├── routers/
│   ├── skill_registry.py        新增：Skill 注册/查询 API
│   ├── product_line_registry.py  新增：产品线 API
│   └── work_orders.py           新增：Work Order CRUD API
├── services/
│   ├── skill_router.py          新增：确定性路由引擎
│   ├── ceo_orchestrator.py      新增：CEO Agent 编排器
│   ├── work_order_executor.py   新增：Work Order 执行器
│   └── openclaw_bridge.py       新增：OpenClaw Bridge
├── ceo/
│   ├── __init__.py              已有
│   └── schema_definitions.py    已有
├── main.py                      已有 — 注册新 router
└── models.py                    已有 — 注册新模型

projects/ai-seller-finance-validation/
├── scripts/
│   └── generate_profit_health_report.py  已有（OP-006）
└── providers/                            已有

~/.hermes/skills/autonomous-ai-agents/
└── ceo-agent/                            新增：CEO Agent skill
    └── SKILL.md
```

---

## Sprint A：Registry + Router + Work Order 基础（4h）

### A-1：Skill Registry 模型 + API + 种子数据（1.5h）

**文件：** `backend/app/models/skill_registry.py`

**字段（13 个）：**
- skill_id PK — research_agent / landing_page_copywriter / landing_page_builder / deployment_assistant / profit_health_report_generator
- name, description, capability_type, owner_agent, owner_runtime, risk_level
- **execution_mode** — direct_delegate / code_bridge / local_script / openclaw_task_card / checklist_only / manual
- input_schema, output_schema, examples, status, created_at, updated_at

**种子数据：** 注册 5 个 Skill，每个标注 execution_mode

**API：** GET/POST/PATCH skills, GET /skills/route?task_type=xxx

**验收：** curl /api/v1/skills/route?task_type=research → research_agent

### A-2：Product Line Registry 模型 + API（30min）

**文件：** `backend/app/models/product_line_registry.py`

**种子数据：** 5 条产品线

### A-3：Work Order 模型 + API + 状态机（2h）

**文件：** `backend/app/models/work_order.py`

**字段（20+ 个）：**
- work_order_id PK, goal_session_id, product_line_id, skill_id
- task_type, route_reason, risk_level, execution_mode
- assigned_agent, runtime_id, input_context, expected_output
- **状态机（9 状态）：** created → routed → assigned → blocked / requires_approval → in_progress → completed / failed / cancelled
- approval_required, approval_id, attempt_count
- output_path, evidence_path, result_summary, error
- **日志字段：** artifacts_json, routing_log_json, execution_log_json
- created_at, assigned_at, completed_at

**API（16 端点）：**
- GET/POST/PATCH skills
- GET/POST/PATCH product-lines
- GET/POST work-orders + /{id}/route + /{id}/execute + /{id}/complete
- POST /ceo/goal-intake + GET /ceo/goal-sessions/{id}

**验收：** 能创建 Work Order，能 route 5 种 task_type，状态转换正确

### A-4：Skill Router 引擎（1.5h）

**文件：** `backend/app/services/skill_router.py`

```python
# 核心函数
TASK_TYPE_TO_CAPABILITY = {
    "research": "research",
    "market_analysis": "research",
    "competitor_analysis": "research",
    "copywriting": "copywriting",
    "landing_page_copy": "copywriting",
    "marketing_copy": "copywriting",
    "code_build": "code_build",
    "landing_page_code": "code_build",
    "feature_implementation": "code_build",
    "report_generation": "report_generation",
    "profit_health_report": "report_generation",
    "deploy": "deploy",
    "deployment_checklist": "deploy",
}

def route(task_type: str, skills: list) -> dict:
    """确定性路由：task_type → capability → skill"""
    ...

def batch_route(tasks: list[dict], skills: list) -> list[dict]:
    """批量路由：输入 [{task_type, task_desc}, ...] → 输出 [{task_type, skill_id, runtime_id, risk_level}, ...]"""
    ...
```

**规则：**
1. 输入 task_type → 映射到 capability_type
2. 查询 skill_registry WHERE capability_type = X AND status = 'active'
3. 返回匹配的 skill 信息
4. 无匹配 → 返回错误（not routed）
5. LLM **不参与**路由过程

**集成到 API：**
- `/api/skills/route?task_type=xxx` 直接调用路由函数

### A-5：CEO Agent Skill（1h）

**文件：** `~/.hermes/skills/autonomous-ai-agents/ceo-agent/SKILL.md`

**系统提示核心内容：**

```markdown
---
name: ceo-agent
description: "CEO Agent — Founder 与 AI Company OS 的唯一对话接口"
version: 0.1.0
author: Hermes Agent
---

# CEO Agent

## 身份
你是 AI Company OS 的 CEO Agent。你代表 Founder 管理整个公司操作系统。

## 职责
1. 接收 Founder 的目标
2. 拆解为子任务列表
3. 每个子任务标注 task_type
4. 调用 Skill Router API (/api/skills/route) 查询能力
5. 生成 Work Orders
6. 分派给对应 Runtime
7. 收集结果
8. 汇总回复

## 行为边界
- 低风险任务可以直接执行
- 代码修改任务必须走 Code Bridge
- 部署类任务只输出 checklist，不自动执行
- 每次决策写入 ceo_action_logs

## 输出格式
- Goal Session: { goal, task_plan, work_orders }
- Work Order: { skill_id, task_type, input_context, expected_output, risk_level }
- Final Summary: { goal_session, results, next_steps, evidence }
```

**注意：** CEO Skill 的加载方式：
- 用户说"开始 CEO 模式"或下达明确目标时加载
- 或通过对话前缀 `/ceo 为利润报告准备销售页` 触发
- 普通对话不加载 CEO Skill，保持 Hermes 原生能力

---

## Sprint B：执行回传 + Bridge（3-5h）

### B-1：Work Order Executor（2h）

**文件：** `backend/app/services/work_order_executor.py`

```python
class WorkOrderExecutor:
    """执行 Work Order 并回填结果"""
    
    def execute(self, work_order_id: str) -> dict:
        """根据 work_order 的 runtime_id 分派执行"""
        ...
    
    def execute_hermes(self, wo) -> dict:
        """通过 delegate_task 派给 Hermes"""
        ...
    
    def execute_codex(self, wo) -> dict:
        """通过 Code Bridge 或 delegate_task(acp_command="codex") 执行"""
        ...
    
    def execute_local(self, wo) -> dict:
        """执行本地脚本（如利润报告生成器）"""
        ...
    
    def execute_openclaw(self, wo) -> dict:
        """生成 task card → 调用 OpenClaw gateway"""
        ...
```

**执行矩阵：**

| runtime_id | 方法 | 文件 |
|:-----------|:-----|:-----|
| hermes | `delegate_task()` | 已有 |
| codex | `delegate_task(acp_command="codex")` | 已有 |
| local | `subprocess.run()` | 新增 |
| openclaw | task card → gateway | 新增(B-2) |

**回填逻辑：**
```
执行完成 → PATCH /api/work-orders/{id}
  → status = completed
  → output_path = 结果路径
  → evidence_path = 证据路径
  → completed_at = now
```

### B-2：CEO Orchestrator（2h）

**文件：** `backend/app/services/ceo_orchestrator.py`

```
CEO Orchestrator 是 CEO Agent 的后端编排层。
当 CEO Skill 生成 task_plan 后，Orchestrator 负责：

1. 按顺序/并行执行 Work Orders
2. 收集结果
3. 生成汇总
4. 写入 Evidence

流程：
  CEO Skill 生成 task_plan → POST /api/work-orders (批量)
  → Orchestrator 读取 work_orders，按风险等级决定执行策略
  → 调用 WorkOrderExecutor 执行
  → 回填结果
  → 返回汇总
```

**不是必须马上实现完整版。** MVP 可以先让 CEO Agent 直接生成 Work Orders，然后手动逐个触发执行。Orchestrator 自动化是第二阶段。

### B-3：OpenClaw Bridge 最小版（1h）

**文件：** `backend/app/services/openclaw_bridge.py`

```python
class OpenClawBridge:
    """最小版：生成 task card → 写入目录 → 轮询结果"""
    
    def create_task_card(self, work_order) -> str:
        """生成 OpenClaw-compatible task card JSON"""
        card = {
            "task_id": work_order.work_order_id,
            "source": "ai-company-os-ceo",
            "goal": work_order.expected_output,
            "context": work_order.input_context,
            "report_back_path": str(Path(settings.OPENCLAW_RESULTS_DIR) / f"{work_order.work_order_id}.json"),
        }
        card_path = Path(settings.OPENCLAW_TASKS_DIR) / f"{work_order.work_order_id}.json"
        card_path.write_text(json.dumps(card, ensure_ascii=False, indent=2))
        return str(card_path)
    
    def poll_result(self, work_order_id: str, timeout: int = 300) -> dict:
        """轮询结果路径"""
        result_path = Path(settings.OPENCLAW_RESULTS_DIR) / f"{work_order_id}.json"
        # 轮询逻辑
        ...
```

**配置项（config.py 新增）：**

```python
OPENCLAW_TASKS_DIR: str = "~/.openclaw/ceo-tasks/"
OPENCLAW_RESULTS_DIR: str = "~/.openclaw/ceo-results/"
```

**注意：** 如果 OpenClaw 未运行 → 降级为"生成 task card 但不发送"，不阻止 CEO 流程。

---

## Sprint C：验收场景跑通（2h）

### C-1：种子数据注册

执行 seed 脚本，注册：
- 5 个 Skill
- 5 条 Product Line

**验证方法：**

```bash
# 检查 seed
curl http://localhost:8001/api/skills | python3 -m json.tool
curl http://localhost:8001/api/product-lines | python3 -m json.tool

# 测试路由
curl "http://localhost:8001/api/skills/route?task_type=research"
# → {"skill_id": "research_agent", "runtime_id": "hermes", ...}

curl "http://localhost:8001/api/skills/route?task_type=landing_page_code"
# → {"skill_id": "landing_page_builder", "runtime_id": "codex", "risk_level": "medium"}
```

### C-2：验收场景全链路

**Founder 输入：** `为 Amazon 利润体检报告准备一个最小销售页`

**手动触发流程（MVP 先不自动化整个 Orchestrator）：**

```bash
# 1. CEO Skill 拆解任务（手动或通过页面）
#    生成 5 个 Work Orders

# 2. 手动逐个执行或通过 WorkOrderExecutor
python scripts/generate_profit_health_report.py --sample -o reports/sales-page/sample-report.md

# 3. 检查结果
curl http://localhost:8001/api/work-orders
# → 5 条记录，全部 completed
# → 每个有 output_path / evidence_path

# 4. CEO 汇总
# → 所有结果路径打印
# → 下一步建议
```

### C-3：回归检查

| 检查项 | 方法 |
|:-------|:-----|
| 现有 5 个 Skill 不受影响 | curl 现有 skill API |
| 前端页面正常 | curl 前端路由 |
| CEO 行为日志 | 检查 ceo_action_logs 表 |
| 宪法合规 | 高风险任务不自动执行 |

---

## 依赖项

| 依赖 | 版本 | 用途 |
|:-----|:-----|:------|
| 现有 FastAPI + SQLite | v0.9.x | 后端 |
| Hermes delegate_task (ACP) | 已有 | 执行 Hermes/Codex 任务 |
| `~/.hermes/skills/` | 已有 | CEO Agent skill 存放 |

## 不依赖项

- ❌ 不依赖 OpenClaw 运行（降级为 task card 生成）
- ❌ 不依赖飞书网关（CEO 在终端页面工作）
- ❌ 不依赖 AI经营系统 DB（Work Order 用 OS 自己的 SQLite）

---

## 时间线

| 天数 | Sprint | 内容 | 工时 |
|:----|:-------|:-----|:-----|
| Day 1 | A | Skill Registry + Product Line + Work Order 表 + API + 种子数据 | 3h |
| Day 1 | A | Skill Router + CEO Skill | 2h |
| Day 2 | B | WorkOrderExecutor + CEO Orchestrator | 2h |
| Day 2 | B | OpenClaw Bridge 最小版 | 1h |
| Day 3 | C | 验收场景 + 回归检查 + 修复 | 2h |
| | **Total** | | **10h** |

---

## 验收清单

- [ ] `SkillRegistry` 表创建 + 5 个种子 Skill
- [ ] `ProductLineRegistry` 表创建 + 5 条种子产品线
- [ ] `WorkOrder` 表创建 + CRUD API
- [ ] `skill_router.route()` 返回正确的 skill
- [ ] CEO Agent Skill 可加载，能拆解目标
- [ ] 低风险 Work Order 可直接执行
- [ ] 代码类 Work Order 走 Code Bridge
- [ ] 部署类 Work Order 只出 checklist
- [ ] OpenClaw Bridge 生成 task card（至少降级模式）
- [ ] 验收场景："为利润报告准备销售页" — 5 个 Work Orders 全部跑通
- [ ] 现有功能回归：curl 检查无破坏
