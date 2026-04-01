# OS Capability Project Pool

**Version**: 1.0 (Official)
**Created**: 2026-04-01
**Owner**: CEO (main)
**Operator**: lead-os

---

## 一、Ownership 结构

| Role | Responsibility |
|------|----------------|
| **CEO (main)** | Owner of AI Company OS capability building line |
| **lead-os** | Execution lead / PM for OS capability projects |

---

## 二、Current OS Capability Projects

| # | Project | Owner | Stage | Next Stage | Operational Status | Freeze Rule | End State |
|---|---------|-------|-------|------------|-------------------|-------------|-----------|
| 1 | **gateway-lite-v1** | tiger-coder | MVP | P1 | Running | Complete P1 before freeze | Cost governance, fallback tracking, daily reporting |
| 2 | **control-center-v1** | tiger-coder | P0 | P1 | Completed | Complete P1 before freeze | 7 modules: Project Board, Agent Status, System Health, Gateway Summary, Capability Overview, Routing Summary, CEO Escalation |
| 3 | **capability-registry-v1** | tiger-coder | P0 | P1 | Completed | Complete P1 before freeze | Complete Agent/Project capability map, integrated with routing-layer |
| 4 | **routing-layer-v1** | tiger-coder | P0 | P1 | In Progress | Complete P1 before freeze | Semantic routing rules layer (founder_input, project_input, timeout, task_completed), independent routing service |
| 5 | **checkpoint-resume-v1** | tiger-coder | P0 | P1 | In Progress | Complete P1 before freeze | Resume from checkpoint instead of restart after timeout |
| 6 | **preflight-diagnostics-v1** | lead-os | P0 | P1 | Planning | Complete P1 before freeze | Pre-task health checks, system validation before execution |
| 7 | **evidence-dashboard-lite-v1** | tiger-coder | P0 | P1 | Completed | Complete P1 before freeze | Public evidence layer: Project Board, Agent Status, Run Flow, Asset Growth, Gateway Summary |

---

## 三、Project Status Definitions

### roadmap_stage

| Stage | Description |
|-------|-------------|
| P0 | MVP / Proof of concept - Core functionality built |
| P1 | Iteration / Enhancement - Add features, stabilize |
| P2 | Production - Ready for production use |
| P3 | Maintenance - Long-term maintenance mode |

### operational_status

| Status | Description |
|--------|-------------|
| Planning | Project being planned |
| In Progress | Actively being built |
| Completed | Core functionality done |
| Running | In production use |
| Paused | Temporarily halted |
| Frozen | No longer actively developed |
| Cancelled | Stopped with reasons documented |

### freeze_rule

- Projects must complete P1 before being frozen
- Frozen projects must document reason
- No project should "naturally disappear" after P0

---

## 四、routing-layer-v1 Direction

**Approach**: Borrow base layer + build semantic rules

### Reuse from OpenClaw

- Gateway event ingestion
- WebSocket / RPC communication
- Agent status display
- Routing & health event frontend

### AI Company OS Focus (Own)

- Founder input / project input / system input classification
- Route type / route reason / next agent / escalation to semantics
- Timeout → resume / fallback / main_rescue rules
- Memory Layer / Registry / Evidence Layer integration
- Capability Registry / Project Flow rules

---

## 五、Weekly OS Review

### Review Frequency

- **Every Sunday 20:00** (or first working day)
- Separate from normal project review

### Review Checklist

1. Which OS projects are in P0 / P1 / P2?
2. Which projects have entered stable running?
3. Which projects are blocked?
4. Which projects need upgrade?
5. Which projects should be frozen?
6. Which need OS Radar / Skills Gap Review input?
7. Which projects completed P0 but have no next step?

### Weekly Output

- OS Progress Summary
- Project Status Table
- Blockers
- Upgrade / Freeze Decision Recommendations

---

## 六、Project Lifecycle Rules

### After P0 Completion

Every project must move to one of:

1. **Stable Running** - In production, working as expected
2. **Upgrade to P1** - Continue iteration
3. **Frozen** - Documented reason required

**Prohibited**: "Complete minimum version, then naturally disappear"

### Decision Authority

- CEO makes final decision on upgrade / freeze
- lead-os prepares recommendations and materials

---

## 七、Next Steps

1. ✅ Ownership structure confirmed
2. ⏳ lead-os agent creation (in progress)
3. ⏳ All OS projects receive required fields (in progress)
4. ⏳ Weekly OS Review schedule (first review: 2026-04-06)
5. ⏳ routing-layer-v1 semantic layer design

---

## Registry

| Field | Value |
|-------|-------|
| current_version | 1.0 |
| last_updated | 2026-04-01 |
| owner | CEO (main) |
| operator | lead-os |

---

*This document is the authoritative source for OS capability project tracking.*