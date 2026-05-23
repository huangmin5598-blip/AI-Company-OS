# Productization Architecture — AI Company OS

> **Separation of OS Core from Company Instance, enabling productization.**
> v0.4.1 · 2026-05-23

---

## 1. Why Productization

AI Company OS started as a solo founder's personal operating system. The codebase, config, docs, and runtime were all mixed together — what worked for "one company running on one machine" couldn't be cleanly extended to new users without risking the core logic.

**The goal of v0.4.1 is to draw clean boundaries** between what is:

- **OS Core** — invariant, reusable, product
- **Company Instance** — configurable, per-user, deploy-time
- **Operating Kit** — methodology, optional, additive
- **Evidence Layer** — public, verifiable, separate

---

## 2. The Four Layers

```
┌─────────────────────────────────────────────────┐
│                 Evidence Layer                    │
│  Public proof: releases, build logs, dashboards   │
│  Location: /evidence, /docs/releases, /docs/build-logs
├─────────────────────────────────────────────────┤
│                 Operating Kit                     │
│  Methodology: constitution, playbooks, templates  │
│  Location: /docs/constitution, /examples          │
├─────────────────────────────────────────────────┤
│                Company Instance                    │
│  Per-company config: runtimes, channels, policies  │
│  Location: /config/company-instance.yaml           │
├─────────────────────────────────────────────────┤
│                   OS Core                          │
│  Invariant product: backend, frontend, protocols   │
│  Location: /backend, /frontend, /docs/architecture │
└─────────────────────────────────────────────────┘
```

### 2.1 OS Core (Invariant)

The OS Core is what every AI Company OS installation shares. It should never contain company-specific data, runtime endpoints, or business logic that differs per user.

| Component | What It Contains | Invariant? |
|:----------|:-----------------|:-----------|
| `backend/` | FastAPI app, models, routers, adapters, database schema | ✅ Yes |
| `frontend/` | Next.js Control Center UI | ✅ Yes |
| `backend/app/runtime/protocol.py` | RuntimeAdapter abstract protocol | ✅ Yes |
| `docs/architecture/` | System architecture documentation | ✅ Yes |
| `.env.example` | Template for environment variables | ✅ Yes |

**Invariant rules:**
- No hardcoded company names, founder names, or business line names in backend/frontend code
- No hardcoded runtime endpoints (localhost URLs, specific ports)
- No company-specific approval policies in code
- All per-company parameters must come from `config/company-instance.yaml`

### 2.2 Company Instance (Configurable)

The Company Instance is the configuration that turns an OS Core into "Your AI Company." It defines:

- Which runtimes are available and how to reach them
- Which business lines the company operates
- Where to send notifications
- Approval policy (auto-approve thresholds, required approvals)

**Location:** `config/company-instance.yaml`

**Example structure:**

```yaml
company:
  name: "My AI Company"
  founder_name: "Founder"

runtimes:
  - name: hermes-local
    type: hermes
    endpoint: http://localhost:8080

business_lines:
  - name: short-drama-production
    leads: ["ceo-agent"]

notification_channels:
  - type: feishu
    webhook_url: "..."

approval_policy:
  default_requires_approval: true
```

**Instance rules:**
- Never committed to the product repository (add to `.gitignore`)
- The `config/company-instance.example.yaml` serves as the template
- Migration: `config/` directory is for examples; actual instances live outside the repo

### 2.3 Operating Kit (Methodology)

The Operating Kit is the methodology layer — the "how to run an AI-native company" content that sits alongside the software.

| Component | What It Contains | Product Status |
|:----------|:-----------------|:---------------|
| `docs/constitution/` | Design principles, constitutional documents | ✅ v0.4.1 |
| `examples/novel-v1/` | Real project case study | ✅ v0.4.1 |
| `examples/skills/` | Hermes skill examples | ✅ v0.4.1 |
| Playbooks | Step-by-step operating procedures | 🔮 Future |
| Templates | Project templates, agent config templates | 🔮 Future |

**Operating Kit rules:**
- Never makes assumptions about which specific runtimes the user has
- Examples should be generic enough to apply to any AI-native company
- Should be readable as standalone methodology, not requiring the codebase

### 2.4 Evidence Layer (Public Proof)

The Evidence Layer is the public-facing proof that the system is running, projects are progressing, and capabilities are growing.

| Component | Status |
|:----------|:-------|
| `docs/releases/` | ✅ v0.1.1 through v0.4 release notes |
| `docs/build-logs/` | ✅ Build process records |
| `evidence/` | ✅ Public evidence dashboard |
| `assets/screenshots/` | ✅ UI screenshots |
| `REPO-CLEANUP-PLAN.md` | ✅ Cleanup evidence |

**Evidence Layer rules:**
- Always public and verifiable
- Versioned alongside the codebase
- Each release should update at least: release note + build log + evidence dashboard

---

## 3. Productization Marking Convention

Every file and module in the codebase is classified into one of three categories:

| Category | Tag | Description | Version Boundary |
|:---------|:----|:------------|:-----------------|
| **Product** | `PRODUCT` | Core OS code that ships with every installation | Must be generic |
| **Platform** | `PLATFORM` | Infrastructure, CI/CD, deployment tooling | Internal tooling |
| **Internal** | `INTERNAL` | Temporary code, experiments, one-off scripts | Should graduate or be removed |

### Marking syntax

In Python files:
```python
# @PRODUCT backend/app/runtime/protocol.py
# This file is part of the OS Core — invariant across all installations.
```

In YAML/JSON config:
```yaml
# @PRODUCT config/company-instance.example.yaml
```

In Markdown docs:
```markdown
<!-- @PRODUCT docs/architecture/PRODUCTIZATION-ARCHITECTURE.md -->
```

---

## 4. Migration Path

### Now (v0.4.1)

```
/backend          → PRODUCT (already mostly clean)
/frontend         → PRODUCT (already mostly clean)
/config/          → PLATFORM examples (new)
/docs/architecture → PRODUCT (new)
/docs/constitution → OPERATING KIT (moved from root)
/examples/        → OPERATING KIT (new)
/evidence/        → EVIDENCE (existing)
```

### Near term (v0.5+)

```
/backend/app/runtime/       → PRODUCT (grow the protocol)
/docs/architecture/         → PRODUCT (add Monitor Framework)
/docs/operating-kit/         → OPERATING KIT (new directory for playbooks)
```

### Future (v0.6+)

```
/backend/app/runtime/adapters/  → PRODUCT (multi-runtime)
/docs/operating-kit/playbooks/  → OPERATING KIT
/examples/company-instances/    → OPERATING KIT (reference instances)
```

---

## 5. Design Decisions

### Why not microservices?

The four layers are **logical boundaries**, not deployment boundaries. A single-process FastAPI app serves all layers. The separation is about code organization and configuration, not network topology.

### Why Company Instance as YAML, not a database table?

Because it's a deploy-time concern, not a runtime concern. The instance config tells the OS who it's running for and how to reach its team. Runtime data (tasks, memory, alerts) goes into the database.

### Why not multi-tenant?

Because the first user is a solo founder. Multi-tenancy is a v0.9+ concern. The current architecture ensures that when multi-tenancy arrives, the boundaries are already drawn — the OS Core stays the same, and each tenant gets a separate Company Instance config.

---

## 6. Files Changed in This Architecture

| File | Layer | Action |
|:-----|:------|:-------|
| `docs/architecture/PRODUCTIZATION-ARCHITECTURE.md` | PRODUCT | **New** (this file) |
| `backend/app/runtime/protocol.py` | PRODUCT | **New** |
| `config/company-instance.example.yaml` | PLATFORM | **New** (already created) |
| `README.md` | PRODUCT | **Updated** (v0.4.1 cleanup) |
| `docs/AI-COMPANY-OS-ROADMAP.md` | PRODUCT | **Updated** (v0.4.1 cleanup) |
| `docs/architecture/v0.5-MONITOR-FRAMEWORK-ARCHITECTURE.md` | PRODUCT | **New** |

---

> **This architecture is the foundation for all v0.4.1 deliverables.**
> Every subsequent file references the four-layer model defined here.
