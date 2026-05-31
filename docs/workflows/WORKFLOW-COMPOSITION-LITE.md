# AI Company OS — Workflow Composition Lite (v0.30)

> **设计文档** · 2026-05-17
> **对应版本**: v0.30 — Workflow Composition Lite with Asset Handoff
> **PRD**: `docs/prd/v0.30-WORKFLOW-COMPOSITION-LITE-PRD.md`
> **模板目录**: `scripts/templates/`
> **主要脚本**: `scripts/workflow_runner.py`（Sprint C 实现）

---

## 一、设计原则

1. **Workflow 是 Work Order 的编排层**，不是新的执行系统
2. **Workflow 不能绕过 Founder approval**
3. **Workflow 不能绕过 Policy Resolver**
4. **Workflow 每步仍然是 Work Order**，走完整生命周期
5. **Workflow first, Agent second** — 不引入 Agent Meeting / 自由 multi-agent mesh

---

## 二、Workflow Schema

### 双层 Metadata 载体

| 阶段 | 载体 | 内容 |
|:-----|:-----|:------|
| **Draft 阶段** | Draft 文件 YAML front matter | `workflow_id`, `step_id`, `template`, `depends_on`, `outputs` |
| **Work Order 阶段** | WO `metadata_json` | 从 Draft front matter 复制 + 补充 `asset_id` |

**Draft 文件 front matter**:

```yaml
---
workflow_id: WF-20260517-001
workflow_step_id: step_1_review
workflow_template: decision_followup_workflow
step_index: 0
total_steps: 3
depends_on: []
outputs:
  - asset_type: decision_summary
    required: true
    status: pending
---
```

### Work Order metadata_json 扩展

每个 Work Order 在 `metadata_json` 中包含：

```json
{
  "workflow_id": "WF-20260517-001",
  "workflow_step_id": "step_1_review",
  "workflow_template": "decision_followup_workflow",
  "step_index": 0,
  "total_steps": 3,
  "depends_on": [],
  "consumes_asset": null,
  "outputs": [
    {
      "asset_type": "decision_summary",
      "asset_id": null,
      "status": "pending"
    }
  ],
  "workflow_step_status": "pending",
  "blocked_reason": null
}
```

### Workflow Plan Record（Run Ledger）

Workflow 级别的元数据作为 `workflow_created` 事件写入 Run Ledger：

| 字段 | 类型 | 说明 |
|:-----|:-----|:------|
| `workflow_id` | string | `WF-YYYYMMDD-NNN` |
| `template` | string | 模板名 |
| `status` | string | `active` / `completed` / `cancelled` |
| `total_steps` | int | 模板 step 数量 |
| `current_step_index` | int | 当前进行到的 step |
| `created_via` | string | 触发来源（`cli`） |
| `context_summary` | string | 用户提供的上下文 |

---

## 三、Template 规范

### 存放位置

`scripts/templates/<template_id>.yaml`

### Schema

```yaml
workflow:
  id: string                    # 唯一模板 ID
  name: string                  # 显示名称
  description: string           # 描述
  version: string               # 版本号
  mode: sequential              # 当前仅支持 sequential

steps:
  - step_id: string             # 唯一 step ID
    task_type: string           # 任务类型（review / draft_generation / research / planning / execution）
    action: string              # 对应 capability-boundary 的 action
    action_class: string        # read_only / safe_output / approval_required
    description: string         # 人类可读描述
    outputs:                    # 本 step 产出物声明
      - asset_type: string      # Asset Registry 类型
        required: boolean       # 是否必须
        description: string     # 描述
    depends_on:                 # 前置依赖（第一项可不填）
      - step: string            # 前置 step_id
        consumes_asset: string  # 消费的 asset_type
    completion_criteria:        # 完成判断标准
      type: string              # asset_created / work_order_completed / result_synced
      required_asset_type: string  # 对应的 asset_type
```

### Completion Criteria 可选值

| 类型 | 适用 action_class | 完成条件 |
|:-----|:-----------------|:---------|
| `asset_created` | read_only / safe_output | 产出资产已登记到 Asset Registry |
| `work_order_completed` | approval_required | Work Order 状态为 completed |
| `result_synced` | approval_required | Work Order completed + 结果已回写 |

---

## 四、Step 状态机

```
     created
       │
    in_progress
       │
  ┌────┴────┐
  │         │
completed  blocked
  │         │
  │     ┌───┴───┐
  │     │       │
  │  resolved  skipped
  │     │       │
  └─────┴───────┘
       │
  (next unlocked / cancelled)
```

---

## 五、Run Ledger 事件（9 类）

| 事件类型 | 触发点 | 数据负载 |
|:---------|:-------|:---------|
| `workflow_created` | `create` 命令 | `workflow_id`, `template`, `total_steps`, `context` |
| `workflow_step_created` | `next` 命令 | `workflow_id`, `step_id`, `draft_wo_id` |
| `workflow_step_completed` | WO result_sync | `workflow_id`, `step_id`, `wo_id` |
| `workflow_step_unlocked` | `next` 命令 | `workflow_id`, `step_id`, `unlocked_by_step` |
| `workflow_blocked` | `next` 检测依赖未满足 | `workflow_id`, `step_id`, `blocked_reason` |
| `workflow_block_resolved` | `resolve` 命令 | `workflow_id`, `step_id`, `resolved_by` |
| `workflow_step_skipped` | `skip` 命令 | `workflow_id`, `step_id`, `skip_reason` |
| `workflow_cancelled` | `cancel` 命令 | `workflow_id`, `cancelled_by`, `reason` |
| `workflow_completed` | 最后一步 completed | `workflow_id`, `total_steps` |

---

## 六、Asset 类型（3 种）

| asset_type | 触发点 | 数据 |
|:-----------|:-------|:-----|
| `workflow_plan` | `create` 命令 | `workflow_id`, `template`, steps 总览 |
| `workflow_step_context` | `next` 命令 | `step_id`, `context`, `source_asset_refs` |
| `workflow_step_output` | WO result_sync | `step_id`, `wo_id`, `output_summary` |

---

## 七、Skip Context 机制

当 Founder 使用 `skip` 命令跳过某 step 时，不静默置空 `consumes_asset`，而是生成一个 `skipped_context` 资产：

```json
{
  "asset_type": "workflow_step_context",
  "summary": "Step validation_plan was skipped by Founder. The expected opportunity_card asset is unavailable.",
  "status": "skipped_context"
}
```

后续 step 消费此资产时，Draft 将明确提示："上一步已被 Founder 跳过，因此本步骤缺少原计划输入。"

---

## 八、Asset Fallback（next 命令）

`next` 读取前置 step 输出资产时，使用三层 fallback：

| 优先级 | 方法 |
|:------:|:-----|
| 1 | Step `metadata_json.outputs[].asset_id` |
| 2 | Asset Registry 按 `source_work_order` + `asset_type` 查询 |
| 3 | Work Order `result_summary` / Draft `metadata` 生成 fallback context |
| — | 三层均找不到 → `BLOCKED`, `blocked_reason=missing_required_asset` |

---

## 九、模板列表

| 模板 ID | 名称 | 用途 | 状态 |
|:--------|:-----|:-----|:-----|
| `decision_followup_workflow` | Decision Follow-up | 决策 → Draft → WO → 执行 | ✅ v0.30 |
| `opportunity_followup_workflow` | Opportunity Follow-up | 机会信号 → 研究 → 验证 → 执行 | ✅ v0.30 |

**暂不做**：
- 文章摄入模板（由 Hermes + AI-Knowledge-OS 负责）
- 并行 workflow / 条件分支（v0.31+）

---

## 十、Founders' Handbook

### 创建 Workflow

```bash
python3 scripts/workflow_runner.py create --template decision_followup_workflow --context "跟进 XX 项目的执行结果"
```

### 查看进度

```bash
python3 scripts/workflow_runner.py status WF-20260517-001
```

### 前进到下一步

```bash
python3 scripts/workflow_runner.py next WF-20260517-001
```

### 处理阻塞

```bash
# 阻塞已解决，恢复
python3 scripts/workflow_runner.py resolve WF-20260517-001 step_2

# 跳过该步骤（生成 skip_context 资产）
python3 scripts/workflow_runner.py skip WF-20260517-001 step_2

# 取消整个 workflow
python3 scripts/workflow_runner.py cancel WF-20260517-001
```

### 注意事项

- 每次 `next` 只生成**下一步 Draft**，不会自动批准或执行
- 所有 Workflow 操作**不绕过 Policy Resolver**
- Step 跳过后会产生 `skip_context` 资产，后续 Draft 会提示输入缺失
- Workflow 是**顺序执行**，当前版本不支持并行或分支
- 如果觉得 2-3 步不如手动创建 WO，这是 v0.30 的起点

---

## 十一、未来扩展（v0.31+）

| 功能 | 计划版本 |
|:-----|:---------|
| OS 主动市场机会扫描（Opportunity Scout Loop） | v0.31 |
| AI-Knowledge-OS → Opportunity Signal 桥 | v0.31+ |
| 并行 workflow | v0.31+ |
| 条件分支 | v0.31+ |
| Workflow DB 表（workflow_runs / workflow_steps） | v0.31（如需 UI 展示） |
| Web UI workflow 展示 | v1.0 |
