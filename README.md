# AI Company OS

> ⚠️ Experimental · Local-first · Founder-built · Not a hosted SaaS
> **Current Public Release:** [`v0.46-alpha`](https://github.com/huangmin5598-blip/AI-Company-OS/releases/tag/v0.46-alpha) — Company Memory Public Foundation

**An AI-native company operating system — for solo founders and small teams.**

AI Company OS is not an agent framework. It is a company operating layer that manages AI agents through structured governance, execution pipelines, company memory, and evidence tracking.

It helps Founder + AI Agents run the full company loop: discover opportunities, initiate projects, build products, serve customers, collect feedback, and compound company assets.

---

## 🏗️ Architecture

AI Company OS is designed around **two complementary views**:

**View A — Company Operating Loop** (how the company creates value)

```
Opportunity Discovery → Productization → Build/Production →
Growth & Distribution → Customer Interaction/Sales →
Readiness/Execution → Learning/Iteration
```

**View B — OS Technical Support Layers** (how the system is organized)

```
Founder Control Plane → Governance Kernel → Company Memory/Context Layer →
Asset & Evidence Registry → Workflow & Skill Layer →
Runtime Adapter Layer → Product Line Workspace
```

> [📄 Public Architecture Lite](docs/architecture/ai-company-os-core-architecture-map.md) — Full A/B dual-view with 7+7 layer definitions.
> *The detailed layer-by-layer maturity roadmap and gap analysis are maintained privately.*

---

## 🧠 Key Capabilities

| Capability | What It Does | Status |
|:-----------|:-------------|:------:|
| **Governance CLI** | `create-task` enforces A/B perspective, maturity level, sensitivity, execution boundary, and value check — mandatory for all tasks | ✅ v0.46.2 |
| **Runtime Layer** | Standardized task lifecycle: create → prepare (Codex/Claude) → start → record-result → mark-reviewed | ✅ v0.45 |
| **Company Memory Core** | Structured company memory: 9-type taxonomy, lifecycle CLI (create/list/approve/reject), context pack templates | ✅ v0.46-alpha |
| **Public Architecture Lite** | Public A/B dual-view reference with 7+7 layer definitions | ✅ v0.46-alpha |
| **Opportunity Discovery** | Structured signal collection, enrichment, evaluation, and candidate pipeline (pain-first methodology) | ✅ v0.31–v0.34 |
| 🔒 **Opportunity Evaluation v2** | Proprietary multi-signal scoring, archetype system, confidence rules | 🔒 Private |

---

## 🔧 Core Mechanisms

Core OS mechanisms are file- and CLI-based, designed to be usable by different agents such as Hermes, OpenClaw, Claude Code, or custom runtimes.

**Memory lifecycle:**
```bash
python3 tools/memory/memory-runner.py create-candidate --type <type> --title <title> ...
python3 tools/memory/memory-runner.py list | show | approve | reject
```

**Runtime lifecycle management** — standardized task creation with mandatory governance fields, tracked via local CLI in the private operating workspace:

> Governance fields (`--view-a`, `--view-b`, `--maturity`, `--sensitivity`, `--execution-boundary`, `--value-check`) are **required** for task creation. The CLI rejects tasks that don't declare them.

---

## 🚀 Version Milestones

| Version | Layer | Status |
|:--------|:------|:------:|
| v0.1–v0.9 | Foundation: visibility, task loop, CEO agent, memory, runtime | ✅ |
| v0.10–v0.14 | Execution: Work Delegation, Skill Router, OpenClaw bridge | ✅ |
| v0.15–v0.22 | Governance: Skill Registry, Budget Guard, Decision Layer, Self-Improvement | ✅ |
| v0.23–v0.30 | Assets: Run Ledger, CEO CLI, Evidence, Workflow Composition | ✅ |
| **v0.30.1** | **Repository Boundary Enforcement** — public/private boundary hardened | ✅ |
| v0.31–v0.34 | Opportunity Discovery: signal source, enrichment, calibration | ✅ |
| v0.35–v0.44 | **Internal operating iterations** — methodology drafts, product-line experiments, infrastructure refinements | 🔒 Not individually published |
| **v0.45** | **Runtime Layer:** Codex/Claude adapters, task lifecycle, state machine | ✅ |
| **v0.46-alpha** | **Company Memory Core:** taxonomy, CLI, context pack templates, Architecture Lite | ✅ |
| **v0.46.2** | **Agent Independence Patch:** governance CLI enforcement | ✅ Internal milestone |
| 🔮 *Next* | *Product line validation: short novels / AI music* | 📋 |

> **Note:** Some releases (v0.10–v0.29) were rebuilt after repository boundary hardening at v0.30.1. Original bilingual release notes for those versions were lost and are now summarized as concise one-liners. See [Version History Note](https://github.com/huangmin5598-blip/AI-Company-OS/releases/tag/v0.46-alpha) for details.

---

## 📐 Repository Boundary

This public repo contains **reusable OS modules, tools, CLI scripts, and governance logic only**. The following are **excluded** from the public repository:

| Excluded | Location |
|:---------|:---------|
| Company Memory content (approved entries, candidates) | `private/memory/` |
| Runtime execution data and product-line assets | `private/` |
| Opportunity evaluation methodology (scoring, archetypes, confidence rules) | 🔒 Proprietary |
| Instance-specific research data (signals, watchlists) | `research/` (removed from git history) |
| Personal knowledge base | `AI-Knowledge-OS/` (separate local directory) |
| Environment config, tokens, credentials | `.env`, `config/company-instance.yaml` |

These directories and sensitive file patterns are excluded by `.gitignore` and checked during the release process.

---

## 📄 License

All Rights Reserved. See [NOTICE.md](NOTICE.md) and [COMMERCIAL.md](COMMERCIAL.md).

This is a source-visible public repository, not open source. No license is granted to use, modify, or distribute the code without explicit commercial agreement.
