# AI Company Control Center v0.10 — Work Delegation Layer MVP PRD

> **状态**: 📋 PRD · 待执行
> **预估工时**: 10-14h（文档 + 表结构 + CEO Prompt + Router + 执行回传 + 验收场景）
> **定位**: v0.10 让 AI Company OS 从"有很多模块"升级成"能把目标分派给正确 Agent 并推动产品上线"的公司操作系统。
>
> **一句话**: 不是做一个 CEO Agent，而是做"公司工作分派层"——CEO 是入口，Skill Registry 是能力地图，Skill Router 是确定性路由，Work Order 是执行合同。

---

## 0、v0.10 产品定义

### 一句话目标
> **让 Founder 通过 CEO Agent 下达一个目标，系统能识别任务类型、选择能力/Agent/Runtime，并生成可执行 Work Order，执行后回传结果。**

### 核心链路
```
Founder 提目标
  → CEO 拆解（LLM 参与）
  → Skill Router 路由（确定性规则，不用 LLM）
  → 生成 Work Order
  → 按 execution_mode 分派执行
  → 结果回填 Work Order
  → CEO 汇总
  → Evidence 留痕
```

### v0.10 不做
- ❌ 不做完整 CEO 自治（CEO 不自执行、不自决策高风险事项）
- ❌ 不做 Agent Meeting
- ❌ 不做自动部署
- ❌ 不做高风险自动执行（删除文件、改 .env、支付、发邮件、部署上线、restart runtime）
- ❌ 不做 UI 重构
- ❌ 不做多租户
- ❌ 不做 Skill Marketplace
- ❌ 不做大量子 Agent 常驻进程
- ❌ CEO 不能绕过 Approval / Code Bridge

## 一、产品定位

### 为什么现在做

过去三个版本的能力积累：

| 版本 | 核心能力 | 当前状态 |
|:-----|:---------|:---------|
| v0.7 | Proposal Layer | 🏁 完成 |
| v0.8 | Execution Bridge | 🏁 完成 |
| v0.9 | Code-Capable Runtime Bridge | 🏁 完成 |
| **v0.10** | **Work Delegation Layer** | **📋 本次** |

但当前 OS 缺一个"大脑"——当 Founder 说一个目标时，系统不知道：
- 这个任务需要什么能力
- 哪个 Agent/Runtime 有这些能力
- 任务如何拆解、分派、追踪、汇总

### 根本原则

```
CEO Agent 如果没有 Skill Router / Work Order，只是一个会聊天的壳。
```

### 和其他模块的关系

```
Founder（你）
  │
  ▼
CEO Agent ────────────── 本次核心
  │  Goal Intake + 任务拆解
  │
  ▼
Skill Router ──────────── 本次核心
  │  确定性规则 → 选 Agent + Runtime
  │
  ├─ Skill Registry Lite    本次新增 SQLite 表
  ├─ Product Line Registry  本次新增 SQLite 表
  ├─ Work Order             本次新增 SQLite 表 + API
  │
  ▼
执行层（已有）
  ├─ Hermes / OpenClaw      已有 Runtime
  ├─ Codex（v0.9 Code Bridge）已有
  ├─ OpenClaw Bridge        本次最小版
  └─ Local Script           本次新增（OP-006 报告生成器）
  │
  ▼
回传 → CEO 汇总 → Evidence  本次闭环
```

---

## 二、范围

### 必做

| # | 模块 | 说明 | 工时 |
|:-:|:-----|:------|:----:|
| 1 | **Skill Registry Lite** | SQLite 表：skill_id / capability_type / owner_agent / owner_runtime / 风险等级 | 1h |
| 2 | **Product Line Registry Lite** | SQLite 表：5 条产品线（ai-company-os / ai-seller-finance / amazon-business / digital-products / launch-sites） | 30min |
| 3 | **Work Order 表 + API** | 正式工作单：wo_id / goal_session_id / product_line / skill_id / runtime_id / status / input / output / evidence_path | 2h |
| 4 | **Deterministic Skill Router** | Python 规则引擎：task_type → capability_type → skill。LLM 不参与低层路由 | 1.5h |
| 5 | **CEO Goal Intake** | Hermes 同进程 CEO skill/system prompt。接收目标 → 生成 Goal Session → 调用 Router → 生成 Work Orders | 2h |
| 6 | **执行回传闭环** | CEO 调用 delegate_task / local script → Work Order result 写回 → CEO 汇总 → Evidence 留痕 | 3h |
| 7 | **OpenClaw Bridge 最小版** | 生成 OpenClaw-compatible task card，不做复杂对话 | 1h |
| | **验收场景跑通** | "为利润报告准备最小销售页"全链路 | 1h |

### 必做详情

#### 1. Skill Registry Lite

**数据模型：**

| 字段 | 类型 | 说明 |
|:-----|:-----|:------|
| skill_id | TEXT PK | 唯一标识 |
| name | TEXT | 技能名称 |
| description | TEXT | 描述 |
| capability_type | TEXT | 能力类型：research / copywriting / code_build / report_generation / deploy |
| owner_agent | TEXT | 负责 Agent（hermes / openclaw / codex / local） |
| owner_runtime | TEXT | 负责 Runtime（hermes / openclaw / codex / shell） |
| risk_level | TEXT | low / medium / high |
| input_schema | TEXT | JSON Schema 或描述 |
| output_schema | TEXT | 输出格式描述 |
| examples | TEXT | 适用场景示例 |
| status | TEXT | active / disabled / experimental |
| execution_mode | TEXT | direct_delegate / code_bridge / local_script / openclaw_task_card / checklist_only / manual |
| created_at | DATETIME | — |
| updated_at | DATETIME | — |

**首批注册 5 个 Skill：**

| skill_id | capability_type | owner_agent | owner_runtime | risk_level | execution_mode |
|:---------|:---------------|:------------|:--------------|:-----------|:---------------|
| research_agent | research | hermes | hermes | low | direct_delegate |
| landing_page_copywriter | copywriting | hermes | hermes | low | direct_delegate |
| landing_page_builder | code_build | codex | codex | medium | code_bridge |
| deployment_assistant | deploy | codex | shell | high | checklist_only |
| profit_health_report_generator | report_generation | local | local | low | local_script |

#### 2. Product Line Registry Lite

**数据模型：**

| 字段 | 类型 | 说明 |
|:-----|:-----|:------|
| product_line_id | TEXT PK | 唯一标识 |
| name | TEXT | 产品线名称 |
| description | TEXT | 描述 |
| owner_agent | TEXT | 负责人 Agent（暂为虚拟角色） |
| status | TEXT | active / paused / incubating |
| related_skills | TEXT | 逗号分隔 skill_id 列表 |

**首批注册 5 条产品线：**

| product_line_id | name | 说明 |
|:----------------|:-----|:------|
| ai-company-os | AI Company OS 自身 | OS 平台能力建设 |
| ai-seller-finance | AI经营系统 / 卖家财务 | 利润报告、财务分析 |
| amazon-business | 亚马逊跨境业务 | 运营、选品、供应链 |
| digital-products | 数字产品（电子书/课程/SaaS） | 内容产品 + 独立站 |
| launch-sites | 启动页 / 落地页 | 产品 landing page |

#### 3. Work Order 表 + API

**数据模型：**

| 字段 | 类型 | 说明 |
|:-----|:-----|:------|
| work_order_id | TEXT PK | UUID |
| goal_session_id | TEXT | 关联的目标会话 |
| product_line_id | TEXT | 关联的产品线 |
| skill_id | TEXT | 需要的能力 |
| assigned_agent | TEXT | 实际执行的 Agent 标识 |
| runtime_id | TEXT | 实际执行的 Runtime |
| input_context | TEXT | 输入数据和上下文 |
| expected_output | TEXT | 预期输出描述 |
| status | TEXT | 状态机：created → routed → assigned → blocked / requires_approval → in_progress → completed / failed / cancelled |
| task_type | TEXT | 任务类型（research / copywriting / code_build / report_generation / deploy） |
| route_reason | TEXT | 路由原因记录 |
| risk_level | TEXT | low / medium / high |
| execution_mode | TEXT | direct_delegate / code_bridge / local_script / checklist_only / openclaw_task_card |
| approval_required | BOOLEAN | 中高风险任务需要审批 |
| approval_id | TEXT | 审批 ID |
| attempt_count | INT | 重试次数 |
| output_path | TEXT | 执行结果路径 |
| evidence_path | TEXT | Evidence 记录路径 |
| error | TEXT | 错误信息 |
| result_summary | TEXT | 执行结果摘要 |
| artifacts_json | TEXT | JSON：产物路径列表 |
| routing_log_json | TEXT | JSON：路由日志 |
| execution_log_json | TEXT | JSON：执行日志 |
| created_at | DATETIME | — |
| completed_at | DATETIME | — |

**状态机：**

```
created → routed → assigned → blocked（找不到 Skill）
                               → requires_approval（中高风险）
                               → in_progress → completed / failed
created → cancelled（人工取消）
```

**状态说明：**

| 状态 | 说明 | 触发条件 |
|:-----|:------|:---------|
| created | 已创建但未路由 | CEO 生成 Work Order |
| routed | 已路由找到 Skill | Skill Router 返回匹配结果 |
| assigned | 已分派给 Agent/Runtime | 确认执行 |
| blocked | 找不到匹配 Skill | Router 返回 no_matching_skill |
| requires_approval | 需要 Founder 审批 | risk_level=medium/high |
| in_progress | 正在执行 | Executor 开始工作 |
| completed | 执行完成 | 结果回填 |
| failed | 执行失败 | Executor 返回错误 |
| cancelled | 人工取消 | Founder 或 CEO 取消 |

**API 清单：**

| Method | Path | 用途 |
|--------|------|------|
| GET | /api/v1/skills | 列表（支持 capability_type / status 筛选） |
| GET | /api/v1/skills/{skill_id} | 详情 |
| POST | /api/v1/skills | 注册新 Skill |
| PATCH | /api/v1/skills/{skill_id} | 更新 |
| GET | /api/v1/product-lines | 列表 |
| GET | /api/v1/product-lines/{product_line_id} | 详情 |
| POST | /api/v1/product-lines | 注册 |
| PATCH | /api/v1/product-lines/{product_line_id} | 更新 |
| GET | /api/v1/work-orders | 列表（支持 session / product_line / status 筛选） |
| POST | /api/v1/work-orders | 创建 |
| GET | /api/v1/work-orders/{id} | 详情 |
| POST | /api/v1/work-orders/{id}/route | 手动路由 |
| POST | /api/v1/work-orders/{id}/execute | 手动执行 |
| POST | /api/v1/work-orders/{id}/complete | 标记完成 + 回填 |
| POST | /api/v1/ceo/goal-intake | CEO 目标输入 |
| GET | /api/v1/ceo/goal-sessions/{id} | 查询 Goal Session |

#### 4. Deterministic Skill Router

**核心逻辑：** Python 规则引擎，不用 LLM。

```python
# skill_router.py

TASK_TYPE_MAP = {
    # 研究类
    "research": "research",
    "market_analysis": "research",
    "competitor_analysis": "research",
    
    # 文案类
    "copywriting": "copywriting",
    "landing_page_copy": "copywriting",
    "marketing_copy": "copywriting",
    
    # 代码类
    "code_build": "code_build",
    "landing_page_code": "code_build",
    "feature_implementation": "code_build",
    
    # 报告类
    "report_generation": "report_generation",
    "profit_health_report": "report_generation",
    
    # 部署类
    "deploy": "deploy",
    "deployment_checklist": "deploy",
}


def route(task_type: str, skills: list) -> dict:
    """输入任务类型，返回匹配的 Skill"""
    capability = TASK_TYPE_MAP.get(task_type)
    if not capability:
        return {"error": f"Unknown task type: {task_type}"}
    
    for skill in skills:
        if skill.capability_type == capability and skill.status == "active":
            return {
                "skill_id": skill.skill_id,
                "capability_type": skill.capability_type,
                "owner_runtime": skill.owner_runtime,
                "risk_level": skill.risk_level,
            }
    
    return {"error": f"No active skill for capability: {capability}"}
```

**注意：LLM 参与"目标拆解"** — CEO 收到 Founder 目标后，先用 LLM 拆成子任务列表，每个子任务标注 task_type，然后 Router 做确定性查询。

#### 5. CEO Goal Intake

**实现方式：** Hermes skill（`ceo-agent` skill）

**CEO 系统提示核心内容：**

```
你正在以 AI Company OS 的 CEO Agent 身份运行。

你的职责：
1. 接收 Founder 的目标/指令
2. 理解目标，拆解为子任务列表
3. 每个子任务标注 task_type（从预定义列表中选）
4. 调用 Skill Router 查询能力
5. 生成 Work Orders 列表
6. 分派 Work Orders 给对应 Agent/Runtime
7. 收集执行结果
8. 汇总给 Founder
9. 写入 Evidence

你的限制：
- 你不能直接执行代码（必须通过 Code Bridge）
- 你不能绕过 Skill Router
- 高风险任务必须生成 Proposal，不可直接执行
- 每次决策写入 ceo_action_logs

你的输出格式：
- goal_session: { id, goal, task_plan, work_orders }
- 每个 work_order: { skill_id, task_type, input_context, expected_output }
```

**注意：CEO Agent 不替换你（Founder）和 Hermes 的日常对话。**
当用户以"常规操作"身份说话时（如"帮我查下数据库"），走普通流程。
当用户以"下达目标"身份说话时（如"为利润报告准备一个销售页"），走 CEO 流程。
区别方式：CEO 模式用明确标记的前缀或单独的命令。

#### 6. 执行回传闭环

**流程：**

```
CEO 生成 Work Order
  → 检查 risk_level：
      low → 直接执行（delegate_task / local script）
      medium → 需要确认后执行
      high → 生成 Proposal，不自动执行
  → 执行结果写回 Work Order（output_path / evidence_path）
  → CEO 汇总所有 Work Orders 结果
  → 生成 Summary 回复给 Founder
  → 记录到 Evidence（如果路径配置）
```

**执行方式矩阵：**

| Skill | execution_mode | 具体执行方式 | 回填内容 |
|:------|:---------------|:-------------|:---------|
| research_agent | direct_delegate | Hermes delegate_task | markdown summary + source notes |
| landing_page_copywriter | direct_delegate | Hermes delegate_task | landing-copy.md |
| landing_page_builder | code_bridge | 创建 CCR / Code Bridge 申请，不直接写代码 | CCR ID + artifact path |
| deployment_assistant | checklist_only | 只生成部署 checklist，不执行 shell，不部署 | deploy-checklist.md |
| profit_health_report_generator | local_script | subprocess 调用 `generate_profit_health_report.py` | report path |

### 安全边界（硬规则）

| 风险等级 | 允许自动执行 | 规则 |
|:---------|:-------------|:------|
| low | ✅ 直接执行 | research_agent / copywriter / report_generator |
| medium | ⚠️ 需进入 Code Bridge | landing_page_builder 不直接写文件 |
| high | ❌ 只出 checklist | deployment_assistant 不执行 shell，不部署 |
| blocked | ❌ 禁止 | 以下操作全部禁止自动执行 |

**明确禁止 CEO Agent 自动执行的操作：**
- ❌ 删除文件 / 目录
- ❌ 修改 .env / 配置文件
- ❌ 支付 / 收款操作
- ❌ 发送电子邮件
- ❌ 部署上线到生产环境
- ❌ restart runtime / kill 进程
- ❌ 绕过 Skill Router 直接派任务
- ❌ 找不到 Skill 时自己决定怎么做（必须 blocking）

#### 7. OpenClaw Bridge 最小版

**不实现复杂的 Agent 间对话。**

只做：

1. 生成 OpenClaw-compatible task card（Markdown 格式）
2. 写入 `backend/runtime/openclaw-task-cards/{work_order_id}.md`
3. 轮询 `backend/runtime/openclaw-results/{work_order_id}.json`（手动完成或降级）
4. 结果回填 Work Order

**降级策略：** 如果 OpenClaw 未运行 → 只生成 task card 文件，不阻塞 CEO 流程。
结果回填先走手动路径：用户确认 → PATCH Work Order。

**Task Card 格式（Markdown）：**

```markdown
# OpenClaw Task Card

work_order_id: wo-xxx
product_line: ai-seller-finance
source: ai-company-os-ceo
goal: Research target users and pain points for Amazon profit report
context: ...
expected_output: structured research brief in markdown
allowed_actions: [read, research, write_markdown]
report_back_path: backend/runtime/openclaw-results/wo-xxx.json
created_at: 2026-05-29
```

**结果回填格式（JSON）：**

```json
{
  "work_order_id": "wo-xxx",
  "status": "completed",
  "output_path": "outputs/research-summary.md",
  "summary": "Found 3 key pain points: ...",
  "artifacts": ["outputs/research-summary.md"],
  "error": null
}
```

### 不做

- ❌ 不做完整 CEO 自治（CEO 不自执行具体任务，不自决策高风险事项）
- ❌ 不做 Agent Meeting（Agent 间结构化会议）
- ❌ 不做完整 UI 重构
- ❌ 不做自动部署（deployment_assistant 只输出 checklist，不自动执行）
- ❌ 不做自动支付接入
- ❌ 不做多租户
- ❌ 不做复杂权限系统
- ❌ 不做完整 Skill Marketplace
- ❌ 不做大量子 Agent 常驻进程
- ❌ CEO 不能绕过 Approval / Code Bridge
- ❌ 不重构现有代码库

---

## 三、验收标准

### 验收场景

> **Founder 输入：** "为 Amazon 利润体检报告准备一个最小销售页。"

**预期产物路径：**

```
work_orders/
├── WO-001 research_agent
│     → outputs/research-summary.md                          （用户痛点 + 卖点整理）
├── WO-002 landing_page_copywriter
│     → outputs/landing-copy.md                              （落地页文案）
├── WO-003 profit_health_report_generator
│     → reports/sample-profit-health-check.md                 （样例报告）
├── WO-004 landing_page_builder
│     → code_bridge request 或 landing-page artifact         （页面代码，走 Code Bridge）
├── WO-005 deployment_assistant
│     → outputs/deploy-checklist.md                          （部署 checklist，只出文档不部署）
└── evidence/
      └── v0.10-work-delegation-run.md                       （CEO 汇总 + Evidence）

CEO 最终汇总输出：
  goal_session_summary.md
  - 每个 Work Order 状态
  - 产物路径
  - 未完成原因
  - 下一步建议
```

**流程验证：**

```
1. CEO 收到目标 → 生成 Goal Session

2. CEO 拆解任务：
   Work Order 1: research_agent
     → 任务：整理目标用户痛点和卖点
     → Runtime: hermes
     → 风险: low

   Work Order 2: landing_page_copywriter
     → 任务：生成落地页文案
     → Runtime: hermes
     → 风险: low

   Work Order 3: landing_page_builder
     → 任务：生成静态页面代码
     → Runtime: codex
     → 风险: medium → 走 Code Bridge

   Work Order 4: profit_health_report_generator
     → 任务：生成样例报告链接/说明
     → Runtime: local script
     → 风险: low

   Work Order 5: deployment_assistant
     → 任务：生成部署 checklist
     → Runtime: codex/shell
     → 风险: high → 只出 checklist，不自动执行

3. 各 Work Order 执行完成 → 结果回填

4. CEO 汇总回复：
   - 销售页文案路径
   - 页面代码路径
   - 样例报告路径
   - 部署说明路径
   - 下一步建议
   - Evidence 记录
```

### 质量指标

| 检查项 | 标准 |
|:-------|:-----|
| Skill Router 响应时间 | < 50ms（确定性查询，无 LLM） |
| Work Order 创建 | API 返回 < 200ms |
| CEO 目标拆解 | 至少识别 3 个以上子任务 |
| 执行回传 | 5 个 Work Orders 全部完成或反馈状态 |
| 不影响现有功能 | 现有 5 个 Skill + 前端页面不受影响 |
| CEO 行为日志 | 每次决策写入 ceo_action_logs |

---

## 四、宪法兼容性

| 宪法条款 | v0.10 如何遵守 |
|:---------|:---------------|
| Founder 是最终决策者 | CEO Agent 不自决策高风险任务 |
| CEO Agent 是唯一的 Controller | CEO Agent 是唯一入口，其他 Agent 不互相调用 |
| 三层权责分离 | CEO = 调度层，Execution = 执行层 |
| 证据留存 | 执行结果写入 Work Order + Evidence |
| 安全和审批门禁 | Code/Deploy 任务走 Code Bridge / Proposal |

---

## 五、版本命名

> v0.10 原名"CEO Agent"，GPT 和 Hermes 共同纠正为 **Work Delegation Layer MVP**。
> 核心区别：
> - CEO Agent → 做一个更聪明的聊天界面 ❌
> - Work Delegation Layer → 公司工作分派层 ✅

---

## 六、风险与缓解

| 风险 | 等级 | 缓解 |
|:-----|:-----|:------|
| CEO 和普通 Hermes 行为混淆 | 🟡 | 独立 system prompt + 结构化输出 + 行为日志 |
| Work Order 堆积不执行 | 🟡 | MVP 先手动物理确认，不自动批量执行 |
| Codex 调用失败 | 🟡 | 已有 Code Bridge + mock fallback |
| 范围蔓延到"完整 CEO 自治" | 🔴 | 不做清单已明确写死 |
| OpenClaw task card 格式不兼容 | 🟡 | 验证阶段先 mock，不依赖真实 OpenClaw 环境 |
