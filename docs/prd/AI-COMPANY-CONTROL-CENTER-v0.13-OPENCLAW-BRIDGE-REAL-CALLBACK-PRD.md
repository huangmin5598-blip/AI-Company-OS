# v0.13 — OpenClaw Bridge Real Callback MVP (PRD 草案)

> **Status:** Draft
> **Author:** CEO Agent (via AI Company OS v0.12.1)
> **Date:** 2026-05-29
> **Product Line:** AI Company OS
> **Previous:** v0.12 — Product Line Agents MVP
> **Next:** v0.14 — Skill Registry v2

---

## 1. Executive Summary

v0.13 establishes a **real callback bridge** between AI Company OS and OpenClaw — transforming OpenClaw from a task-card-producer into an **execution runtime** with result backfill.

### One-line Value

> CEO can assign Work Orders to OpenClaw, and the results come back.

### Why Now

- OpenClaw has a rich external API ecosystem — it can handle customer service, external data collection, content distribution, API integrations, and more
- OpenClaw is ready to be used as an **external execution runtime** — not just another chat agent, but a bridge to external tools and services
- v0.12.1 proved the product line operating cadence generates real Work Orders — OpenClaw needs to be able to accept and complete them, regardless of task type
- The current OpenClaw Bridge (v0.10) only creates task cards; it does NOT receive results back
- A generic bridge means OpenClaw can handle any task type: customer response, data research, content publishing, monitoring, notification, etc.

---

## 2. Target Chain

```
CEO / Work Order
    → OpenClaw Task Card (with goal, context, expected output, allowed actions)
    → OpenClaw executes (autonomously)
    → Output Artifact (file, summary, structured data)
    → Result backfill to Work Order (status, output_path, result_summary)
    → CEO Summary
```

---

## 3. Core Requirements

### 3.1 OpenClaw Task Card — Enhanced

The existing task card (v0.10 `openclaw_bridge.py`) must be extended with:

| Field | Type | Description |
|:------|:-----|:------------|
| `card_id` | string | UUID, matches WO ID |
| `goal` | text | The task objective, verbatim from Work Order |
| `context` | text | Input context for execution |
| `expected_output` | text | What OpenClaw should produce |
| `allowed_actions` | string[] | What OpenClaw is permitted to do (read, write, search, respond) |
| `skill_constraints` | string[] | Which Hermes skills OpenClaw may delegate to |
| `report_back_path` | string | Where to write the result artifact |

### 3.2 Result Backfill Mechanism

When OpenClaw completes a task, it must:

1. Write the output artifact to a known path (`~/.ai-company-os/artifacts/<WO-ID>/`)
2. Update the Work Order with:
   - `status` → `completed` or `failed`
   - `output_path` → path to artifact
   - `result_summary` → 1-3 sentence summary
   - `artifacts_json` → list of output files
   - `completed_at` → timestamp

### 3.3 CEO Summary Integration

After all Work Orders in a Goal Session are completed (by OpenClaw or otherwise), the CEO Orchestrator must generate a summary that includes OpenClaw-executed tasks.

### 3.4 OpenClaw Runtime Contract (Inbox/Outbox)

The bridge uses a **shared filesystem** for job dispatch and result collection. This keeps the MVP lean — no HTTP protocol changes needed on the OpenClaw side.

```
~/.ai-company-os/openclaw/
├── inbox/                          ← AI Company OS writes task.json here
│   └── WO-xxx.task.json
├── working/                        ← OpenClaw moves task here when claimed
│   └── WO-xxx.task.json
└── logs/                           ← Optional: runtime logs from OpenClaw
    └── WO-xxx.log
```

**Lifecycle:**
1. `AI Company OS` writes `WO-xxx.task.json` to `inbox/`
2. `OpenClaw` scans `inbox/`, picks up the task
3. `OpenClaw` moves the task to `working/` or writes a `claimed_at` marker
4. `OpenClaw` executes and writes `result.json` + output files to `~/.ai-company-os/artifacts/WO-xxx/`
5. `AI Company OS` polls `artifacts/WO-xxx/result.json` — if it exists, the task is done
6. `AI Company OS` backfills the Work Order and removes the task from `working/`

### 3.5 Task Card Schema

The task card is written as `WO-xxx.task.json` with the following schema:

```json
{
  "card_id": "WO-xxx",
  "work_order_id": "WO-xxx",
  "goal_session_id": "GS-xxx",
  "product_line_id": "ai-company-os",
  "task_type": "customer_response",
  "goal": "回答用户关于利润体检报告的问题",
  "context": "产品：Amazon利润体检报告; 目标用户：月销50-200万卖家",
  "expected_output": "response-draft.md",
  "allowed_actions": ["read_faq", "write_response"],
  "forbidden_actions": ["send_email", "deploy", "delete_file", "modify_code"],
  "allowed_tools": ["faq_reader"],
  "report_back_path": "~/.ai-company-os/artifacts/WO-xxx/",
  "timeout_seconds": 300,
  "risk_level": "low",
  "requires_human_review": true,
  "created_at": "2026-05-29T..."
}
```

Note: `skill_constraints` is intentionally absent — OpenClaw should NOT delegate to Hermes Skills in v0.13. That cross-runtime loop belongs in v0.14+.

### 3.6 Result Manifest Schema

OpenClaw MUST write `result.json` when done. Without this file, the task is not considered complete.

```json
{
  "work_order_id": "WO-xxx",
  "status": "completed",
  "result_summary": "已完成任务，生成 3 个产物。",
  "artifacts": [
    {
      "name": "customer-response-draft.md",
      "path": "~/.ai-company-os/artifacts/WO-xxx/customer-response-draft.md",
      "type": "markdown"
    }
  ],
  "confidence": 0.87,
  "unresolved_questions": ["用户还问了API接入时间"],
  "recommended_follow_up": "建议 Founder 审阅后发送。",
  "metadata": {
    "runtime": "openclaw",
    "agent": "customer-support-agent",
    "tokens_used": 450
  },
  "completed_at": "2026-05-29T18:30:00Z"
}
```

**Rules:**
- `poll_results()` ONLY checks for `result.json` — never guesses based on arbitrary new files
- If `result.json` is malformed or missing required fields → status = `needs_review`
- If `result.json` contains `status: "failed"` → WO status = `failed`, error extracted

### 3.7 Execution State Rules

The Work Order `execution_log_json` field records OpenClaw-specific state transitions:

| State | When | Trigger |
|:------|:-----|:--------|
| `dispatched_to_openclaw` | Task card written to inbox | After `create_task_card()` |
| `claimed_by_openclaw` | Task moved from inbox to working | OpenClaw picks up task |
| `running` | OpenClaw started execution | OpenClaw writes `started_at` |
| `completed` | `result.json` found with status=completed | `poll_results()` |
| `failed` | `result.json` found with status=failed | `poll_results()` |
| `timeout` | No result within `timeout_seconds` | Background timer |
| `needs_review` | Malformed result, or confidence < threshold | `poll_results()` |

**Timeout behavior:**
- OpenClaw offline → task stays `dispatched` for 5 min → `timeout`
- OpenClaw claimed but no progress for 5 min → `timeout`  
- Result format invalid → `needs_review` (not failed — manual review)

These states are stored in `execution_log_json`, NOT as new Work Order status values — the Work Order's own `status` field stays as `in_progress` until the final outcome.

### 3.8 Safety Rules

| Rule | Applies to | Enforcement |
|:-----|:-----------|:------------|
| Customer service tasks produce **drafts only** — never auto-send | `task_type: customer_response` | `requires_human_review: true` |
| Deployment tasks produce **checklist only** — never execute shell | `task_type: deploy` | `execution_mode: checklist_only` \\
| Code tasks still go through **Code Bridge** — no direct code modification | `task_type: code_build` | `OpenClaw` cannot have `modify_code` in `allowed_actions` |
| High-risk actions must return to **Approval** | `risk_level: high` | Inherited from v0.10 — WO stays `requires_approval` |
| OpenClaw cannot call external paid APIs without explicit config | All | Configurable allowlist in `openclaw_bridge.py` |

---

## 4. Acceptance Scenarios

### Scenario A: External Interaction Draft (Primary)

Generic pattern — OpenClaw uses external APIs or knowledge sources to generate a draft response, then writes back. **The output is always a draft — never auto-sent.**

**Example — Customer Service FAQ Response:**
```
Founder/CEO: "让 OpenClaw 客服 Agent 根据项目 FAQ 回答用户关于利润体检报告的问题"

WO Input:
  - task_type: "customer_response"
  - input_context: "用户问：利润报告支持哪个站点的数据？"
  - expected_output: "response-draft.md"
  - allowed_actions: ["read_faq", "write_response"]

OpenClaw Output:
  - customer-response-draft.md (回答草稿)
  - confidence: 0-1 分
  - unresolved_questions: ["用户还问了API接入时间"]
  - recommended_follow_up: "建议预约演示"

Work Order Backfill:
  - status: "completed"
  - output_path: "~/.ai-company-os/artifacts/WO-XXX/customer-response-draft.md"
  - result_summary: "已根据 FAQ 生成回答草稿，覆盖用户2/3问题"
```

### Scenario B: Research / Execution Task

```
CEO: "让 OpenClaw 整理 AI Seller Finance 目标用户常见问题"

WO Input:
  - task_type: "research"
  - input_context: "产品：Amazon利润体检报告; 目标用户：月销50-200万卖家"
  - expected_output: "research-summary.md"
  - allowed_actions: ["read_knowledge_base", "write_report"]

OpenClaw Output:
  - research-summary.md (Top 10 FAQs)
  - source-notes.md
  - next-actions.md

Work Order Backfill:
  - status: "completed"  
  - output_path: "~/.ai-company-os/artifacts/WO-YYY/"
  - result_summary: "已整理10个高频问题，建议补充实操数据"
```

---

## 5. Non-Goals (Explicitly Out of Scope)

| Item | Note |
|:-----|:-----|
| ❌ Free-form chat between CEO and OpenClaw | Not a conversation, it's a task contract |
| ❌ Multi-agent orchestration | No autonomous OpenClaw → Hermes → OpenClaw loops |
| ❌ Complex bidirectional protocol | Single direction: WO → Task Card → Artifact → Backfill |
| ❌ OpenClaw runtime restructuring | No changes to OpenClaw core |
| ❌ Auto-approval for high-risk tasks | Code Bridge requires manual approval (inherited from v0.10) |
| ❌ Real-time streaming results | Backfill happens on completion, not incremental |
| ❌ OpenClaw skills integration into Hermes Skill Registry | Separate concern for v0.14 — OpenClaw does NOT delegate to Hermes Skills in v0.13 |
| ❌ Cross-runtime Hermes ↔ OpenClaw delegation loops | `skill_constraints` intentionally excluded from Task Card schema |

---

## 6. Technical Approach

### 6.1 Architecture (Minimal Change)

```
WorkOrderExecutor
    → openclaw_bridge.create_task_card(wo)
    → [OpenClaw polls/dispatches the card]
    → OpenClaw writes result to ~/.ai-company-os/artifacts/<WO-ID>/
    → openclaw_bridge.poll_results()  [new — periodic check]
    → WorkOrder.update() with results
    → CEO Orchestrator.get_goal_session_summary()
```

### 6.2 Files to Change

| File | Change |
|:-----|:-------|
| `backend/app/services/openclaw_bridge.py` | Add `poll_results()` + enhanced task card creation |
| `backend/app/services/work_order_executor.py` | Add `execution_mode = "openclaw_bridge"` handler |
| `backend/app/routers/work_orders.py` | Add callback endpoint for OpenClaw to POST results |
| `backend/app/services/ceo_orchestrator.py` | Update goal session summary to include OpenClaw results |

### 6.3 New Endpoint

```
POST /api/v1/work-orders/{wo_id}/openclaw-callback
Body: {
  "status": "completed",
  "output_path": "...",
  "result_summary": "...",
  "artifacts": [...],
  "confidence": 0.95,
  "metadata": {...}
}
```

### 6.4 Polling vs Callback

**Phase 1 (MVP): Polling** — `openclaw_bridge.poll_results()` checks `~/.ai-company-os/artifacts/<WO-ID>/` for new files every N seconds. Simple, no OpenClaw changes needed.

**Phase 2 (Post-MVP): Callback** — OpenClaw POSTs to `/api/v1/work-orders/{wo_id}/openclaw-callback`. Requires OpenClaw to support webhook-style callback. **Prefer this for final implementation.**

Decision: **Start with polling (Phase 1), design API for callback (Phase 2).**

---

## 7. Success Criteria

| Criterion | Measurement |
|:----------|:------------|
| Task card → execution → backfill completes | Interaction tasks (draft): < 5 min; Research tasks: < 15 min |
| Artifact visible in Work Order detail | `GET /work-orders/{id}` returns `output_path` and `result_summary` |
| CEO summary includes OpenClaw results | `GET /ceo/goal-sessions/{id}` shows OpenClaw-executed WOs |
| External interaction draft scenario passes | Scenario A acceptance test (customer service example) |
| Research scenario passes | Scenario B acceptance test |
| No regression in existing Work Order flow | Existing `direct_delegate` and `code_bridge` modes still work |
| Timeout rules work | Task moves to `timeout` if unclaimed > 5 min |
| Malformed result handling | Malformed `result.json` → WO status = `needs_review` |
| Idempotent callback | Duplicate callback does not overwrite completed status |

---

## 8. Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|:-----|:-----------|:-------|:-----------|
| OpenClaw produces malformed output | Medium | Medium | Schema validation + fallback to "review required" status |
| Polling interval too slow | Low | Low | Configurable interval, default 30s |
| OpenClaw task card not picked up | Low | High | Logging + timeout alert after 5 min |
| Result backfill conflicts with manual update | Low | Medium | Write-once with WAL locking |

---

## 9. Implementation Estimate

| Phase | Effort | Description |
|:------|:-------|:------------|
| Phase 1: Polling bridge | 4-6 hours | Enhanced task card + inbox/outbox + `poll_results()` + WO update |
| Phase 2: Callback API | 2-3 hours | POST endpoint + API key auth + idempotency + OpenClaw integration |
| Testing | 2-3 hours | Scenario A + Scenario B + timeout + malformed result + regression |
| **Total** | **8-12 hours** | Lightweight MVP |

---

## 10. Appendices

### A. Related Evidence

- `backend/app/services/openclaw_bridge.py` — current v0.10 implementation
- `evidence/product-lines/weekly-status/company-weekly-brief.md` — context for why this v0.13 is needed
- `launch-pipeline/runs/LR-001-amazon-profit-health-check/launch-evidence.md` — existing product needing support

### B. Open Questions

1. Should OpenClaw run as a Hermes skill or as an independent runtime? → **Independent runtime** with shared filesystem contract
2. How does OpenClaw authenticate to the AI Company OS API? → API key in callback phase; shared filesystem in polling phase
3. What happens if OpenClaw is offline when a Work Order is assigned? → Work Order stays `dispatched`, timeout after 5 min → `timeout`
4. Who creates the `~/.ai-company-os/openclaw/` directory structure? → `openclaw_bridge.py` on first `create_task_card()` call

---

*PRD Draft generated by CEO Agent — AI Company OS v0.12.1 Product Line Operating Cadence*
