# AI Company OS — Evidence Dashboard Lite

> Generated: 2026-05-30T16:41:29.937412+00:00  |  Evidence Version: v0.26

---

## 1. What AI Company OS Is

A governance-first operating system for AI-native companies — starting from solo founders

- **Current Version:** `v0.22.1`
- **Local-First:** True
- **Single-Founder Oriented:** True
- **Not a Hosted SaaS:** True

---

## 2. Architecture

5-layer: Execution Spine (WO pipeline), Governance Kernel (budget/failure/skill), Memory & Asset Layer (Run Ledger + Asset Registry), Founder Control Plane (Console + CEO Command), Productization & Evidence

```
Execution Spine:  CEO Brief → Review → Decision → Draft
                  → Work Order → Approve → Execute → Callback
                  → Result Sync → Run Ledger / Asset Registry

Founder Access:    Hermes Agent (Chief of Staff)
                  ceo_cmd.py (Structured CLI)
                  Control Center / Dashboard (Web UI)
```

---

## 3. Version Milestones

| Metric | Value |
|--------|-------|
| Versions Released | 40 |
| Latest Version | `v0.22.1` |
| First Version | `v0.1.1-p0` |
| Total Git Tags | 40 |

Latest tags:
v0.22.1, v0.22, v0.21, v0.20, v0.19.1

---

## 4. Decision-to-Execution Flow

The core pipeline:

1. **CEO Brief** — System-generated status summary for Founder
2. **Review** — Founder reviews, decides next action
3. **Decision** — Recorded in Decision Log
4. **Draft** — Work Order Draft generated from decision
5. **Work Order** — Dispatched to appropriate runtime
6. **Approve** — Founder or automated approval
7. **Execute** — Runtime executes via OpenClaw/Codex/Hermes
8. **Callback** — Result returned via callback API
9. **Result Sync** — Output backfilled to decision context

All steps recorded in Run Ledger and Asset Registry.

---

## 5. Governance Mechanisms

The system enforces the following governance:

1. **CEO Brief → Review → Decision → Draft → Work Order → Approve → Execute → Callback → Result Sync**

2. **Budget Guard**
   - per-agent/per-task budget enforcement

3. **Failure Policy**
   - automated retry, escalation, fallback

4. **Skill Router**
   - capability-based task routing across runtimes

5. **Capability Registry**
   - declarative agent capability declaration

6. **Preflight Checks**
   - 11 health diagnostics

7. **Founder Console**
   - read-only Founder control plane

8. **Asset Registry**
   - idempotent pipeline asset tracking

9. **Run Ledger**
   - event-sourced execution audit trail

10. **CEO Command Interface**
   - structured OS CLI for Hermes/automation

---

## 6. Run Ledger Evidence

| Metric | Value |
|--------|-------|
| Total Events | 78 |
| Event Types | 9 |

Event type distribution:

- `approved_for_dispatch`: 24 ████████████████████████
- `ceo_assets`: 1 █
- `ceo_draft_from_asset`: 1 █
- `ceo_draft_from_decision`: 1 █
- `ceo_lineage`: 1 █
- `ceo_status`: 1 █
- `result_synced`: 1 █
- `work_order_executed`: 24 ████████████████████████
- `work_order_routed`: 24 ████████████████████████

![Skills Coverage Matrix](../screenshots/screenshot-skills.png)
*Skills Coverage Matrix — agent skill mapping with coverage indicators*

---

## 7. Asset Registry Evidence

| Metric | Value |
|--------|-------|
| Total Assets | 1 |
| Asset Types | 1 |

Asset type distribution:

- `execution_result`: 1 █

---

## 8. Founder Control Center Evidence

The Control Center provides a read-only Founder console with:

- **5-Tab Navigation:** Dashboard, Workbench, Company, Products, Governance
- **Founder Console Cards:** System health, WO status, recent events, assets
- **Preflight Health Checks:** 11/11 passing

![Founder Console Dashboard](../screenshots/screenshot-dashboard.png)
*Founder Console Dashboard — system overview, health checks, WO stats*

![Preflight Health Checks](../screenshots/screenshot-preflight.png)
*Preflight Health Checks — 11/11 all passing*
✅ All checks pass

Checks performed:
- ✅ `Database`
- ✅ `Run Ledger`
- ✅ `Asset Registry`
- ✅ `Reports Paths`
- ✅ `Capability Registry`
- ✅ `Decision Log`
- ✅ `Budget Policy`
- ✅ `CEO Brief`
- ✅ `OpenClaw CLI`
- ✅ `Codex CLI`
- ✅ `OpenClaw Queue`

---

## 9. Runtime / Agent Evidence

| Metric | Value |
|--------|-------|
| Total Agents | 9 |
| Runtime `hermes` Agents | 1 |
| Runtime `system` Agents | 1 |
| Runtime `openclaw` Agents | 6 |
| Runtime `codex` Agents | 1 |

Agent roles (layer summary):
- Founder-facing Chief of Staff
- System-facing CEO Command Interface
- Research & Information Specialist
- Financial Analysis Specialist
- Amazon E-commerce Operations Specialist
- Multi-format Content Production Specialist
- Code Development Specialist
- Model Gateway & Execution Runtime
- Background Task Executor

![Workbench Tab](../screenshots/screenshot-workbench.png)
*Workbench Tab — task pool, execution bridge, chat*

![Agent List](../screenshots/screenshot-agents.png)
*Agent List — runtime-grouped agent cards with status indicators*

---

## 10. Current Limitations

- Local-first system — not a hosted SaaS platform
- Single-founder oriented — optimized for solo operator workflows
- No multi-user permission system — all operations are founder-trusted
- Evidence is summarized — not live public telemetry
- Founder approval still required for high-risk execution
- Some workflows remain CLI-assisted
- Screenshots in evidence doc are static snapshots

---

## 11. Next Roadmap

- **v0.26** — Evidence Dashboard Lite + GitHub Refresh (current)
- **v0.27** — Asset & Lineage Enhancement + Test Fixes
- **v0.28** — Workflow Composition (WO `depends_on`, chains)
- **v0.29+** — Further productization

Full roadmap: [ROADWAY.md](/ROADMAP.md)

---

*Evidence generated at 2026-05-30T16:41:29.937412+00:00*
