# Evidence: Memory Layer — How the System Remembers

**Date**: 2026-03-31

---

## What is Memory Layer?

Memory Layer is the system mechanism that automatically captures, categorizes, and persists all task outputs as company assets. It's not just logging — it's structured asset accumulation.

## Why We Built This

Early system: run task → get output → done. One-off. No trace.

Problem: Where did outputs go? What was produced? Could we build on past work?

**Memory Layer answers**: Every task completion triggers a chain that turns outputs into assets.

---

## Core Components

### 1. task_completed_event

When any task finishes, a structured event is triggered:

```json
{
  "event_type": "task_completed",
  "task_id": "novel-23",
  "project": "novel-v1",
  "agent": "writer",
  "output": { ... },
  "timestamp": "2026-03-31T08:00:00Z"
}
```

**Why this matters**: Single trigger point for all task completions. No matter what agent or project — all outputs flow through the same gate.

### 2. asset_processor

This component classifies the output and determines its asset type:

| Output Format | Asset Type |
|--------------|------------|
| .md / .docx | content |
| .pdf / .pptx | document |
| .py / .js | code |
| protocol/workflow | system |
| research card | knowledge |

**Why this matters**: Knowing "this is content" vs "this is code" changes how we can reuse it.

### 3. registry_writer

Writes the asset to central registry with standardized fields:

```json
{
  "asset_id": "novel-23",
  "asset_type": "content",
  "title": "重生千金虐渣打脸",
  "format": "docx",
  "source_project": "novel-v1",
  "source_agent": "writer",
  "created_date": "2026-03-31",
  "storage_path": "manuscripts/novel-23.md"
}
```

**Why this matters**: Standardized fields enable search, query, and reuse.

---

## Supported Asset Types

| Type | Examples | Storage |
|------|----------|---------|
| content | novels, articles, scripts | manuscripts/ |
| document | reports, proposals | reports/ |
| system | protocols, workflows | docs/ |
| code | modules, scripts | code/ |
| knowledge | research cards, opportunity cards | memory/ |

---

## How New Projects接入

1. Define asset types in CAPABILITY-REGISTRY.md
2. Ensure task_completed triggers asset_processor
3. Configure storage paths
4. Asset automatically registered

---

## What This Means for the System

**Without Memory Layer**:
- Outputs are one-off
- Nothing is traceable
- Can't build on past work
- No company memory

**With Memory Layer**:
- All outputs visible
- Searchable by project/date/type
- Reusable for future tasks
- Assets accumulate over time

---

## Real Impact

| Metric | Before | After |
|--------|--------|-------|
| Outputs tracked | None | All |
| Asset search | Manual | Queryable |
| Reuse | Impossible | Possible |
| Company memory | None | Growing |

---

## Related Files

- `/CAPABILITY-REGISTRY.md` (asset type definitions)
- `/archive/memory/execution-records.json` (registry)
- `/assets/` (asset categories)

---

*Evidence: Memory Layer | 2026-03-31*
