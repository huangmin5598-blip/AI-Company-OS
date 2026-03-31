# Build Log 02: Runtime Stability — Timeout, Fallback, and Serial Chain Verification

**Build Log**: 02-runtime-stability
**Date**: 2026-03-31
**Status**: Completed

---

## Background

### What was the problem?

Early system operation revealed several runtime stability issues:

1. **Timeout problems**: Agent tasks would hang or timeout without recovery
2. **No fallback mechanism**: When one agent failed, the entire chain stopped
3. **Serial chain fragility**: Multi-agent pipelines were fragile — one failure meant restart from scratch
4. **No checkpoint system**: No way to resume from intermediate progress

These weren't just "bugs" — they were fundamental system capabilities that needed to be built.

---

## Setup / Change

### What we changed

| Component | Change | Purpose |
|-----------|--------|---------|
| Timeout Configuration | Added tiered timeout (lead:3min, story:5min, writer:8min, review:3min) | Match timeout to task complexity |
| Fallback Mechanism | Implemented fallback_agent routing | When primary fails, try backup |
| Checkpoint System | Added 3 checkpoint types (task-init, structure, draft-progress) | Save progress for resume |
| Resume Logic | Implemented checkpoint-based resume | Resume from last valid progress |
| main_rescue | Added main agent rescue for unrecoverable failures | Human/AI backup for critical failures |

---

## Execution / What was done

### 1. Timeout Tiered Configuration

```python
timeout_config = {
    "lead-novel": "3min",
    "story-editor": "5min", 
    "writer": "8min",
    "review-editor": "3min"
}
```

### 2. Checkpoint System Implementation

```python
checkpoint_types = [
    "task-init",        # Task created
    "structure",        # Outline done
    "draft-progress"    # Draft in progress
]
```

### 3. Resume Logic

```python
def handle_timeout(agent_id, task_id):
    checkpoint = find_last_checkpoint(task_id)
    if checkpoint:
        resume_from_checkpoint(checkpoint)
        autonomy_status = "resumed"
    else:
        fallback_agent(agent_id)
    if fallback_fails:
        main_rescue()
        autonomy_status = "main_rescue"
```

---

## Results

### What we achieved

| Metric | Before | After |
|--------|--------|-------|
| Timeout recovery | Manual restart | Automatic resume |
| Fallback | None | Automatic backup agent |
| Chain restart | Full restart | Resume from checkpoint |
| main_rescue | ad-hoc | Structured with status tracking |

### Real-world验证

**Case: novel-26 (2026-03-31)**
- Writer timeout after 30s
- Checkpoint found: structure checkpoint (novel-26-structure-2026-03-31T08-11-03)
- Resume successful: continued from outline
- Output: 3500+ words (Chapter 1 of "密室解剖师")
- autonomy_status: "resumed"

---

## Observations

### What we learned

1. **Timeout isn't always failure**: Sometimes it just means the task needs more time. Checkpoint makes this safe.

2. **Fallback works for single-agent tasks**: When research-agent times out, retry works. For multi-agent chains, checkpoint is better.

3. **main_rescue is a safety net, not the goal**: The goal is autonomous completion. main_rescue should be rare.

4. **Serial chains can be resilient**: With checkpoint/resume, even 5-agent chains can recover from failures.

---

## Operating Implications

### What this means for the system

This isn't a one-off fix. It's a **system-level capability**:

- **Reliability**: Tasks that used to fail completely can now complete
- **Efficiency**: No need to restart entire chains
- **Observability**: autonomy_status field tracks how each task completed
- **Extensibility**: The checkpoint mechanism can be extended to new agent types

### Current limitations

- Checkpoint only works for text-based outputs
- Resume logic needs manual trigger for some edge cases
- Not all agents have full checkpoint support yet

---

## Next Step

- Extend checkpoint to more agent types
- Add automatic resume trigger (reduce manual intervention)
- Track checkpoint effectiveness over time

---

## Related Files

- `/novel-v1/checkpoints/PROJECT.md`
- `/docs/protocols/failure.md`
- `/archive/memory/execution-records.json` (autonomy_status tracking)

---

*Build Log 02 — Runtime Stability | 2026-03-31*
