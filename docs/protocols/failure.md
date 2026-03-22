# Failure Protocol

## Failure Types

| Type | Description |
|------|-------------|
| TRIGGER FAILURE | Heartbeat didn't run |
| PRODUCTION FAILURE | Task not created |
| FLOW FAILURE | Task stuck, not progressing |
| EXECUTION FAILURE | Agent timeout/fail |
| EXPORT FAILURE | No docx delivered |
| DATA FAILURE | Status inconsistent |

---

## Detection

System checks every heartbeat:
1. Did heartbeat run?
2. Are tasks created?
3. Are tasks progressing?
4. Are deliverables exported?

---

## Recovery

| Failure | Action |
|---------|--------|
| Trigger | Compensate run |
| Production | Auto-generate tasks |
| Flow | Next step detection |
| Execution | Retry (max 1) |
| Export | Force export |
| Data | Fix status |

---

## Compensation

If a cycle was missed:
1. Detect the gap
2. Create compensating tasks
3. Mark as "COMPENSATED TASK"

---

## Degradation

| Days Failed | Status |
|-------------|--------|
| 2 days | ⚠️ AT RISK |
| 3 days | 🔴 DEGRADED |
| 5 days | Suggest KILL |

---

## Example

```
Date: 2026-03-22
Failures: TRIGGER_FAILURE
Recovery: Compensate_Yesterday
Status: Recovered
```

---

## Why This Matters

- System must run without human help
- Failures will happen
- Recovery must be automatic
