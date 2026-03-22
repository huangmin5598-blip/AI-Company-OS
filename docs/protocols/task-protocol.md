# Task Protocol

## Task Lifecycle

```
待创建 → 待执行 → 执行中 → 待验收 → 已完成
```

---

## Task Card Fields

| Field | Required | Description |
|--------|----------|-------------|
| Task ID | Yes | Unique (hub-001) |
| Project ID | Yes | Parent project |
| Title | Yes | Short description |
| Description | Yes | What to do |
| Task Type | Yes | research/planning/execution/review |
| Priority | Yes | P0/P1/P2 |
| Owner | Yes | Who responsible |
| Acceptance Criteria | Yes | How to verify |
| Status | Yes | Current state |

---

## Task Creation

**Who**: Project Lead (lead-*)

**Process**:
1. Understand project goal
2. Break into tasks
3. Create task cards
4. Write to TASK-POOL.md

---

## Task Execution

**Who**: Execution Agent

**Process**:
1. Read task card
2. Execute work
3. Deliver output
4. Mark status

---

## Task Review

**Who**: Project Lead

**Result**:
- PASS → Mark completed
- REVISION → Return to execution (max 1)
- BLOCKED → Report to CEO

---

## Examples

### Good Task Card
```
Task ID: hub-001
Project: hub-v1
Title: Build homepage
Description: Create index.html with hero section
Acceptance Criteria: Page loads, no errors
Priority: P0
Owner: tiger-coder
Status: 待执行
```

### Bad Task Card
```
Task: "Make it better" ← Too vague
```

---

## Limitations

- Can't predict everything
- Some tasks need iteration
- Scope creep is real
