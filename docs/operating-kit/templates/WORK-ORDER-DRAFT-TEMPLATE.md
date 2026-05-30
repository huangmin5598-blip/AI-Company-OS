---
title: "Work Order Draft Template — AI Company OS 工单草稿模板"
domain: operating-kit
---

# Work Order Draft

**Draft ID:** {WO-DRAFT-YYYYMMDD-NNN}
**Source Brief:** {reports/ceo-briefs/YYYY-MM-DD.md}
**Source Decision:** {DEC-YYYYMMDD-NNN}
**Decision Type:** {maintenance | business | research | system}
**Risk Level:** {low | medium | high}
**Approval Required:** {true | false}
**Created:** {timestamp}

---

## Auto-filled Title

{title_from_decision}

---

## Founder To Fill

**Suggested Task Type:**
```
TODO: Founder to fill
e.g. market_intelligence, report_generation, code_change, system_maintenance
```

**Suggested Skill:**
```
TODO: Founder to fill
e.g. research_summary, finance_analysis, code_change
```

**Suggested Agent:**
```
TODO: Founder to fill
e.g. research-agent, codex-agent, hermes-main
```

**Proposed Prompt:**
```
TODO: Founder to fill
Detailed instructions for the executing agent.
```

**Expected Output:**
```
TODO: Founder to fill
What successful output looks like (Markdown report, code PR, analysis).
```

---

## Founder Confirmation

- [ ] approve_create_work_order (确认创建 Work Order)
- [ ] edit_required (需要修改)
- [ ] dismiss (放弃此草稿)

---

## Notes

_{Optional notes from Founder}_


---

## Execution Result

_(Populated automatically by `wait-result --sync-source`)_

| Field | Value |
|-------|-------|
| Status | {completed | failed} |
| WO ID | {work_order_id} |
| Executed At | {timestamp} |
| Summary | {result_summary} |

---

_draft_status: draft_
