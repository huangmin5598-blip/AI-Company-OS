# Repository Cleanup Plan — v0.4.1

> **Goal**: Transform GitHub from a personal experiment dumpster into a product repository + public evidence layer + operating kit entry point for AI Company OS.
>
> **New positioning**: *An operating system for AI-native companies — starting from solo founders.*
>
> **Important**: This cleanup targets the current branch structure only. No `git filter-repo` or history rewriting unless sensitive data is found during the pre-push audit.

---

## 1. Target Directory Structure

```
AI-Company-OS/
├── README.md                  ← Rewritten with new positioning
├── LICENSE
├── .env.example
├── .gitignore
│
├── backend/                   ← Unchanged (product code)
├── frontend/                  ← Unchanged (product code)
├── config/                    ← v0.4.1 addition
│   └── company-instance.example.yaml
│
├── docs/
│   ├── architecture/          ← v0.4.1 addition
│   ├── prd/                   ← Unchanged (v0.2-v0.4 PRDs)
│   ├── releases/              ← Unchanged (v0.1.1-v0.4 release notes)
│   ├── build-logs/            ← Unchanged
│   ├── constitution/          ← Migrated from root-level .md files
│   │   ├── AI-COMPANY-OS-CONSTITUTION.md
│   │   └── legacy-archives/   ← Valuable conceptual docs archived here
│   │       └── AGENTS.md, SOUL.md, HEARTBEAT.md, etc.
│   ├── legacy/
│   │   └── README.md          ← Migration history explanation only (no raw content)
│   └── AI-COMPANY-OS-ROADMAP.md  ← Updated with v0.4.1+ narrative
│
├── examples/                  ← Evidence of real usage, not raw data
│   ├── novel-v1/
│   │   ├── README.md
│   │   ├── workflow-summary.md
│   │   └── evidence-links.md
│   └── skills/
│       ├── ceo-agent-skill.example.md
│       └── memory-recall-skill.example.md
│
├── evidence/                  ← Unchanged (public evidence dashboard)
└── assets/
    └── screenshots/           ← Unchanged
```

---

## 2. File Disposition Table

### 2.1 Root-level .md files (17 files)

| File | Disposition | Destination |
|:-----|:------------|:------------|
| `README.md` | Rewrite | Same location |
| `AGENTS.md` | Move | `docs/constitution/legacy-archives/AGENTS.md` |
| `SOUL.md` | Move | `docs/constitution/legacy-archives/SOUL.md` |
| `IDENTITY.md` | Delete | Content superseded by README + constitution |
| `TOOLS.md` | Move | `docs/constitution/legacy-archives/TOOLS.md` |
| `USER.md` | Delete | Historical, no product value |
| `HEARTBEAT.md` | Move | `docs/constitution/legacy-archives/HEARTBEAT.md` |
| `ROUTING-RULES.md` | Move | `docs/constitution/legacy-archives/ROUTING-RULES.md` |
| `TASK-POOL.md` | Move | `docs/constitution/legacy-archives/TASK-POOL.md` |
| `BUSINESS-GUARANTEE-RULES.md` | Delete | Outdated concept |
| `BUSINESS-TRIGGER-PROTOCOL.md` | Delete | Outdated concept |
| `CAPABILITY-REGISTRY.md` | Delete | Superseded by product code |
| `CONTROL-CENTER-V1-P0.md` | Delete | Superseded by v0.2-v0.4 |
| `LEAD-OS-ROLE.md` | Delete | Outdated concept |
| `OS-CAPABILITY-POOL.md` | Delete | Outdated concept |
| `AI-COMPANY-CONTROL-CENTER-v0.1.1-GITHUB-PUBLISH-REPORT.md` | Move | `docs/legacy/reports/` |
| `AI-COMPANY-CONTROL-CENTER-v0.1.1-RELEASE-EVIDENCE-SUMMARY.md` | Move | `docs/legacy/reports/` |

**Note**: Files being moved to `docs/constitution/legacy-archives/` preserve historical design thinking without cluttering the root. They are still in the repo, just hidden behind two directory levels.

### 2.2 `archive/` directory (~700+ files)

| Category | Disposition | Notes |
|:---------|:------------|:------|
| `__MACOSX/` (all occurrences) | Delete | Garbage files |
| `agent_arch-v1-old/` full agent SOUL/config (50+ agents) | Delete from main branch. **Local backup only** | Never deployed agents from conceptual phase |
| `agent_arch-v2-old/` (duplicate of v1) | Delete from main branch. **Local backup only** | Redundant |
| `book_extracted-old/` (56 chapters × 2 versions, docx+txt) | Delete from main branch. **Local backup only** | Book drafts, not part of product |
| `ai-landing-page-old/` (docx/pdf) | Delete from main branch. **Local backup only** | Old marketing materials |
| `meme-pet/` full project | Delete from main branch. **Local backup only** | Abandoned side project |
| `memory/` heartbeat logs | Delete | Local runtime artifacts |
| `run-config/` | Delete | Local runtime config |
| `experiments-old/` | Delete from main branch. **Local backup only** | Superseded by structured build logs |
| `legacy-build-logs/` | Migrate | `docs/build-logs/legacy/` |
| `system/`, `team/`, `templates/` | Delete | Outdated |
| `agents/` (amazon-selections, daily-finance) | Delete from main branch. **Local backup only** | Old agent definitions |
| `logs/` | Delete | Local runtime artifacts |
| `cases/`, `copyright-blacklist.md` | Delete | Not product-relevant |
| `chat_history_export.md` | Delete | Personal chat export |
| `avatars/` | Delete | Media file |
| `livebench-old/` | Delete from main branch. **Local backup only** | Experiment data |
| `architecture_advice.html` | Delete | Historical advice document |
| `task-panel-skill/` | Delete | Local skill artifact |

### 2.3 `skills/` directory (~50+ skills, ~150 files)

| Action | Detail |
|:-------|:-------|
| Remove entire `skills/` from main branch | These are local Hermes configurations, not product code |
| Local backup | Keep full `skills/` locally at `~/.hermes/skills/` |
| Example skills | Create `examples/skills/` with 2 representative examples |

### 2.4 `novel-v1/` directory (~150 files)

| Action | Detail |
|:-------|:-------|
| Remove `manuscripts/` (all .docx, .txt, .md drafts) | Local backup only — raw output not needed in product repo |
| Remove `TASK-CARDS/` | Local backup |
| Remove `checkpoints/` | Local backup |
| Remove `outlines/` | Local backup |
| Keep `registry/` | Move to `examples/novel-v1/` as evidence of project registry structure |
| Create `examples/novel-v1/README.md` | Project overview |
| Create `examples/novel-v1/workflow-summary.md` | Multi-agent pipeline description |
| Create `examples/novel-v1/evidence-links.md` | Links to build logs and release evidence |
| Keep `v3-acceptance-tests.md` | Move to `examples/novel-v1/` as acceptance evidence |
| Keep `v3-agent-templates.md` | Move to `examples/novel-v1/` as template evidence |
| Keep `asset-layer-phase1.md` | Move to `examples/novel-v1/` as evidence |
| Keep `README.md` | Move to `examples/novel-v1/` |

### 2.5 Other directories

| Directory | Disposition | Notes |
|:----------|:------------|:------|
| `backend/` | Keep | Product code — unchanged |
| `frontend/` | Keep | Product code — unchanged |
| `control-center/` | Delete | Superseded by frontend/ product code |
| `docs/` (already in product) | Keep | Needs reorganization under new structure |
| `evidence/` | Keep | Public evidence dashboard — unchanged |
| `assets/` | Keep | Screenshots and assets — unchanged |
| `landing/` | Delete | Outdated landing pages |
| `memory/` | Delete | Runtime artifacts |
| `policy/` | Delete | Old policy files |
| `scripts/` | Delete | Local scripts, not product |
| `sticker-v1/` | Delete | Abandoned project |
| `.openclaw/` | Delete | Local tool config |
| `projects/` | Delete | Old project hub — content superseded by examples/ |
| `novel-v1/` | Transform | → `examples/novel-v1/` |
| `skills/` | Remove | → `examples/skills/` |
| `archive/` | Remove | **Local backup only** |

---

## 3. README Rewrite Draft

```markdown
# AI Company OS

**An operating system for AI-native companies — starting from solo founders.**

AI Company OS helps founders and small AI-native teams manage AI agents, task loops, approvals, company memory, runtime visibility, and self-improvement workflows.

It started as a real solo-founder operating system. The long-term goal is broader: a company-level operating layer for teams that use AI agents as part of their daily execution system.

Most people are building agents. We are building the operating system around them.

---

## Current Status

AI Company Control Center has reached v0.4.

The system now includes:

- **Runtime Visibility** — agents, runs, costs, alerts, and execution records.
- **Company Loop MVP** — Alert / Command / Manual Input → Task → Context Pack → Approval → Execute → Review → Learning Candidate.
- **CEO Agent Lite** — Founder natural language goals can be decomposed into tasks and routed into the company loop.
- **Company Memory MVP** — approved learning candidates can become searchable organizational memory and be recalled by the CEO Agent.
- **Command Center Alpha** — a guarded command interface with dry-run and confirmation gates.

---

## Version Milestones

| Version | Layer | What It Proves | Status |
|:--------|:------|:---------------|:------:|
| v0.1.1 | Visibility + Control | The system reads real runtime data and exposes it in a Founder dashboard. | ✅ |
| v0.2 | Company Loop MVP | Alerts and commands become tasks with context, approval, review, and learning candidates. | ✅ |
| v0.3 | CEO Agent Lite | Founder intent enters the OS through natural language and becomes structured tasks or approvals. | ✅ |
| v0.4 | Company Memory MVP | Approved learning candidates become searchable organizational memory. | ✅ |
| v0.4.1 | Productization & Runtime Readiness | OS Core separates from company-specific configuration. | 🚧 |
| v0.5 | Monitor Framework Lite | The system observes itself and proposes improvements. | Planned |

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
```

---

## 4. Execution Steps

### Precondition Checklist

Before any execution, verify all of these:

- [ ] v0.2, v0.3, v0.4 are committed, tagged (`git tag -l "v0*"`), and pushed to GitHub (`gh release list`)
- [ ] Working tree is clean (`git status --short` shows nothing except REPO-CLEANUP-PLAN.md)
- [ ] GitHub Releases exist for v0.2, v0.3, v0.4 (`gh release list`)
- [ ] Local backup directory created for archive/, skills/, novel-v1/
- [ ] No .env, .db, token, or private keys are currently tracked (`git ls-files | grep -iE '\.env$|\.db$|token|secret|sk-'`)

### Step A: Preparation (Safety First + Local Backup)

```bash
cd ~/Documents/Codex/ai-company-os

# --- Precondition check ---
echo "=== Tags ===" && git tag -l "v0*"
echo "=== Releases ===" && gh release list --limit 10 2>/dev/null
echo "=== Working tree ===" && git status --short
echo "=== Sensitive files check ===" && git ls-files | grep -iE '\.env$|\.db$|token|secret|sk-' || echo "None found"

# --- Local backup (real files, not just git tag) ---
mkdir -p ~/AI-Company-OS-local-backups/pre-repo-cleanup-v0.4.1
cp -a archive ~/AI-Company-OS-local-backups/pre-repo-cleanup-v0.4.1/archive
cp -a skills ~/AI-Company-OS-local-backups/pre-repo-cleanup-v0.4.1/skills
cp -a novel-v1 ~/AI-Company-OS-local-backups/pre-repo-cleanup-v0.4.1/novel-v1
echo "Local backup complete"

# --- Cleanup branch + tag ---
git checkout -b repo-cleanup-v0.4.1
git tag backup/pre-repo-cleanup-v0.4.1
```

### Step B: Create New Directory Structure (before deleting anything)

```bash
mkdir -p docs/architecture
mkdir -p docs/constitution/legacy-archives
mkdir -p docs/legacy/reports
mkdir -p examples/novel-v1
mkdir -p examples/skills
```

### Step C: README + Roadmap Update

Replace `README.md` with the rewritten version (draft in Section 3 above).

Update `docs/AI-COMPANY-OS-ROADMAP.md` to:
- Add v0.4.1 row
- Update v0.5 description to "Monitor Framework Lite"
- Remove "Not Planned" items that are stale

### Step D: Write Legacy Explanation

Create `docs/legacy/README.md`:

```markdown
# Legacy Materials

Earlier experimental materials, raw manuscripts, legacy runtime configs, and abandoned
side projects have been moved out of the main branch to keep this repository focused
on AI Company OS as a product and evidence layer.

These materials are preserved in local backups. Key historical design documents that
still hold conceptual value have been archived under `docs/constitution/legacy-archives/`.

If you're looking for:
- **Old agent architecture designs** → `docs/constitution/legacy-archives/`
- **novel-v1 raw manuscripts** → Local backup only (summary in `examples/novel-v1/`)
- **Hermes skills** → Local Hermes installation (`~/.hermes/skills/`)
- **Archive of all pre-v0.2 materials** → Local backup
```

### Step E: Migration (Move, then Delete)

**Phase 1 — Safe migrations (add first, remove after):**

```bash
# Move conceptual docs
git mv AGENTS.md docs/constitution/legacy-archives/AGENTS.md
git mv SOUL.md docs/constitution/legacy-archives/SOUL.md
git mv TOOLS.md docs/constitution/legacy-archives/TOOLS.md
git mv HEARTBEAT.md docs/constitution/legacy-archives/HEARTBEAT.md
git mv ROUTING-RULES.md docs/constitution/legacy-archives/ROUTING-RULES.md
git mv TASK-POOL.md docs/constitution/legacy-archives/TASK-POOL.md

# Move old reports
git mv AI-COMPANY-CONTROL-CENTER-v0.1.1-GITHUB-PUBLISH-REPORT.md docs/legacy/reports/
git mv AI-COMPANY-CONTROL-CENTER-v0.1.1-RELEASE-EVIDENCE-SUMMARY.md docs/legacy/reports/

# Move legacy build logs — verify dir exists first
ls -d archive/legacy-build-logs 2>/dev/null && mkdir -p docs/build-logs/legacy && git mv archive/legacy-build-logs/* docs/build-logs/legacy/ && echo "Legacy build logs migrated" || echo "No legacy-build-logs found, skipping"
```

**Phase 2 — Delete from main branch:**

```bash
# --- Verify legacy build logs migrated before deleting archive ---
echo "=== Verify legacy build logs ===" && ls docs/build-logs/legacy/ 2>/dev/null && echo "✅ Migrated" || echo "⚠️  Nothing to migrate"

# Delete entire directories
git rm -r archive/
git rm -r skills/
git rm -r novel-v1/       # (replaced by examples/novel-v1/ below)
git rm -r control-center/
git rm -r landing/
git rm -r memory/
git rm -r policy/
git rm -r scripts/
git rm -r sticker-v1/
git rm -r .openclaw/
git rm -r projects/

# Delete root-level concept files
git rm IDENTITY.md USER.md BUSINESS-GUARANTEE-RULES.md
git rm BUSINESS-TRIGGER-PROTOCOL.md CAPABILITY-REGISTRY.md
git rm CONTROL-CENTER-V1-P0.md LEAD-OS-ROLE.md OS-CAPABILITY-POOL.md
```

**Phase 3 — Add new example files:**

Create `examples/novel-v1/*` and `examples/skills/*` files.

### Step F: Pre-Push Audit (Sensitive Info Check)

```bash
# 1. Check for any tracked .env or secrets
git diff --cached --name-only | grep -iE '\.env$|token|secret|key|password'
git diff --cached | grep -iE 'api_key|api_secret|password|token|sk-'

# 2. Check for large binary files in diff
git diff --cached --stat | grep -E 'Bin|\.zip|\.docx|\.pdf|\.jpg|\.png|\.ico'

# 3. Check for local paths
git diff --cached | grep -E '/Users/|/home/|C:\\\\'

# If ANY issues found → stop, investigate, remove the offending file from commit
```

### Step G: Commit + Tag + Push

```bash
# Only commit if audit passes
git add -A
git commit -m "chore: reorganize repository for AI-native company OS positioning

- Rewrite README with new product positioning
- Move legacy conceptual docs to docs/constitution/legacy-archives/
- Remove archive/ from main branch (local backup preserved)
- Remove skills/ from main branch (examples kept)
- Transform novel-v1/ into examples/novel-v1/ (evidence only)
- Clean up root-level concept files
- Add docs/legacy/ with migration explanation
- Create examples/skills/ with representative samples

No git history was rewritten. Tags v0.1.1 through v0.4 remain intact."

# Create cleanup evidence tag (not a product version)
git tag -a v0.4.1-cleanup -m "Repository cleanup for AI Company OS product positioning"

# Push
git push origin repo-cleanup-v0.4.1
# After confirmation, merge to main:
# git checkout main && git merge repo-cleanup-v0.4.1 && git push origin main --tags
```

---

## 5. Risk Assessment & Rollback

### Risks

| Risk | Mitigation |
|:-----|:-----------|
| **Accidental deletion of needed file** | Files are only deleted from git (repo-cleanup branch); backup tag `backup/pre-repo-cleanup-v0.4.1` preserves full state |
| **Broken links in docs** | After migration, `git diff --cached --name-only` to identify all moved files; manually verify README links |
| **Sensitive data in old commits** | Sensitive data check in Step F. If found, stop and use `git filter-repo` before continuing |
| **External references broken** | GitHub Release Notes (v0.2, v0.3, v0.4) reference specific tags — tags are not affected by branch structure changes |

### Rollback

If anything goes wrong after pushing:

```bash
git checkout main
git reset --hard backup/pre-repo-cleanup-v0.4.1
git push origin main --force-with-lease
```

---

## 6. Post-Cleanup Checklist

- [ ] `git status` shows expected changes only (no surprise files)
- [ ] `README.md` renders correctly on GitHub
- [ ] All Release tags still exist (`git tag -l`)
- [ ] `backend/` and `frontend/` untouched
- [ ] `docs/prd/` and `docs/releases/` intact
- [ ] `evidence/` and `assets/` intact
- [ ] No `.env`, `.db`, token, or local paths in diff
- [ ] `docs/legacy/README.md` explains migration
- [ ] `examples/novel-v1/` has evidence summary (not raw manuscripts)
- [ ] `examples/skills/` has 2 representative .example.md files
- [ ] Push to branch first → confirm → merge to main

### Post-Execution Verification Commands

```bash
# 1. backend / frontend should NOT have been modified
echo "=== Backend diff ===" && git diff --name-status backup/pre-repo-cleanup-v0.4.1..HEAD -- backend/ | head
echo "=== Frontend diff ===" && git diff --name-status backup/pre-repo-cleanup-v0.4.1..HEAD -- frontend/ | head

# 2. README links sanity check
echo "=== Link check ===" && grep -R "(./" README.md docs/ --include="*.md" | grep -v "node_modules" | head -20

# 3. No large block directories remain
echo "=== Garbage check ===" && ls archive skills novel-v1 .openclaw control-center landing 2>/dev/null && echo "⚠️  Still exists!" || echo "✅ Clean"

# 4. Root directory should be clean
echo "=== Root .md files ===" && find . -maxdepth 1 -name "*.md" -print | sort

# 5. Tags preserved
echo "=== Tags ===" && git tag -l "v0*"
```
