---
title: "Decision Log Template — AI Company OS 决策日志模板"
domain: operating-kit
---

# CEO Brief — Decision Log

_Auto-generated. Append-only._
_Created: {timestamp}_

---

| Date | Decision ID | Source Brief | Summary | Decision | Notes | Logged At |
|------|-------------|--------------|---------|----------|-------|-----------|
| {date} | {DEC-YYYYMMDD-NNN} | {brief_path} | {decision_summary} | {founder_decision} | {notes} | {timestamp} |

---

## Decision Types

| Type | Meaning |
|:-----|:---------|
| `approve` | Founder approved the recommendation |
| `defer` | Founder deferred to a later date |
| `reject` | Founder rejected the recommendation |
| `create_work_order_later` | Founder agreed, but Work Order will be created separately |
| `Execution Completed` | System entry — Work Order finished execution |

---

## Lifecycle

```
Decision Logged
      │
      ├──→ approve → Work Order Draft (if applicable)
      ├──→ defer → (no action, marked as deferred)
      ├──→ reject → (no action, marked as rejected)
      ├──→ create_work_order_later → Draft generated in reports/work-order-drafts/
      │                                 │
      │                                 ▼
      │                           create-work-order command
      │                                 │
      │                                 ▼
      │                           Work Order created
      │                                 │
      │                                 ▼
      └──→ Execution Completed (auto-populated by wait-result --sync-source)
```

---

## Data Integrity

- **Append-only**: New entries are always appended at the bottom
- **Dedup**: Entries are skipped if brief_path + decision_id already exist
- **Conflict detection**: If the same Decision Item has conflicting checkboxes, the entry is marked `invalid_review`
- **Source traceable**: Every entry links back to its CEO Brief and (if applicable) Work Order

---

_document_status: reference_
