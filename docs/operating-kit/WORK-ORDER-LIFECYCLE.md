---
title: "Work Order Lifecycle — AI Company OS 工单生命周期"
domain: operating-kit
---

# Work Order Lifecycle — 工单生命周期

> **对应版本**：v0.10–v0.22  
> **核心模型**：`backend/app/models/work_order.py`  
> **核心服务**：`backend/app/services/work_order_executor.py`, `scripts/work_order_control.py`

---

## 1. 状态机

```
                     ┌──────────┐
                     │  created │  ← Work Order 创建后初始状态
                     └────┬─────┘
                          │ approve-dispatch
                          ▼
                   ┌──────────────┐
                   │  routed      │  ← 路由完成（skill_id, runtime 已分配）
                   └──────┬───────┘
                          │ execute
                          ▼
                  ┌────────────────┐
                  │  in_progress   │  ← 正在执行（同步或异步）
                  └───┬────┬───────┘
                      │    │
          ┌───────────┘    └───────────┐
          ▼                            ▼
   ┌───────────┐               ┌──────────────┐
   │ completed │               │    failed    │
   └───────────┘               └──────────────┘
          │                            │
          │                            ▼
          │                  ┌──────────────────┐
          │                  │  needs_review    │  ← 连续失败两次
          │                  └──────────────────┘
          │
          ▼
   ┌───────────┐
   │ cancelled │  ← 被 Founder 取消
   └───────────┘
```

### 状态说明

| 状态 | 含义 | 下一状态 |
|:-----|:------|:---------|
| `created` | 已创建，未路由 | routed / cancelled |
| `routed` | 已路由，等待执行 | in_progress |
| `in_progress` | 正在执行 | completed / failed / cancelled |
| `completed` | 执行成功，有结果 | —（终止） |
| `failed` | 执行失败 | needs_review（连续失败） |
| `needs_review` | 需要人工审查 | —（终止，待人工） |
| `cancelled` | 被取消 | —（终止） |

---

## 2. 执行模式

| 模式 | 说明 | 适用场景 |
|:-----|:------|:---------|
| `direct_delegate` | 立即在当前进程执行 | 简单任务、本地脚本 |
| `local_script` | 在本地执行脚本 | 代码生成、批处理 |
| `openclaw_agent` | 通过 OpenClaw 发送到远程 Agent | 复杂任务、需要 Agent 推理 |

---

## 3. Work Order 数据结构

```yaml
work_order_id: "WO-XXXXXXXX"     # UUID
status: "created"                 # 状态
skill_id: "research_summary"      # 对应 skill_registry.yaml
task_type: "market_intelligence"  # 任务类型
execution_mode: "direct_delegate" # 执行模式
assigned_agent: "codex"           # 执行 Agent
runtime_id: "codex-cli"          # 运行时

# 路由信息
route_reason: "..."               # 路由理由
risk_level: "low"                 # low / medium / high
approval_required: true           # 是否需要审批

# 执行信息
input_context: "..."              # 输入上下文
expected_output: "..."            # 预期产出
output_path: "..."                # 输出路径
result_summary: "..."             # 结果摘要
attempt_count: 1                  # 尝试次数

# 时间戳
created_at: "..."                 # 创建时间
assigned_at: "..."                # 路由时间
approved_for_dispatch_at: "..."   # 审批时间
completed_at: "..."               # 完成时间
```

---

## 4. CLIs

### 查询 Work Orders

```bash
# CEO Command 查询
python3 scripts/ceo_cmd.py

# OS Registry 查询（更底层）
python3 scripts/os_registry.py assets list --type work_order
```

### 审批派发

```bash
python3 scripts/work_order_control.py approve-dispatch <WO_ID>
```

### 等待结果

```bash
python3 scripts/work_order_control.py wait-result <WO_ID>
python3 scripts/work_order_control.py wait-result --sync-source <WO_ID>
```

---

## 5. 风险等级与审批

每个 Work Order 在创建时根据 Skill Registry 中的 `risk_level` 确定是否需要 Founder 审批：

| 风险等级 | 策略 |
|:---------|:------|
| `low` | 自动执行（如有 Capability Boundary 限制则需 check） |
| `medium` | 需 Founder approve-dispatch |
| `high` | 需 Founder approve-dispatch，且记录到 Run Ledger 的特殊事件 |

审批通过后，WO 状态从 `created` → `routed` → `in_progress`。

---

## 6. 故障策略

| 故障类型 | 处理 |
|:---------|:------|
| 未知 task_type | status = needs_review |
| 运行时不可用 | status = needs_review |
| 执行超时（低风险） | retry |
| 执行超时（中/高风险） | status = needs_review |
| 连续失败 2 次 | status = escalation_required |

---

## 7. 资产与事件记录

每个 Work Order 在生命周期中产生两类记录：

**Asset Registry**：
- `work_order` — WO 本身
- `work_order_draft` — 创建 WO 的 Draft
- `execution_result` — 执行结果

**Run Ledger**：
- `work_order_created`
- `approved_for_dispatch`
- `routed`
- `executed`
- `callback_completed`
- `result_synced`

---

## 8. 当前限制

- 不支持跨运行时动态路由
- 不支持批量审批
- 不支持 WO 暂停/恢复
- 不支持执行策略的多级审批链
- openclaw_agent 为异步模式，无实时推送
