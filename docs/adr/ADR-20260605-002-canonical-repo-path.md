# ADR-20260605-002 — Canonical Repo Path Rule

## Status
Active

## Date
2026-06-05

## Context

AI Company OS requires a single canonical GitHub-connected repo for all
public code, evidence, release, and external-facing work.

A source workspace was used for initial development (B1 results), but
all execution, release, and evidence work must use the canonical repo.

## Decision

**Canonical Repo Definition:**
- A GitHub-connected repository
- Contains all public code, docs, ADR, evidence, README
- Has correct git remote pointing to huangmin5598-blip/AI-Company-OS

**Source Workspace Role:**
- Used as B1 development source only
- NOT for ongoing execution or public work
- NOT for GitHub release

**Environment Variable for Path Resolution:**
```
AI_COMPANY_OS_CANONICAL_REPO
```

## Canonical Repo Properties (Required)

| Property | Requirement |
|----------|-------------|
| Git remote | https://github.com/huangmin5598-blip/AI-Company-OS.git |
| Git branch | main |
| private/ gitignored | Yes |
| Contains B1 migration results | Yes |

## Runtime Preflight (Blocking)

Before any Codex / Claude Code / GitHub task executes:

| Check | Pass Condition |
|-------|---------------|
| `current_realpath` | Equals canonical repo path |
| `git_toplevel_path` | Equals canonical repo path |
| `repo_root_matches_canonical` | `true` |
| Git remote | Correct GitHub remote URL |

**If any check fails → BLOCK. Do not execute.**

## Path Resolution

Actual paths are stored locally (not in tracked files):

```
private/runtime/local-paths.yaml
```

This file is gitignored. Agents read it at runtime for environment-specific paths.

## Binding Rules

### Must Use Canonical Repo
- Codex execution
- Claude Code execution
- GitHub release
- Public evidence updates
- README / documentation changes

### Source Workspace Restrictions
- NOT for Codex / Claude Code execution
- NOT for GitHub release
- NOT for public evidence updates

## Memory

This is a **blocking governance rule**, not a preference.
All AI agents operating in the AI Company OS context must obey it.
