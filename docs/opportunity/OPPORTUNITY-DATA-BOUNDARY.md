# Opportunity Module — Data Boundary

> **Principle:** Knowledge is not the product; the *management mechanism* is the product.

This document defines what goes where when working with opportunities in AI Company OS.

---

## Three-Layer Separation

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 3: OS Opportunity Module  │  PUBLIC (GitHub)         │
│  scripts/opportunity.py          │  Reusable framework      │
│  scripts/ceo_cmd.py opportunity  │  Template + CLI + Events │
│  config/opportunity.example.yaml │                          │
│  docs/opportunity/               │                          │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: Company Instance Data  │  PRIVATE (local, .git)   │
│  research/opportunity-pool/      │  Real opportunity cards   │
│  research/watchlist.yaml         │  Real watchlist config   │
│  research/source-notes/          │  Real market signals     │
│  config/opportunity.yaml         │  Real instance config    │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: Personal Knowledge      │  PRIVATE (not in repo)   │
│  ~/AI-Knowledge-OS/              │  Your personal KB         │
└─────────────────────────────────────────────────────────────┘
```

### Layer Definitions

| Layer | What | Where | Git? | Sold? |
|:------|:-----|:------|:-----|:------|
| **1. Personal Knowledge Base** | Raw research, reading notes, frameworks | `~/AI-Knowledge-OS/` | ❌ Never | ❌ Not |
| **2. Company Instance Data** | Your specific opportunities, watchlist, signals | `research/`, `config/opportunity.yaml` | ❌ Never | ❌ Not |
| **3. OS Opportunity Module** | Framework code, schemas, CLI, templates | `scripts/`, `config/*.example.yaml` | ✅ Yes | ✅ Yes |

---

## Data Flow

```
AI-Knowledge-OS (Layer 1)
  ↓  You selectively extract insight
opportunity_signal (a structured object created by Layer 3 tools)
  ↓  Stored locally in research/ (Layer 2)
opportunity_card (after your assessment)
  ↓  Also stored in research/ (Layer 2)
opportunity_decision (your approve/park/reject)
  ↓  Triggers workflow via Layer 3 framework
opportunity_followup_workflow (created by Layer 3)
  ↓  Execution tracked via Run Ledger (Layer 3)
```

**Critical rule:** The boundary is enforced at the `knowledge_source_ref` level — any reference to Layer 1 or Layer 2 content in Layer 3 must use opaque, local-only identifiers, never file paths or content.

```yaml
# ✅ Correct — Layer 3 references a signal with local-only ID
knowledge_source_ref:
  type: private_knowledge_os
  ref_id: "96a7b3e1"
  public: false

# ❌ Wrong — exposes Layer 1/2 structure
knowledge_source_ref:
  path: /Users/you/AI-Knowledge-OS/amazon/seller-finance/README.md
```

---

## What Ships (Layer 3 — Public)

| Artifact | File | Purpose |
|:---------|:-----|:--------|
| Opportunity data boundary | `docs/opportunity/OPPORTUNITY-DATA-BOUNDARY.md` | This document |
| Example config | `config/opportunity.example.yaml` | Template for instance config |
| Opportunity CLI | `scripts/opportunity.py` | List, show, approve, park, reject |
| CEO command wrapper | `scripts/ceo_cmd.py opportunity` | Unified entry point |
| Opportunity types | `scripts/opportunity.py` (constants) | `OPPORTUNITY_SIGNAL`, `OPPORTUNITY_CARD`, etc. |
| Run Ledger events | `scripts/opportunity.py` (recorded) | `opportunity_signal_created`, etc. |
| Workflow bridge | `scripts/workflow_runner.py` (existing) | Approve → create workflow |

## What Stays Local (Layer 1 & 2 — Private)

| Artifact | File | Purpose |
|:---------|:-----|:--------|
| Real opportunity cards | `research/opportunity-pool/` | Your OP-001 through OP-00n |
| Real watchlist | `research/watchlist.yaml` | Your focus domains |
| Real market signals | `research/source-notes/` | Raw signal data |
| Real config | `config/opportunity.yaml` | Your instance configuration |
| Personal knowledge | `~/AI-Knowledge-OS/` | Your knowledge base |

---

## Enforcement

### Release Hygiene Check (in `ai-company-os-release` skill v2.0)

Before any release:

```bash
# Layer 2 must never be tracked
git ls-files research/ | wc -l          # Expected: 0
git ls-files config/opportunity.yaml | wc -l  # Expected: 0
git log --all -- research/ | wc -l      # Expected: 0
```

### .gitignore (current state)

```
research/
config/opportunity.yaml
config/company-instance.yaml
```

### If a breach is detected

1. Stop the release
2. Run `git rm --cached -r <path>` to stop tracking
3. Add path to `.gitignore`
4. If the file exists in history, use `git filter-repo` (see `docs/known-issues/PRIVATE-RESEARCH-DATA-CLEANUP-v0.30.1.md`)
5. Record the incident in `docs/known-issues/`
