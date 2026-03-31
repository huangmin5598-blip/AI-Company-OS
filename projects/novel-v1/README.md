# Novel-V1 Project Overview

## Project Goal

Short story production: Generate and publish quality short stories on a daily basis.

**Target**: 2 stories/day, 14 stories/week

## Pipeline

```
lead-novel (选题/调度)
  → story-editor (大纲/结构)
    → writer (正文写作)
      → review-editor (质量审核)
        → export (docx/持久化)
```

## Running Status

| Date | Target | Completed | Output |
|------|--------|-----------|--------|
| 2026-03-31 | 2 | 2 | novel-23, novel-24 |
| 2026-03-30 | 2 | 2 | novel-21, novel-22 |

## Current Output

All outputs stored in `/manuscripts/` as both .md and .docx formats.

## System Integration

- Uses **CAPABILITY-REGISTRY** for agent capability mapping
- Uses **ROUTING-RULES** for task dispatch
- Uses **checkpoint-resume** for timeout recovery
- Uses **Memory Layer** for output persistence

---

*Project: Novel-V1 | 2026-03-31*
