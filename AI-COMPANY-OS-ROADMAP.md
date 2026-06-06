# AI Company OS Roadmap — v0.46.5

> Last updated: 2026-06-06

## Core Principle

AI Company OS is a **governance and operations layer ABOVE agent frameworks**.
It is NOT another agent framework.

```
Previous: Founder → Hermes CEO → OpenClaw Executor
Current:  Founder → CEO Agent Interface → AI Company OS Core → Runtime Adapter Interface → [Codex | Claude | OpenClaw | local_script | future]
```

**Key principle:** Hermes / OpenClaw / Codex / Claude / Paperclip are **REPLACEABLE IMPLEMENTATIONS**, not OS Core.

---

## Phase Status

| Phase | Description | Status |
|-------|-------------|--------|
| B0R | OS Work Queue + local_script bootstrap | ✅ PASS |
| B1 | local_script adapter verification | ✅ PASS |
| B2-0A | Workspace split detection | ✅ PASS |
| B2-0B | Canonical workspace reconciliation | ✅ PASS |
| B2-0C | Coding runtime readiness check | ✅ PASS |
| B2-0D | Git boundary + pluggable interface baseline | ✅ PASS |
| B2-1 | Codex Adapter Trial | ⏸ Pending Preview approval |
| B2-2 | Claude Code Adapter Trial | ⏸ Pending B2-1 |
| B2-OpenClaw-0 | OpenClaw Adapter Readiness | ⏸ Pending B2-1 |
| B2-Hermes-0 | Hermes CEO Control Plane Enforcement | ⏸ Pending B2-2 |
| B2-Skill-0 | OS Skill Protocol Preview | ⏸ Pending B2-1 |
| B3 | Multi-Work Parallel Trial | ⏸ Pending B2-Hermes-0 |
| v0.47 | Async Work Queue Lite | ⏸ Future |

---

## P0 / P1 / P2 Definitions

### P0: OS Control Plane Foundation — COMPLETE

**Goal:** Establish minimum control plane WITHOUT binding to any single agent framework.

**P0 Done:**
- Work Queue filesystem state machine
- local_script_adapter minimum execution
- waiting_review / Audit Packet
- canonical repo path rule (via env var + local-paths.yaml)
- Git baseline
- CEO Agent Interface
- Runtime Adapter Interface
- Runtime Adapter Registry
- ADR-001: OS owns Work Queue
- ADR-002: Canonical Repo Path Rule (public-safe)
- ADR-003: Pluggable Agent Interface

**P0 NOT doing:**
- Persistent daemon
- Multi-agent parallel
- Product line automation
- Auto-dispatch to external runtimes
- Public release push
- Binding Hermes / OpenClaw as sole architecture

---

### P1: Runtime Adapter Verification — IN PROGRESS

**Goal:** Different runtimes ACTUALLY dispatch through OS Work Queue, execute, write back, receive Review.

**P1 Next Steps:**
- B2-1: Codex Adapter Trial
- B2-2: Claude Code Adapter Trial
- B2-OpenClaw-0: OpenClaw Adapter Readiness
- B2-Hermes-0: Hermes CEO Control Plane Enforcement
- B2-Skill-0: OS Skill Protocol Preview
- B3: Multi-Work Parallel Trial

**P1 Acceptance Criteria (ALL must pass):**
- Canonical repo check passed
- Work Queue / Handoff Packet used
- allowed_files / forbidden_paths defined
- Audit Packet output
- Hermes only Reviews, does not execute

**Runtime path rules:**
- External runtimes (Codex / Claude / OpenClaw): Must NOT read/write `private/`, `memory-system/`, `.git/` unless explicitly mediated through OS handoff packet
- OS internal workers (local_script / OS worker): May operate `private/work-queue/` under Work Queue state machine rules

**After passing:** `available_not_tested → smoke_test_passed` (NOT fully verified)

**P1 NOT doing:**
- Auto long-running daemon
- Multi-product-line resident
- CEO Agent replacement
- Large-scale task parallel
- Public push unless separate release approval

---

### P2: Agent Army Operating System — FUTURE

**Goal:** Founder talks to ONE CEO Agent; multiple runtimes work in parallel in background.

**P2 Capabilities:**
- Async Work Queue Lite
- Persistent worker / daemon
- Cron Poller / Event Trigger
- Multi-task parallel
- Runtime Adapter auto-selection
- OS Skill Protocol + Skill Router
- Context Pack Builder
- Quality Gate CLI
- Memory / Asset / Evidence auto-deposition
- Multi-product-line Lead Agent
- Multiple adapters running in parallel
- One active CEO rule still applies

**P2 NOT doing:**
- Cramming tools into OS Core
- Binding to Hermes / OpenClaw / Codex / Claude
- Turning OS into another agent framework

---

## OS Skill Protocol Roadmap

### P0: 沿用现有 os-skills/

- `os-skills/skill-registry.yaml` is OS Skill Source of Truth
- Hermes-native skills accessible via existing skill tools
- No change to current skill mechanism

### P1: 建立 OS Skill Protocol

**Goal:** Make skill capability accessible to ANY agent framework, not just Hermes.

**Target:**
- `tools/os-skill list` — list all available skills
- `tools/os-skill lookup --task <task>` — find skill for task
- `tools/os-skill show <skill_id>` — show skill details
- Standard skill manifest fields:
  - `skill_id`, `name`, `description`
  - `agent_compatibility`: `hermes | openclaw | codex | claude | any`
  - `skill_source`: `os-skills/skill-registry.yaml`
  - `trigger_conditions`
  - `execution_interface`

**Purpose:** Support customers who do not use Hermes — any adapter that implements skill protocol can access OS skill pool.

### P2: Skill Router + Context Pack Builder

- Skill Router: auto-select appropriate runtime for skill execution
- Context Pack Builder: bundle skill + context for specific adapter
- Adapter-specific skill execution layers

---

## Registered Runtime Adapters (v0.46.5)

| Adapter | Type | Status |
|---------|------|--------|
| local_script_adapter | local_worker | verified_B1 |
| codex_adapter | coding_runtime | available_not_tested |
| claude_code_adapter | coding_runtime | available_not_tested |
| openclaw_adapter | agent_host | declared_not_verified |
| paperclip_adapter | future | future_compatible |
| crewai_adapter | future | future_compatible |
| dify_adapter | future | future_compatible |
| langgraph_adapter | future | future_compatible |
| autogen_adapter | future | future_compatible |

---

## Governance Rules Summary

| Rule | Description |
|------|-------------|
| G1 | P0/P1/P2 Continuity: each phase records what is done, next, and explicitly not done |
| G2 | Canonical Repo Path: resolved via `AI_COMPANY_OS_CANONICAL_REPO` env var + `private/runtime/local-paths.yaml` |
| G3 | One Active CEO: only one CEO Agent active at a time, replacement requires conformance test |
| G4 | Runtime Adapter Registration: can register as candidate, must pass conformance test before real work |
| G5 | No Direct Execution by CEO: CEO creates/dispatches/reviews, does not execute directly |
| G6 | Framework-Agnostic OS: OS does not bind to any specific runtime or framework |
| G7 | OS Skill Protocol: skills are not Hermes-locked, any compliant adapter can access |

---

## v0.46.5 Roadmap Update — 2026-06-06

This section appended via Phase 3 apply on 2026-06-06.

---

## v0.47–v1.0 Core Substrate PRD — APPROVED

**PRD Document:** `docs/prd/AI-COMPANY-OS-v0.47-v1.0-CORE-SUBSTRATE-PRD-v2.md`
**Version:** v2.0
**Status:** Key PRD — Primary development input for Codex / Claude Code

### Core Substrate Overview

AI Company OS is a **governance and operating layer ABOVE agent frameworks**.
It is NOT another agent framework.

**Ultimate Goal:** Founder operates through a replaceable CEO Agent. OS manages Work Queue, Runtime Adapters, Model Policy, Workflow Composer, Quality Gates, Audit Packets, Cost Ledger, Capability & Skill Supply Chain, Company Context, Evidence/Memory, Learning Loop, and Founder Control Center UI.

### Product Boundary

**OS Core includes:**
- Work Queue Engine, State Machine
- Runtime Adapter Interface, Registry, Invocation Authenticity Gate
- CEO Agent Interface, Provider Registry
- Model Policy & Model Profile Registry
- Intent Intake & Conversation Sync
- Requirement Clarification & PRD Pipeline
- Opportunity Discovery & Opportunity-to-PRD Pipeline
- Product Line Workflow Composer
- Company Context Graph
- Capability & Skill Supply Chain
- Learning Loop Engine
- Founder Control Center UI, AI Army Live View, Replay Engine

**OS Core does NOT include:**
- ComfyUI, TTS, video generation tools
- Codex/Claude/OpenClaw internal planning capabilities
- Any single agent framework's internal capabilities
- Specific product line business content
- Private API tokens, sensitive data
- Any un-reviewed external Skill

### 14 Implementation Epics (PRD Section 30)

| Epic | Name | Priority |
|------|------|----------|
| 1 | Project Structure & AGENTS.md | P0 |
| 2 | Work Queue Core | P0 |
| 3 | Runtime Adapter Base + Local Script Adapter | P0 |
| 4 | Codex Adapter Wrapper | P0 |
| 5 | Gates (Canonical Repo, Authenticity, Forbidden Path, etc.) | P0 |
| 6 | Audit / Cost / Evidence | P0 |
| 7 | CEO Provider + Intake | P0 |
| 8 | Model Policy + Workflow Composer | P0 |
| 9 | Capability & Skill Supply Chain | P0 |
| 10 | Company Context + Learning Loop | P0 |
| 11 | Opportunity + PRD Pipeline | P0 |
| 12 | Founder Control Center UI | P0 |
| 13 | AI Army Live + Replay | P1 |
| 14 | Tests & Release Readiness | P0 |

### Version Roadmap

| Version | Target | Status |
|---------|--------|--------|
| v0.47 | OS Control Plane MVP | ⏸ Superseded by PRD v2 |
| v0.48 | Capability & Skill Supply Chain | ⏸ Future |
| v0.49 | Async Work Queue Lite | ⏸ Future |
| v0.50 | Multi-Runtime / Multi-Workflow Trial | ⏸ Future |
| v0.51 | PRD-to-Execution Pipeline | ⏸ Future |
| v0.52 | Founder Control Center & AI Army UI | ⏸ Future |
| v1.0 | Complete Core Substrate | ⏸ Future |

### Native Agent Mode vs OS-Governed Mode

- **Native Agent Mode:** Agent actions in native environment (chat, draft, brainstorm). NOT official OS actions.
- **OS-Governed Mode:** Requires Goal/Task Record + Work Queue + Handoff Packet + Runtime Adapter + Audit Packet + Review. ONLY this counts as official OS action.

### Key Rules (from PRD)

| Rule | Description |
|------|-------------|
| CEO Agent replaceable | Via CEO Agent Provider Registry, one active CEO, conformance test required |
| Model Policy | Founder-configurable, per Agent/Runtime/ProductLine/TaskType |
| Workflow Composer | Founder-configurable product line workflows |
| No CEO direct execution | CEO creates/dispatches/reviews, does not execute |
| Runtime Invocation Authenticity Gate | Blocks fake adapter calls |
| Forbidden paths | External runtimes blocked from private/, .git/, memory-system/, os-skills/ |
| Evidence/Memory/Asset Pipeline | Every work item produces evidence candidates |
| Learning Loop | Failures → root cause → tool/rule/skill/context/model/workflow update |

### Hard Restrictions for All Runtimes

- No git commit / push without Founder approval
- No modification of private/, .git/, memory-system/
- No local absolute paths in public docs
- No upgrade of runtime registry status without Founder approval
- No bypass of Work Queue
- No fake adapter invocation
- OS Core never binds to Hermes / OpenClaw / Codex / Claude