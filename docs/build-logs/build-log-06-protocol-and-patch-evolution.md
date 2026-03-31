# Build Log 06: Protocol and Patch Evolution — From Ad-Hoc Fixes to System Capabilities

**Build Log**: 06-protocol-and-patch-evolution
**Date**: 2026-03-31
**Status**: Completed

---

## Background

### What happened?

Over the course of system development, we encountered issues, fixed them, and gradually formalized solutions into protocols. This log tracks that evolution — from one-off patches to system-level capabilities.

Key question: When does a fix become a capability?

---

## Setup / Change

### Categorization of changes

| Category | Description | Example |
|----------|-------------|---------|
| Ad-hoc fix | One-time solution | Fix a specific error |
| Protocol | Documented process | production.md |
| System capability | Built-in mechanism | checkpoint-resume |
| Patch | Temporary workaround | Config change |

---

## Execution / What was done

### 1. From timeout issues to checkpoint-resume (System Capability)

**Problem**: Writer times out, entire chain restarts
**Fix**: Checkpoint at task-init, structure, draft-progress
**Evolution**: Now a standard system capability (Build Log 02)
**Status**: ✅ System capability, not a patch

### 2. From manual dispatch to capability-based routing (System Capability)

**Problem**: Manually telling each agent what to do
**Fix**: Capability registry + routing layer
**Evolution**: Now automatic dispatch based on capability mapping
**Status**: ✅ System capability

### 3. From sporadic reporting to automated digest (Protocol)

**Problem**: Manual daily reports
**Fix**: Daily/weekly digest in execution-records.json
**Evolution**: Standard reporting protocol
**Status**: ✅ Protocol

### 4. From one-off fallback to structured fallback (System Capability)

**Problem**: When agent fails, no recovery
**Fix**: fallback_agent + main_rescue
**Evolution**: Standard exception handling
**Status**: ✅ System capability

### 5. From scattered tasks to Task Pool (Protocol)

**Problem**: Can't see what tasks exist
**Fix**: TASK-POOL.md with structured task tracking
**Evolution**: Standard task management protocol
**Status**: ✅ Protocol

### 6. From project chaos to Project Lead structure (System Capability)

**Problem**: No coordination between agents
**Fix**: lead-* roles for planning, dispatch, acceptance
**Evolution**: Standard project organization (Build Log 03)
**Status**: ✅ System capability

---

## Results

### What we achieved

| Evolution | Before | After |
|-----------|--------|-------|
| Timeout handling | Manual restart | Checkpoint resume |
| Agent dispatch | Manual | Capability-based |
| Reporting | Manual | Automated digest |
| Failure recovery | Ad-hoc | Structured fallback |
| Task management | Scattered | TASK-POOL |
| Project coordination | Ad-hoc | Project Lead |

---

## Observations

### What we learned

1. **Every fix is a potential capability**: If a solution works, document it. If it works repeatedly, make it a protocol.

2. **Distinguish patch from capability**: A patch fixes a bug. A capability prevents a class of problems.

3. **Protocols need maintenance**: Protocols that aren't updated become stale.

4. **Layering matters**: Some fixes belong in agent code, some in OS layer.

---

## Operating Implications

### What this means for the system

We now have a systematic approach to capability building:

1. **Identify** recurring issue
2. **Solve** with minimal fix
3. **Validate** the solution works
4. **Formalize** into protocol or capability
5. **Integrate** into OS layer

This prevents "patch fatigue" and ensures the system improves over time.

---

## Related Files

- `/PROTOCOL.md`
- `/docs/protocols/production.md`
- `/docs/protocols/task-protocol.md`
- `/CAPABILITY-REGISTRY.md`
- `/ROUTING-RULES.md`
- `/checkpoint-resume` files

---

*Build Log 06 — Protocol and Patch Evolution | 2026-03-31*
