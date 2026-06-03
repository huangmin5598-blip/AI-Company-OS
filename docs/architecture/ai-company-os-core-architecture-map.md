# AI Company OS — Core Architecture Map

> **Public Architecture Lite**
> *Full maturity roadmap, gap analysis, and internal governance rules are maintained privately.*

---

## Overview

AI Company OS is a company operating system for AI-native businesses. It is designed around two complementary views that together describe how an AI company creates value and how the OS supports it.

---

## View A — Company Operating Loop

View A answers: *How does an AI-native company create value?*

```
Opportunity Discovery
       ↓
   Productization
       ↓
  Build / Production
       ↓
Growth & Distribution
       ↓
Customer Interaction / Sales
       ↓
   Readiness / Execution
       ↓
  Learning / Iteration
       ↻
```

| Stage | What it does |
|:------|:-------------|
| **Opportunity Discovery** | Scan market signals, identify viable entry points, prioritize |
| **Productization** | Turn opportunities into product concepts, PRDs, execution tasks |
| **Build / Production** | Produce the actual output — code, content, design, or deliverables |
| **Growth & Distribution** | Publish, distribute, and promote to target channels |
| **Customer Interaction / Sales** | Collect feedback, build trust, convert interest into revenue |
| **Readiness / Execution** | Confirm team, cost, compliance, and process readiness |
| **Learning / Iteration** | Reflect, extract patterns, and update the OS itself |

**View A is a company operating model, not a workflow architecture.** It defines *what stages a company goes through*, not *how each stage is executed*. The execution details live in View B's Workflow & Skill Layer.

---

## View B — OS Technical Support Layers

View B answers: *How does the AI Company OS system organize, govern, remember, and execute?*

```
      Founder Control Plane
             ↓
       Governance Kernel
             ↓
  Company Memory / Context Layer
             ↓
    Asset & Evidence Registry
             ↓
    Workflow & Skill Layer
             ↓
     Runtime Adapter Layer
             ↓
    Product Line Workspace
```

| Layer | What it does |
|:------|:-------------|
| **Founder Control Plane** | Command interface: goal input, decision making, global status review |
| **Governance Kernel** | Rules engine: permissions, compliance, release gates, data boundaries |
| **Company Memory / Context Layer** | Organizational memory: decisions, architecture knowledge, product line learnings |
| **Asset & Evidence Registry** | Asset catalog: outputs, evidence, results with traceable provenance |
| **Workflow & Skill Layer** | Reusable processes: skills, workflow templates, product line SOPs |
| **Runtime Adapter Layer** | External executor adapters: Codex CLI, Claude Code, Manual, and others |
| **Product Line Workspace** | Per-product-line runtime space: context, assets, workflows, history |

---

## View A ↔ View B Mapping

Each operating loop stage (View A) depends on multiple technical layers (View B):

| Operating Stage | Primary Technical Dependencies |
|:----------------|:-------------------------------|
| Opportunity Discovery | Company Memory → Workflow & Skill → Asset Registry |
| Productization | Company Memory → Governance Kernel → Runtime |
| Build / Production | Runtime Adapter → Asset Registry |
| Growth & Distribution | Workflow & Skill → Governance Kernel → Asset Registry |
| Customer Interaction | Company Memory → Asset Registry |
| Readiness / Execution | Governance Kernel → Runtime |
| Learning / Iteration | **Company Memory** → Workflow & Skill |

> **Key insight:** The Company Memory / Context Layer is the most cross-cutting dependency. It is the layer that makes each loop iteration smarter than the last.

---

## Architecture Maturity

AI Company OS evolves through three maturity levels:

| Level | Meaning |
|:------|:--------|
| **P0** | Make the stage or layer runnable — fully functional, manually repeatable |
| **P1** | Make the capability standardized and reusable across product lines |
| **P2** | Make it automated, scalable, and productizable |

*The layer-by-layer maturity roadmap and current gap analysis are maintained privately.*

---

## Public / Private Boundary

- This document describes the **architecture structure** — the naming, relationships, and design philosophy
- The detailed **internal maturity roadmap**, layer-by-layer **gap analysis**, and **governance rules** are maintained in private directories
- **Instance data** (product line assets, runtime logs, cost data, customer records) is excluded from the public repository
- **Company Memory** content (approved memory entries, candidates, governance decisions) is private by default

The private architecture and governance documentation enables the OS to evolve its strategic judgment without exposing competitive methodology in the public repository.

---

*Document version: 2.0 (Public Lite)*
*License: All Rights Reserved — see [NOTICE.md](../NOTICE.md) and [COMMERCIAL.md](../COMMERCIAL.md)*
