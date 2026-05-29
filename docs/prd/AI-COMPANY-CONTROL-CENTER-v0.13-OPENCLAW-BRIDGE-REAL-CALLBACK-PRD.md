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

- OpenClaw is ready to be used as a **customer service agent** — answering user questions, generating response drafts
- v0.12.1 proved the product line operating cadence generates real Work Orders — OpenClaw needs to be able to accept and complete them
- The current OpenClaw Bridge (v0.10) only creates task cards; it does NOT receive results back

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

---

## 4. Acceptance Scenarios

### Scenario A: Customer Service Task (Primary)

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
| ❌ OpenClaw skills integration into Hermes Skill Registry | Separate concern for v0.14 |

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
| Task card → execution → backfill completes | < 5 min end-to-end |
| Artifact visible in Work Order detail | `GET /work-orders/{id}` returns `output_path` and `result_summary` |
| CEO summary includes OpenClaw results | `GET /ceo/goal-sessions/{id}` shows OpenClaw-executed WOs |
| Customer service scenario passes | Scenario A acceptance test |
| Research scenario passes | Scenario B acceptance test |
| No regression in existing Work Order flow | Existing direct_delegate and code_bridge modes still work |

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
| Phase 1: Polling bridge | 4-6 hours | Enhanced task card + poll_results() + WO update |
| Phase 2: Callback API | 2-3 hours | POST endpoint + OpenClaw integration |
| Testing | 2-3 hours | Scenario A + Scenario B + edge cases |
| **Total** | **8-12 hours** | Lightweight MVP |

---

## 10. Appendices

### A. Related Evidence

- `backend/app/services/openclaw_bridge.py` — current v0.10 implementation
- `evidence/product-lines/weekly-status/company-weekly-brief.md` — context for why this v0.13 is needed
- `launch-pipeline/runs/LR-001-amazon-profit-health-check/launch-evidence.md` — existing product needing support

### B. Open Questions

1. Should OpenClaw run as a Hermes skill or as an independent runtime? → **Independent runtime** with REST callback
2. How does OpenClaw authenticate to the AI Company OS API? → API key or shared filesystem in v0.13 MVP
3. What happens if OpenClaw is offline when a Work Order is assigned? → Work Order stays `assigned`, retries with timeout

---

*PRD Draft generated by CEO Agent — AI Company OS v0.12.1 Product Line Operating Cadence*
