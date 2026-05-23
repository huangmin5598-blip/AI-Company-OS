# Memory Recall Skill — Example

> **Hermes skill for organizational memory recall during CEO Agent goal intake.**
> This is an example file. The actual skill is deployed locally.

## Purpose

Before the CEO Agent runs goal intake, this skill automatically recalls relevant organizational memory to enrich the context pack.

## Workflow

```
Goal Intake triggered
  → /memory/recall?q={goal_keywords}&top_k=3
    → Returns org_memory entries matching the goal
      → Writes referenced_memory_ids into context_pack
        → Continues with task generation
```

## Example

```
Founder: "Build a monitoring system for our agents"

Memory Recall:
- Match 1: "Alert auto-pooling mechanism (v0.2 delivery)"
- Match 2: "Monitor agent design rejected — use lightweight probes instead"
- Match 3: "Learning candidate: agent runtime error rate > 5% triggers review"

These 3 references are attached to the context pack for the monitoring tasks.
```

## Why this matters

Without memory recall, the CEO Agent would generate tasks from scratch every time — missing past decisions, rejected approaches, and accumulated knowledge.
