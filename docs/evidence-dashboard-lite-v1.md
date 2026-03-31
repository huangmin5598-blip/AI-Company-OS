# Evidence Dashboard Lite V1

## Planning Document

**Version**: 1.0
**Date**: 2026-03-31
**Status**: Planning

---

## Purpose

The evidence-dashboard-lite-v1 is not a new system.

It is the **external evidence display layer** that transforms internal AI Company OS capabilities into externally understandable, verifiable, and trustworthy information.

**Core goal:** Let external users see at a glance:
- System is running
- Projects are advancing
- Assets are growing
- Governance mechanisms are working

---

## Why Now

### Internal capabilities are ready

| Capability | Status | Ready for display? |
|------------|--------|---------------------|
| Multi-agent execution | ✅ Verified | Yes |
| Memory Layer + Registry | ✅ Operational | Yes |
| Gateway Lite | ✅ Running | Yes |
| Capability Registry | ✅ Validated | Yes |
| Routing Layer | ✅ Validated | Yes |
| Control Center | ✅ P0 Complete | Yes |

### External gap exists

Currently:
- System can do significant things
- But external users cannot verify
- Creates "invisible" perception
- Limits trust and adoption

### Next logical step

The system has completed "building internally."  
The next stage is "displaying externally."

The evidence dashboard bridges this gap.

---

## Target Audience

1. **Prospective users** - Evaluating if AI Company OS is real and working
2. **Potential investors** - Assessing system maturity and progress
3. **Partners** - Understanding system capabilities and reliability
4. **Internal stakeholders** - Getting quick system overview

---

## Core Modules

### Module 1: System Running

**What it shows:**
- System health status (up/down/recovering)
- Latest build logs (last 3-5 entries)
- Heartbeat status (last execution time)
- Recent execution activity

**Data sources:**
- control-center/System Health
- docs/build-logs/
- heartbeat status
- execution-records.json

**Why it matters:**
Proves the system is alive and running, not just a concept.

---

### Module 2: Project Progress

**What it shows:**
- Active projects list
- Current stage of each project
- Recent outputs from each project
- Recent validations/completions

**Data sources:**
- control-center/Project Board
- TASK-POOL.md
- projects/*/README.md

**Why it matters:**
Shows real projects executing, not just abstract capabilities.

---

### Module 3: Asset Growth

**What it shows:**
- Asset counts by type (content/document/code/knowledge/system)
- Latest additions (last 5-10 items)
- Registry growth over time

**Data sources:**
- Memory Layer / Registry
- assets/ (5 asset files)
- execution-records.json

**Why it matters:**
Demonstrates asset accumulation is happening, not just task completion.

---

### Module 4: Governance & Control

**What it shows:**
- Gateway summary (model calls, costs, fallbacks)
- Routing summary (rules, hit rates)
- Capability overview (agent registry mapping)
- CEO escalation summary (priority items)

**Data sources:**
- control-center/Gateway Summary
- control-center/Routing Summary
- control-center/Capability Overview
- control-center/CEO Escalation Summary

**Why it matters:**
Proves governance mechanisms are working, not just executing tasks.

---

### Module 5: Monetization (Optional)

**What it shows:**
- Commercial progress
- Product/ Pricing updates
- Payment/Revenue milestones

**Data sources:**
- logs/monetization-log.md

**When to include:**
Only when commercial progress exists and is appropriate to display.

---

### Module 6: Milestones (Optional)

**What it shows:**
- Major validations completed
- System stage transitions
- Key achievements

**Data sources:**
- evidence/system-evolution.md
- docs/build-logs/

**When to include:**
When significant milestones need highlight.

---

## MVP Scope

### Must have (MVP)

| Module | Priority | Display format |
|--------|----------|----------------|
| System Running | P0 | Status indicators + latest logs |
| Project Progress | P0 | Project list + stages + recent outputs |
| Asset Growth | P0 | Counts by type + latest additions |
| Governance & Control | P0 | Gateway + Routing + Capability + Escalation |

### Out of scope (V1)

- Real-time streaming data
- Interactive charts/graphs
- Historical trend analysis
- User authentication/authorization
- Multi-page navigation

---

## Data Sources Summary

| Module | Primary Source | Update Frequency |
|--------|----------------|------------------|
| System Running | control-center/System Health | Real-time / Daily |
| Project Progress | control-center/Project Board + TASK-POOL | Real-time / Daily |
| Asset Growth | Registry + assets/ | On asset registration |
| Governance | control-center modules | Real-time / Daily |

---

## Display Principles

1. **Evidence over claims** - Show data, not promises
2. **Trust through transparency** - Let users verify
3. **Simplicity first** - MVP is better than complex
4. **Consistency** - Same update rhythm as internal systems
5. **No exaggeration** - Show real state, not inflated

---

## Implementation Notes

### Not a new system
- Uses existing data sources
- Reuses control-center components
- Does not require new backend

### Display medium
- Could be static page (Markdown/HTML)
- Could be dynamic (API + frontend)
- MVP: Static page is sufficient

### Update mechanism
- Follows GitHub continuous update SOP
- Updates when new evidence exists
- Minimum: Weekly refresh

---

## Success Criteria

- [ ] External users can verify system is running
- [ ] Project progress is observable
- [ ] Asset growth is trackable
- [ ] Governance mechanisms are demonstrable
- [ ] Dashboard builds trust and confidence

---

## Next Steps

1. Confirm module list (4 or 6)
2. Choose display format (static/dynamic)
3. Identify data pipeline
4. Build MVP display
5. Integrate with GitHub update flow

---

*Planning Document | 2026-03-31*