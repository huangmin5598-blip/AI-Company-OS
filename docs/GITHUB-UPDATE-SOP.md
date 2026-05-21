# GitHub Continuous Update SOP

**Version**: 1.0
**Date**: 2026-03-31
**Purpose**: Define how GitHub continuously reflects AI Company OS real state

---

## GitHub Role

**Public Evidence Layer + Asset Display Layer + Running Record Layer**

Must continuously reflect 4 things:

1. System is running
2. Projects are advancing
3. Assets are accumulating
4. Mechanisms are evolving

---

## A. Event-Driven Updates

### A1. Project Progress Triggers

**Conditions**:
- New project launched
- Project enters new stage
- Project completes key validation
- Project forms showcase case
- Project output reaches display level
- Project status changes (paused/continued/pivoted)

**Update locations**: /projects/.../README.md, /cases/, /logs/launch-log.md

### A2. System Capability Triggers

**Conditions**:
- timeout/fallback/checkpoint/routing/registry/memory layer new changes
- patch rises to protocol or capability
- New protocol enters real use
- Control Center adds new displayable module
- System reliability/observability/recoverability improves

**Update locations**: /docs/build-logs/, /docs/protocols/, /evidence/system-evolution.md

### A3. Asset Accumulation Triggers

**Conditions**:
- New novel/article/script/image/video script produced
- New document/report/proposal produced
- New code module/script/support module formed
- New knowledge card/research card formed
- New workflow/prompt/template/SOP enters use

**Update locations**: /assets/ (5 files)

### A4. Commercial Progress Triggers

**Conditions**:
- New product launched
- New payment path cleared
- New pricing online
- New landing/transfer page online
- First sale/new sale/new monetization test
- New monetization hypothesis starts testing

**Update locations**: /logs/monetization-log.md, /cases/, README (if needed)

---

## B. Fixed Cycle Updates

### B1. Weekly GitHub Update

**Frequency**: Weekly (suggest Sunday)

**Content**:
1. This week project progress
2. This week system capability changes
3. This week new assets
4. Whether Build Log needs supplement
5. Whether new commercial actions

**Minimum update locations**: /logs/launch-log.md, /assets/, /logs/monetization-log.md

### B2. Monthly Evolution Review

**Frequency**: Monthly (end or beginning of month)

**Content**:
1. Most important project validation this month
2. Most important OS capability progress this month
3. Asset accumulation this month
4. Whether new system stage changes
5. Whether README Current Progress needs update

---

## C. Milestone Updates

**Milestones include**:
- New project pipeline verified
- Project first stable run
- System capability rises from patch to capability
- Memory Layer / Registry enters new stage
- Asset accumulation mechanism verified
- First revenue/external payment/first real monetization validation
- New OS P0 capability enters real use

---

## Update Mapping Table

| Trigger Type | Update Location |
|--------------|-----------------|
| Project progress | /projects/ + /cases/ + /logs/launch-log.md |
| System capability changes | /docs/build-logs/ + /docs/protocols/ + /evidence/system-evolution.md |
| Asset growth | /assets/ |
| Commercial progress | /logs/monetization-log.md + /cases/ + README |
| Stage changes | /evidence/system-evolution.md + README |

---

## Document Update Standards

### 7.1 Build Log

**Structure**:
- Title
- Background
- Setup / Change
- Execution / What was done
- Results
- Observations
- Operating Implications
- Next Step

**Requirements**: Write real changes, not abstract summaries. Explain why it matters and what it means for the system.

### 7.2 Evidence

**Requirements**: External-readable. Explain "what / why / how to connect / why important". Don't write as底层 implementation details pile.

### 7.3 Assets

**Requirements**: List asset name, type, date, source. Briefly explain why it's "company asset". Explain reuse value.

### 7.4 Project Case

**Requirements**: Project goal, pipeline/roles, current results, what it proves, why important.

### 7.5 Monetization Log

**Requirements**: Record real behavior, explain selling what, explain status, don't exaggerate revenue, don't fabricate results.

---

## Auto-Trigger Suggestions

1. **task_completed_event** → If output enters Registry and meets public display standard → Mark as assets pending update

2. **New protocol/patch/capability enters real use** → Mark as build log pending update

3. **Project reaches key status change** → Mark as project/case pending update

4. **Payment/pricing/product status changes** → Mark as monetization pending update

5. **Weekly/Monthly timer** → Trigger GitHub Update Review → Aggregate pending updates

---

## Return Requirements (After Each Update)

1. Trigger reason for this update
2. Which files were updated
3. Why each file was updated
4. What new evidence/assets/progress were added
5. Whether new Build Log needs to be added
6. This commit message

---

## Weekly Output Template

```
Week of [Date]

1. Project updates
- What projects did this week
- Which projects have new stage changes

2. OS updates
- What system capabilities changed this week
- Which changes are worth entering Build Log

3. Asset additions
- What new assets this week
- Which category: content/document/system/code/knowledge

4. Monetization notes
- Whether new monetization actions this week
- Whether product/payment/pricing/sale changes

5. Recommended GitHub updates
- Which files suggest updating
- Which can wait until next week
```

---

## Execution Boundaries

1. **Don't update for "looking diligent"** — No meaningful evidence, don't do superficial updates

2. **Don't let GitHub become log junk pile** — Every update must have information density

3. **Don't expose all internal details** — Only update content suitable for public evidence layer

4. **Don't frequently change README** — README only updates on obvious stage changes, no high-frequency small fixes

---

## Core Principle

GitHub's long-term goal is not "organizing repository".

But continuously proving:

- AI Company OS is running real projects
- Projects are continuously advancing
- System capabilities are continuously forming
- Company assets are continuously accumulating
- Commercialization paths are gradually validating

**One sentence**: GitHub updates not by "whether there's time", but by "whether there's new evidence".
