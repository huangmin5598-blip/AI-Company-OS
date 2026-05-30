---
title: "Decision to Execution — AI Company OS 决策到执行链路"
domain: operating-kit
---

# Decision to Execution — 决策到执行链路

> **对应版本**：v0.18–v0.22  
> **核心文件**：`scripts/review_brief.py`, `scripts/work_order_control.py`, `scripts/run_operating_loop.py`  
> **前置**：CEO Brief 已生成

---

## 1. 链路总览

```
                    Founder (人)
                        │
    CEO Brief ─────────►│─────────► Decision
      (自动生成)        │            (勾选)
                        │              │
                        ▼              ▼
                    Work Order Draft ──► Work Order
                     (自动生成)       (POST /api/v1/work-orders)
                                          │
                                          ▼
                                    approve-dispatch
                                     (Founder 批准)
                                          │
                                    ┌─────┴─────┐
                                    ▼           ▼
                                 Route      Execute
                                    │           │
                                    ▼           ▼
                              Work Order    Execution
                               状态迁移      Result
                                              │
                                              ▼
                                         Backfill
                                   (Draft + INDEX +
                                    DECISION-LOG)
                                              │
                                              ▼
                                        Run Ledger
                                        Asset Registry
```

---

## 2. 步骤详解

### Step 1: CEO Brief → Founder 阅读

系统每日自动生成 CEO Brief（见 [DAILY-OPERATING-LOOP.md](DAILY-OPERATING-LOOP.md)）。

Founder 打开 `reports/ceo-briefs/YYYY-MM-DD.md` 阅读。

---

### Step 2: Review Brief

```bash
python3 scripts/review_brief.py review reports/ceo-briefs/YYYY-MM-DD.md
```

Review 命令自动提取 Brief 中的 Decision Items，生成 Review 模板。模板包含：

- 每个决策项的描述
- `[ ]` 复选框用于勾选
- 三个选项：approve / defer / reject
- 备注字段

---

### Step 3: Founder 做决策

Founder 在 Review 模板中勾选决策、填写备注，然后保存。

```bash
python3 scripts/review_brief.py decide <review_file>
```

`decide` 命令：

- 读取勾选的决策
- 写入 `DECISION-LOG.md`（含去重 + 冲突检测）
- 自动生成 Work Order Draft 文件

---

### Step 4: 从 Draft 创建 Work Order

```bash
python3 scripts/review_brief.py create-work-order <draft_file>
```

校验必填字段后，实际调用 `POST /api/v1/work-orders`。创建成功后 Draft Footer 回写 `work_order_id`。

**必填字段**：task_type, proposed_prompt, expected_output

---

### Step 5: 审批与派发

```bash
python3 scripts/work_order_control.py approve-dispatch <WO_ID>
```

`approve-dispatch` 依次执行：

1. 校验 Work Order 状态为 `created` 且 `approval_required=true`
2. 写入 `approved_for_dispatch_at` + `approval_id`
3. 调用 `POST /route` — 填充 skill_id / runtime / risk 等路由信息
4. 调用 `POST /execute` — 状态转为 `in_progress`

**拒绝条件**（6 种非法状态）：
- status != created
- approval_required == false
- 已经审批过
- 已达最大尝试次数
- 系统运行时不可用
- 超出预算

---

### Step 6: 等待执行结果

```bash
python3 scripts/work_order_control.py wait-result <WO_ID> [--timeout 180]
```

轮询至以下终止状态之一：

- `completed`
- `failed`
- `cancelled`
- `needs_review`

---

### Step 7: 结果回写（Backfill）

```bash
python3 scripts/work_order_control.py wait-result --sync-source <WO_ID>
```

三重回写（幂等）：

1. **Draft Footer** — 追加 `## Execution Result` 段落
2. **Draft INDEX** — 更新为 `completed` 状态
3. **DECISION-LOG** — 追加 Execution Completed 行

---

## 3. 关键决策原则

| 原则 | 说明 |
|:-----|:------|
| **人机协作** | 系统自动生成建议，Founder 做最终决策 |
| **拒绝后不自动重试** | 决策被 reject 后，需人工重新发起 |
| **审批可追溯** | 每个审批动作写入 Run Ledger |
| **三方去重** | 同 Brief + 同 ID + 同 Decision 任一匹配则跳过 |
| **冲突检测** | 一个 Decision Item 勾选了多个互斥选项 → 标记 invalid |

---

## 4. 角色分工

| 角色 | 职责 |
|:-----|:------|
| **CEO Brief Generator**（系统） | 自动生成 8 段式 Brief |
| **Founder**（人） | 阅读 → Review → 做决策 |
| **review_brief.py** | 解析 Brief、生成 Review 模板、提取决策 |
| **work_order_control.py** | 审批派发、等待结果、回写 |
| **Run Ledger** | 记录每个步骤的事件 |
| **Asset Registry** | 登记 Brief / Review / Decision / Draft / WO / Result 资产 |

---

## 5. 数据流

```
                     Asset Registry
                    ┌──────────────────┐
                    │ ceo_brief        │
                    │ ceo_brief_review │
                    │ decision_log     │
                    │ work_order_draft │
                    │ work_order       │
                    │ execution_result │
                    └──────────────────┘

                     Run Ledger
                    ┌──────────────────┐
                    │ brief_generated  │
                    │ review_created   │
                    │ decision_logged  │
                    │ draft_created    │
                    │ work_order_      │
                    │ created          │
                    │ approved_for_    │
                    │ dispatch         │
                    │ routed           │
                    │ executed         │
                    │ callback_        │
                    │ completed        │
                    │ result_synced    │
                    └──────────────────┘
```

---

## 6. 当前限制

- Founder Review 通过 CLI 完成，无 Web UI
- 决策审批不涉及复杂计算或费用预测
- 不支持自动路由优化
- 决策项中 "create_work_order_later" 仅为标记，未来版本自动定时执行
