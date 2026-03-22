# Production Protocol

## Overview

How we produce outputs — code, content, or products — in a repeatable way.

---

## Production Flow

```
Task Created → Assigned → Executed → Reviewed → Delivered → Archived
```

---

## Daily Production (novel-v1)

**Target**: 2 stories per day

**Process**:
1. Heartbeat checks at 09:00
2. Generates 2 new tasks
3. Tasks go through pipeline
4. Review validates
5. Export to docx

**Failure Handling**:
- If no task generated → Heartbeat auto-creates
- If review fails → Revision (max 1)
- If stuck → Marked BLOCKED

---

## Project Production (hub-v1)

**Trigger**: Manual or milestone-based

**Process**:
1. Lead creates task cards
2. CEO dispatches to tiger-coder
3. Execution happens
4. Lead reviews
5. Deliverable exported

---

## Quality Gates

| Gate | Who | What |
|------|-----|------|
| Planning | Lead | Task breakdown |
| Execution | Tiger-coder | Deliverable |
| Review | Lead | PASS/REVISION/BLOCKED |

---

## Examples

### Daily Content
- novel-v1: 2 stories/day
- Story goes through:选题 → 大纲 → 写作 → 审核 → 导出

### Feature Build
- hub-v1: Add new page
- Goes through: Spec → Code → Review → Deploy

---

## Limitations

- Not all projects fit the pipeline
- Some tasks need human creativity
- Review can become bottleneck
