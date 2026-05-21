# Evidence Dashboard Lite V1

## Purpose

Evidence Dashboard Lite V1 is a lightweight public evidence surface for AI Company OS.

Its purpose is not to become a new internal operating system.

Its purpose is to make existing system progress legible to outside observers.

It should help a new visitor quickly understand four things:

- the system is running
- projects are progressing
- assets are growing
- governance mechanisms are working

## Why now

AI Company OS has already moved beyond simple proof-of-concept execution.

At the current stage, the system has already shown:

- real multi-agent project execution
- timeout / fallback / serial stability validation
- Memory Layer and Registry integration
- gateway-lite-v1 in operational use
- capability-registry-v1 and routing-layer-v1 in real usage validation
- control-center-v1 P0 forming the first internal control plane

The problem is no longer only internal execution.

The problem is external legibility.

A large portion of real progress already exists, but it is still too hard for outside observers to see and understand quickly.

Evidence Dashboard Lite V1 exists to solve that gap.

## What this is

Evidence Dashboard Lite V1 is:

- a lightweight evidence layer
- a structured public-facing summary surface
- a way to organize proof of system activity and progress

It is not:

- a full internal dashboard replacement
- a control center rebuild
- a heavy analytics platform
- a new product in itself

## Target audience

The dashboard should be understandable to at least four audiences:

### 1. Curious external observers
People who want to understand whether AI Company OS is real and active.

### 2. Potential followers / readers
People discovering the project from GitHub, X, or future public channels.

### 3. Potential partners / collaborators
People evaluating whether the system has real operating substance.

### 4. The founder and internal operators
A lightweight public snapshot can also help keep system progress legible internally.

## Core design principle

The dashboard should be evidence-first.

It should not try to impress through complexity.

It should focus on answering the simplest external questions:

- Is this system actually running?
- What projects is it working on?
- Is it producing outputs?
- Are assets accumulating?
- Is there visible governance and control?

## Core modules

The first version should focus on four modules.

### 1. System Running

**What it should show**
- overall system status
- latest run / heartbeat status
- most recent Build Logs
- whether the system is active in the current stage

**Why it matters**
This is the fastest way for an external viewer to answer:
"Is this system actually alive?"

**Possible data sources**
- recent build logs
- heartbeat-related records
- execution summaries
- control-center summaries

### 2. Project Progress

**What it should show**
- active projects
- current project stage
- recent outputs
- recent validations
- whether a project is in build, validation, or monetization mode

**Why it matters**
This makes AI Company OS concrete.

Instead of reading abstract system documents, an external viewer can immediately see what projects are currently moving.

**Possible data sources**
- /projects/
- /cases/
- launch logs
- project summaries
- project-level registry records

### 3. Asset Growth

**What it should show**
- total asset count by category
- latest additions by type
- examples of recent content / document / code / knowledge assets
- whether assets are growing over time

**Why it matters**
This is one of the strongest visible differences of AI Company OS.

The system is not only doing work. 
It is also accumulating company assets.

**Possible data sources**
- Registry
- Memory Layer outputs
- /assets/ pages
- asset ingestion summaries

### 4. Governance and Control

**What it should show**
- gateway summary
- routing summary
- capability overview
- CEO escalation summary
- system health snapshot

**Why it matters**
This shows that the system is not only executing blindly.

It is beginning to operate with routing, control, visibility, and governance.

**Possible data sources**
- control-center-v1 P0 outputs
- gateway-lite-v1 summaries
- capability-registry-v1
- routing-layer-v1
- system health records

## Suggested MVP structure

The first version should remain intentionally small.

A reasonable MVP structure is:

1. **System Running**
2. **Project Progress**
3. **Asset Growth**
4. **Governance and Control**

Optional additions later:
- Monetization Signals
- Recent Milestones
- Build Log Timeline
- Asset Trend Snapshot

## Data sources

Evidence Dashboard Lite V1 should not require a new data universe.

It should mostly be built on top of already existing materials.

Suggested inputs:

- `/docs/build-logs/`
- `/evidence/`
- `/assets/`
- `/projects/`
- registry records
- control-center-v1 P0 summaries
- gateway-lite-v1 summaries
- routing-layer-v1 summaries
- capability-registry-v1 records

## MVP scope

The MVP should focus on clarity, not completeness.

### In scope
- a lightweight structured evidence page
- clear module summaries
- recent status snapshots
- links to deeper evidence
- a readable external-facing structure

### Out of scope
- real-time monitoring
- complex charts
- full internal telemetry
- detailed per-agent drilldown
- advanced analytics
- building a new heavyweight dashboard subsystem

## Relationship to existing system components

Evidence Dashboard Lite V1 should sit above existing system components.

It should not replace:

- control-center-v1
- registry
- Memory Layer
- build logs
- asset pages

Instead, it should summarize them.

A good way to think about it is:

- Control Center = internal control surface
- Evidence Dashboard Lite = external evidence surface

## What success looks like

Evidence Dashboard Lite V1 is successful if an external viewer can understand the current system in a few minutes.

That means they can quickly see:

- the system is active
- there are real projects
- there are real outputs
- assets are accumulating
- governance is visible
- the system is evolving

## Why this matters strategically

At the current stage, AI Company OS already has meaningful internal capability.

But without an external evidence surface, much of that progress remains invisible.

This dashboard matters because it helps turn internal progress into public legibility.

That supports:

- stronger GitHub communication
- better public trust
- clearer storytelling
- easier onboarding for new observers
- future growth and commercialization narratives

## Next step

The next step is not full implementation.

The next step is to define the first version clearly and connect it to existing evidence sources.

Suggested immediate action:

1. confirm the first 4 modules
2. define the source files for each module
3. decide whether the first version lives as:
   - a structured GitHub page
   - a markdown evidence page
   - a simple landing-style summary page
4. keep it lightweight and evidence-first

---

*Planning Document | 2026-03-31*