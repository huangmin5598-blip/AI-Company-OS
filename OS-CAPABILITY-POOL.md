# OS Capability Project Pool

**Version**: 1.1 (With Layered Ownership)
**Created**: 2026-04-01
**Updated**: 2026-04-01
**Owner**: CEO (main)

---

## 一、Ownership Structure (Layered)

| Layer | Role | Responsibility |
|-------|------|----------------|
| **Line Owner** | CEO (main) | Owns the entire OS capability building line |
| **Project Owner** | lead-os | Drives OS projects, tracks progress, ensures continuity |
| **Executor** | tiger-coder (specific agent) | Executes specific implementation tasks |

**Why this layering:**

- CEO owns the line → won't let OS capability line be swallowed by real projects
- lead-os drives projects → won't let projects "naturally disappear" after P0
- tiger-coder executes → handles specific implementation

---

## 二、Current OS Capability Projects

| # | Project | Line Owner | Project Owner | Executor | Stage | Next Stage | Operational Status | Freeze Rule | End State |
|---|---------|-----------|---------------|----------|-------|------------|-------------------|-------------|-----------|
| 1 | **gateway-lite-v1** | main | lead-os | tiger-coder | MVP | P1 | Running | Complete P1 before freeze | Cost governance, fallback tracking |
| 2 | **control-center-v1** | main | lead-os | tiger-coder | P0 | P1 | Completed | Complete P1 before freeze | 7 modules operational |
| 3 | **capability-registry-v1** | main | lead-os | tiger-coder | P0 | P1 | Completed | Complete P1 before freeze | Complete Agent/Project map |
| 4 | **routing-layer-v1** | main | lead-os | tiger-coder | P0 | P1 | In Progress | Complete P1 before freeze | Semantic routing rules layer |
| 5 | **checkpoint-resume-v1** | main | lead-os | tiger-coder | P0 | P1 | In Progress | Complete P1 before freeze | Resume from checkpoint |
| 6 | **preflight-diagnostics-v1** | main | lead-os | lead-os | P0 | P1 | Planning | Complete P1 before freeze | Pre-task health checks |
| 7 | **evidence-dashboard-lite-v1** | main | lead-os | tiger-coder | P0 | P1 | Completed | Complete P1 before freeze | Public evidence layer |

---

## 三、Role Responsibilities

### Line Owner (CEO / main)

-owns the entire OS capability building line
- decides which OS projects enter project pool
- decides upgrade / freeze / prioritize
- hosts Weekly OS Review and makes final decisions
- ensures OS line has resources and doesn't get swallowed by business projects

### Project Owner (lead-os)

- drives each OS project forward
- tracks: current_stage, next_stage, blockers, operational_status
- prevents projects from "naturally disappearing" after P0
- organizes Weekly OS Review materials
- summarizes blockers and forms upgrade/freeze recommendations
- coordinates OS Radar / Skills Gap inputs into project pool

### Executor (tiger-coder / specific agent)

- executes specific implementation tasks
- reports progress to project_owner
- doesn't decide on project stage transitions

---

## 四、Project Status Definitions

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

## 五、routing-layer-v1 Direction

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

## 六、Weekly OS Review

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

## 七、Project Lifecycle Rules

### After P0 Completion

Every project must move to one of:

1. **Stable Running** - In production, working as expected
2. **Upgrade to P1** - Continue iteration
3. **Frozen** - Documented reason required

**Prohibited**: "Complete minimum version, then naturally disappear"

### Decision Authority

- Line Owner (CEO) makes final decision on upgrade / freeze
- Project Owner (lead-os) prepares recommendations and materials

---

## 八、Next Steps

1. ✅ Layered ownership structure confirmed
2. ✅ lead-os takes ownership of project tracking
3. ⏳ lead-os performs first round of project status maintenance
4. ⏳ Identify blockers and next_stage for each project

---

## Registry

| Field | Value |
|-------|-------|
| current_version | 1.1 |
| last_updated | 2026-04-01 |
| line_owner | main (CEO) |
| project_owner | lead-os |
| executor | tiger-coder |

---

*This document is the authoritative source for OS capability project tracking.*