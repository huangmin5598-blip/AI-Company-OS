# AI Company OS

**An operating system for AI-native companies — starting from solo founders.**

AI Company OS helps founders and small AI-native teams manage AI agents, task loops, approvals, company memory, runtime visibility, and self-improvement workflows.

It started as a real solo-founder operating system. The long-term goal is broader: a company-level operating layer for teams that use AI agents as part of their daily execution system.

Most people are building agents. We are building the operating system around them.

---

## Current Status

AI Company Control Center has reached **v0.9.2 — External Runtime Connector MVP** 🏁.

The system now includes everything from v0.1–v0.9, plus:

- **Unified Runtime Access Layer** — Hermes Agent, OpenClaw Gateway, Codex CLI, Claude Code (experimental), and 3 cloud disabled slots under a single adapter protocol
- **External HTTP Agent Adapter Template** — generic remote agent adapter with endpoint whitelist, env-only auth, and execute() hard-disabled
- **Claude Code Experimental Integration** — real health_check + capability discovery + generate_plan (25s), generate_patch/apply blocked as experimental
- **Runtime Registry** — 8 runtimes registered: 4 enabled (hermes, openclaw, codex, claude-code) + 4 disabled (including 3 cloud config-only slots)
- **CCR runtime_id Parameter** — all Code Change Request endpoints accept runtime_id; nonexistent/disabled runtimes return 422
- **Security Boundaries** — execute() hard-disabled, auth via env vars only, endpoint_url whitelist, disabled runtimes never touched

---

## Version Milestones

| Version | Layer | What It Proves | Status |
|:--------|:------|:---------------|:------:|
| v0.1.1 | Visibility + Control | The system reads real runtime data and exposes it in a Founder dashboard. | ✅ |
| v0.2 | Company Loop MVP | Alerts and commands become tasks with context, approval, review, and learning candidates. | ✅ |
| v0.3 | CEO Agent Lite | Founder intent enters the OS through natural language and becomes structured tasks or approvals. | ✅ |
| v0.4 | Company Memory MVP | Approved learning candidates become searchable organizational memory. | ✅ |
| v0.4.1 | Productization & Runtime Readiness | OS Core separates from company-specific configuration. | ✅ |
| v0.5 | Monitor Framework Lite | The system observes itself and proposes improvements. | ✅ |
| v0.6 | **Runtime Layer MVP** | Runtime registration, health checking & frontend grouping. | ✅ |
| v0.7 | **Controlled Self-Improvement** | System improves itself under constraints. | ✅ |
| v0.8 | **Controlled Execution Bridge** | Improvement proposals flow into one-shot, auditable, verified execution. | ✅ |
| v0.9 | **Code-Capable Runtime Bridge** | Codex/Claude Code integrated — safe code change flow for non-technical founders. | 🏁 |
| v0.9.2 | **External Runtime Connector MVP** | Unified Runtime access layer — local agents, experimental agents, cloud disabled slots with security boundaries. | 🏁 |

---

## Runtime Architecture

AI Company OS v0.9.2 introduces a **unified Runtime access layer** that decouples agent execution from any single provider.

### Runtime Types

| Type | Runtimes | Status |
|:-----|:---------|:------:|
| 🟢 **Local** — Real agent on this machine | `hermes`, `openclaw`, `codex` | Enabled |
| 🟡 **Experimental** — Functional but limited | `claude-code` | generate_plan only (no patch/apply) |
| ⚪ **Cloud (Disabled)** — Config slots, zero remote touch | `cloud-openclaw`, `cloud-hermes`, `minimax-agent` | Disabled |

### Key Capabilities

| Runtime | generate_plan | generate_patch | apply | rollback |
|:--------|:------------:|:--------------:|:-----:|:--------:|
| codex | ✅ | ✅ | ✅ | ✅ |
| hermes | ✅ | — | — | — |
| openclaw | ✅ | — | — | — |
| claude-code | ✅ (25s) | ❌ (exp.) | ❌ | ❌ |
| cloud-* (disabled) | ❌ 422 | ❌ | ❌ | ❌ |

### Security Boundaries

- **execute() hard-disabled** — no remote execution in v0.9.2
- **Auth via env vars only** — tokens never stored in config or git
- **endpoint_url whitelist** — only `http://localhost` / `http://127.0.0.1` / `https://`
- **Disabled runtimes never touched** — health checks skipped
- **CCR runtime_id validates** — nonexistent or disabled returns 422

---

## Repository Structure

```
├── backend/            FastAPI backend — runtime, models, routes, adapters
├── frontend/           Next.js Control Center — dashboard, loop, CEO workbench, memory
├── config/             Company instance configuration examples
│
├── docs/
│   ├── architecture/   System architecture and protocol documentation
│   ├── prd/            Product requirement documents (v0.2–v0.4)
│   ├── releases/       Release notes for each version
│   ├── build-logs/     Build process records
│   ├── constitution/   Design principles and constitutional documents
│   └── AI-COMPANY-OS-ROADMAP.md
│
├── examples/
│   ├── novel-v1/       Real project case: multi-agent novel production
│   └── skills/         Hermes skill examples for CEO Agent integration
│
├── evidence/           Public evidence dashboard — system running status
└── assets/             Screenshots and media
```

---

## Who This Is For

AI Company OS is currently built and tested by one founder using AI agents to run real projects.

The first user is a solo founder. The broader user is any AI-native team that needs to manage:

- multiple AI agents
- task and approval loops
- runtime visibility
- company memory
- cost and safety boundaries
- self-improvement workflows

**Solo founder is the starting point, not the ceiling.**

---

## Quick Start

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001

# Frontend
cd frontend
npm install
npm run dev -- -p 3001
```

> **⚠️ Early system**: This is still an early founder-built system. Local setup assumes Python/Node environment and existing runtime data sources. A full "clone and run" experience with demo seed data and installation scripts is not yet available.

See [docs/architecture/](./docs/architecture/) for system design details.

---

## How to read this repository

If you are new here, start with:

- `README.md` — this file, product overview
- `docs/AI-COMPANY-OS-ROADMAP.md` — version evolution plan
- `docs/architecture/` — system architecture documentation
- `docs/prd/` — product requirement documents per version
- `evidence/` — public evidence dashboard showing the system is running
- `examples/novel-v1/` — a real project case demonstrating multi-agent production

---

## Why this exists

This repository is not a demo. It is a real, running system that a founder uses daily to run AI agents as part of a company operating layer.

We believe that:

- AI agents will become independent executors, not just chatbots
- A company with multiple AI agents needs an operating system, not just a framework
- The OS must accumulate organizational memory, enforce safety boundaries, and track cost
- Solo founders get the most leverage from AI-native operations, and what works for one founder can scale to a team

Everything here is public because:

- The system itself is the best documentation
- Evidence speaks louder than claims
- Others building in this space should not start from zero

---

## License

MIT
