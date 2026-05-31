# AI Company OS

**An AI Agent Native Company Operating System — for solo founders and small teams.**

AI Company OS is being built as an end-to-end operating system that helps Founder + AI Agents run the full company loop: discover opportunities, initiate projects, build products, serve customers, collect feedback, and compound company assets.

It is not an agent framework. It is a company operating layer that manages AI agents through structured governance, execution pipelines, and evidence tracking — with every action governed by policies, budgets, approvals, and an auditable ledger.

**Current implemented layers:**
- Governance & Policy Kernel (Capability Boundary, Safe Output, Budget Guard)
- Runtime & Execution (Multi-adapter, Work Order, Workflow Composition)
- Memory & Assets (Run Ledger, Asset Registry)
- Founder Control Plane (CEO Command Interface, Console Dashboard)
- Evidence & Productization (Evidence Dashboard, Operating Kit)
- 🔄 **Opportunity Discovery** (v0.31–v0.32 — in progress)

**Planned future layers:**
- Growth & Content Loop (planned)
- GTM / Sales Loop (planned)
- Customer Service Loop (planned)
- Company Self-Improvement Loop (v0.32 in progress)

**Current Version:** `v0.32` — Opportunity Discovery Loop (Sprint A)  
**Status:** Active, founder-built, local-first. Not a hosted SaaS.

> 📌 **Repository boundary:** This public repo contains reusable OS modules, templates, and governance logic only. Private instance data (company research, opportunity intelligence, personal knowledge base) is excluded — see [Git Boundary Policy](docs/known-issues/PRIVATE-RESEARCH-DATA-CLEANUP-v0.30.1.md).

```
Most people are building agents.
We are building the operating system around them.
```

---

## 🏗️ Architecture

The system is organized into 5 layers:

| Layer | What It Does |
|:------|:-------------|
| **Execution Spine** | CEO Brief → Review → Decision → Draft → Work Order → Approve → Execute → Callback → Result Sync |
| **Governance Kernel** | Budget Guard, Failure Policy, Skill Router, Preflight Checks, Capability Registry |
| **Memory & Asset Layer** | Run Ledger (event-sourced audit trail) + Asset Registry (idempotent pipeline tracking) |
| **Founder Control Plane** | Hermes Agent (Chief of Staff) + `ceo_cmd.py` (Structured CLI) + Control Center Dashboard (Web UI) |
| **Productization & Evidence** | Evidence Dashboard Lite, public-facing system summary, GitHub narrative |

### Founder Access

```
Hermes Agent ──────────── Open-ended chat, strategic discussion, task delegation
ceo_cmd.py ────────────── Structured OS interface for Hermes/automation
Control Center Dashboard ── Web-based Founder console: 5-tab navigation
```

---

## 📊 Evidence

> *"The system itself is the best documentation."*

| Evidence | Link |
|:---------|:-----|
| 📈 Evidence Summary (JSON) | [evidence-summary-v0.26.json](./docs/evidence/evidence-summary-v0.26.json) |
| 📋 Evidence Dashboard (Markdown) | [EVIDENCE-DASHBOARD-LITE-v0.26.md](./docs/evidence/EVIDENCE-DASHBOARD-LITE-v0.26.md) |
| ✅ Preflight Health | [11/11 checks passing](docs/known-issues/KNOWN-ISSUES-v0.26.md) |
| 🛠️ Capability Registry | [config/capability-registry.yaml](./config/capability-registry.yaml) |
| 📊 Run Ledger | 66 events · 9 event types |
| 📦 Asset Registry | Pipeline asset tracking with lineage |

### Screenshots

| Component | Preview |
|:----------|:--------|
| **Founder Console Dashboard** — system overview, health checks, WO stats, recent events | ![Dashboard](docs/evidence/screenshots/screenshot-dashboard.png) |
| **Preflight Health Checks** — 11/11 all passing | ![Preflight](docs/evidence/screenshots/screenshot-preflight.png) |
| **Skills Coverage Matrix** — agent skill mapping with coverage indicators | ![Skills](docs/evidence/screenshots/screenshot-skills.png) |
| **Workbench Tab** — task pool, execution, chat | ![Workbench](docs/evidence/screenshots/screenshot-workbench.png) |
| **Agent List** — runtime-grouped agent cards with status | ![Agents](docs/evidence/screenshots/screenshot-agents.png) |

---

## 🚀 Version Milestones

| Version | Layer | What It Proves | Status |
|:--------|:------|:---------------|:------:|
| v0.1–v0.9 | Foundation | Visibility, Task Loop, CEO Agent, Memory, Monitor, Runtime, Self-Improvement, Execution Bridge, Code Bridge | ✅ |
| **v0.10–v0.14** | **Execution & Callback** | Work Order lifecycle, OpenClaw bridge v2, Callback API contract, Idempotency, Force overwrite | ✅ |
| **v0.15–v0.16** | **Governance** | Skill Registry + Router, Budget Guard, Failure Policy, Health Checks | ✅ |
| **v0.17–v0.19** | **Documentation & QA** | Architecture docs, release notes, known issues, screenshot baseline | ✅ |
| **v0.20–v0.22** | **Studio Integration** | Codex CLI, Claude Code, OpenClaw worker, Executor/Approver separated | ✅ |
| **v0.23** | **Memory & Assets** | Run Ledger event sourcing, Asset Registry, idempotent pipeline tracking | ✅ |
| **v0.24** | **CEO Command** | `ceo_cmd.py` structured CLI, Capability Registry P0 | ✅ |
| **v0.25** | **Founder Control Plane** | 5-tab IA reorganization, Founder Console Dashboard, Preflight 11/11 | ✅ |
| **v0.26** | **Evidence & GitHub Refresh** | Evidence Summary Generator, Evidence Dashboard Lite, GitHub narrative | 🏗️ |

📋 **Full roadmap**: [AI-COMPANY-OS-ROADMAP.md](./docs/AI-COMPANY-OS-ROADMAP.md)

---

## 🧭 Repository Structure

```
├── backend/               FastAPI backend — models, routes, services
├── frontend/              Next.js Control Center — 5-tab dashboard
├── config/                Capability Registry, instance configuration
├── scripts/               ceo_cmd.py, os_registry.py, review_brief.py
├── reports/               CEO Briefs, Reviews, Decision Log, Drafts
│
├── docs/
│   ├── architecture/      System architecture documentation
│   ├── prd/               Product requirement documents
│   ├── releases/          Release notes per version
│   ├── evidence/          Public evidence dashboard data
│   ├── known-issues/      Pre-existing error records
│   └── AI-COMPANY-OS-ROADMAP.md
│
└── examples/              Real project cases
```

---

## 👤 Market & Audience

AI Company OS starts with solo founders — but the market has three layers.

| Layer | Audience | What They Need | Status |
|:------|:---------|:---------------|:------:|
| **1. Solo Founder (beachhead)** | Independent devs, AI entrepreneurs, creator-economy founders, cross-border sellers | Agent delegation without losing founder control; structured task governance; asset compounding | 🟢 Active |
| **2. AI-Native Small Team (2–20 people)** | Small teams running multiple agents across projects | Multi-agent governance, context management, cost tracking, run review, approval workflows | 🔴 Planned |
| **3. Enterprise AI Workforce Ops** | Organizations with sales agents, support agents, finance agents, compliance agents | Unified task flow, approvals, permissions, context, budgets, run state, audit trail, organizational memory | 🔮 Long-term |

**Solo founders are the beachhead, not the ceiling.** The same OS that works for one founder can scale to teams and, eventually, to enterprise AI workforce operations.

### Current Limitations

- **Local-first** — not a hosted SaaS platform
- **Single-founder** — optimized for solo operations
- **No multi-user permissions** — founder-trusted by design
- **Evidence is summarized** — not live public telemetry
- **Founder approval required** — for high-risk execution
- **Some workflows CLI-assisted** — not fully automated

---

## 🔍 How to Read This Repository

| Order | What | Why |
|:-----:|:-----|:----|
| 1 | `README.md` | System overview, evidence, architecture |
| 2 | `docs/evidence/EVIDENCE-DASHBOARD-LITE-v0.26.md` | See the system running |
| 3 | `docs/AI-COMPANY-OS-ROADMAP.md` | Evolution plan |
| 4 | `docs/architecture/` | System design docs |
| 5 | `config/capability-registry.yaml` | Agent capability declaration |
| 6 | `scripts/ceo_cmd.py` | Structured OS interface |

---

## ❓ Why This Exists

This is not a demo. It is a real, running system — built and tested by one founder using AI agents daily.

Four core judgments define why this matters:

**1. Companies become systems, not organizations**  
The AI-native company runs on data, agents, tools, and feedback loops — not on human memory and meetings. It executes, detects failure, analyzes root cause, fixes the path, and improves next time. This is a learnable system, not a traditional org chart.

**2. Competitive advantage is closed loops, not headcount**  
In the AI era, leverage comes from how many high-quality closed loops your company runs — not how many people you hire. Each loop senses, judges, executes, evaluates, and learns. More loops = more leverage.

**3. Company context is AI infrastructure**  
The bottleneck for enterprise AI is not model capability — it is that company context (customer understanding, business rules, historical decisions, founder judgment, existing assets, failure lessons, agent boundaries) is scattered across human brains, chat logs, and unstructured documents. An AI-native OS makes this context machine-readable.

**4. Build AI-readable from day one**  
All key business actions should be recorded. All key knowledge should be structured. All workflows should be agent-callable. All failures should feedback into the system. All experience should compound into assets. This is not adapting AI to old companies — it is designing companies so AI can run them.

---

## 📜 License

All Rights Reserved. © 2026 AI Company OS.

This project is **source-available for educational and reference purposes** — the code is publicly viewable on GitHub. Commercial use, redistribution, or derivative commercial products are not permitted without explicit permission.

> *A formal commercial license will be available in a future release (see ROADMAP: v0.27+ Operating Kit).*
