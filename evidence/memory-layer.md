# Evidence: Memory Layer — How the System Remembers

## What is Memory Layer?

Memory Layer is the system mechanism that automatically captures, categorizes, and persists all task outputs as company assets. It's not just logging — it's structured asset accumulation.

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

### 2. asset_processor

This component classifies the output and determines its asset type:

| Output Format | Asset Type |
|--------------|------------|
| .md / .docx | content |
| .pdf / .pptx | document |
| .py / .js | code |
| protocol/workflow | system |
| research card | knowledge |

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

### 4. memory/YYYY-MM-DD.md

Daily log for session context:

```markdown
## 2026-03-31

### novel-v1
- novel-23: completed (PASS)
- novel-24: completed (PASS)

### research-agent
- Week 15: completed (3 cards)
```

## Supported Asset Types

| Type | Examples | Storage |
|------|----------|---------|
| content | novels, articles, scripts | manuscripts/ |
| document | reports, proposals | reports/ |
| system | protocols, workflows | docs/ |
| code | modules, scripts | code/ |
| knowledge | research cards, opportunity cards | memory/ |

## How to接入 a New Project

1. Define asset types in CAPABILITY-REGISTRY.md
2. Ensure task_completed triggers asset_processor
3. Configure storage paths
4. Asset automatically registered

## Why This Matters

Without Memory Layer:
- Outputs are one-off
- Nothing is traceable
- Can't build on past work
- No company memory

With Memory Layer:
- All outputs visible
- Searchable by project/date/type
- Reusable for future tasks
- Assets accumulate over time

## Related Files

- `/memory/execution-records.json`
- `/CAPABILITY-REGISTRY.md`
- `/memory/2026-03-31.md`

---

*Evidence: Memory Layer | 2026-03-31*
