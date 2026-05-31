# Opportunity Discovery Loop — Rules & Methodology

> **Part of AI Company OS — the Opportunity Discovery Layer**
> Version: v2.0 / 2026-05-31

---

## Core Principle

AI Company OS is an **AI Agent Native Company Operating System** — it runs a full company loop: discover opportunities, initiate projects, build products, serve customers, collect feedback, and compound company assets.

The Opportunity Discovery Loop is the **first company-level closed loop**. It serves two cycles simultaneously:

**Cycle 1: Venture Opportunity Loop** — Find commercial opportunities that can become cash-generating products, content, tools, or services.

**Cycle 2: Company Self-Improvement Loop** — Scan the OS's own runtime data (failures, blocks, patterns) to discover how the system itself should evolve.

This document defines the **rules** that govern both cycles. Instance data (watchlists, signals, cards) stays in `research/`. Company Context stays in `config/company-context.yaml` — never committed.

**Hard rule:** Do NOT invent pain. Do NOT invent users. Do NOT upgrade weak news into opportunity cards. Every signal must trace back to a real source.

---

## 1. Six Signal Sources

Every candidate signal must declare its source. Sources are ordered by priority:

### Priority 1: User Complaints
**Why first:** Prevents AI from hallucinating opportunities.
**Sources:** User comments, forum posts, community questions, product reviews, Reddit, G2, App Store, Xiaohongshu, Zhihu, WeChat groups, customer support logs.
**Filter:** Is the pain real? Recurring? Do users pay for alternatives? Why are existing solutions bad?
**Gate:** Without source_ref and target_user, this signal cannot become a formal candidate.

### Priority 2: New AI Capabilities
**Sources:** New models, new APIs, agent frameworks, multimodal, code gen, video gen, voice, browser automation, OCR, local models.
**Filter:** Was it impossible before? Was it too expensive before? Can it become a micro-tool?

### Priority 3: Market Trends / Structural Shifts
**Sources:** Funding news, policy changes, platform rule changes, major launches, industry shifts, regulatory changes.
**Filter:** Why now? Is this short-term noise or structural shift? Can it convert to Cash or Attention?
**Gate:** C-tier generic news alone → **weak_candidate** only. Must pair with User Complaints or Asset Scan to upgrade.

### Priority 4: Platform Ecosystem Shifts
**Platforms to watch:** Roblox, Shopify, Amazon, TikTok Shop, Feishu, Notion, Chrome Extension, App Store, HarmonyOS, WeChat ecosystem.
**Filter:** Developer incentive? New API? New distribution mechanism? Low barrier for solo devs?

### Priority 5: Own Asset Scan
**Scan your own:** Existing code, docs, methodologies, course material, cases, knowledge base, GitHub evidence, existing Skills, business judgments.
**Filter:** Can this be packaged? Become a template? Become a course/book? Be an MVP starting point?
**Note:** This source often produces the highest Founder Fit signals — you're already 60-80% there.

### Priority 6: OS Runtime Feedback Scan
**Why this matters:** An AI-native company must learn from its own operations.
**Scan sources:** Run Ledger events, Asset Registry, Workflow failure records, Policy blocked events, CEO Briefs, Decision Log, Capability Boundary violations, Budget warnings.
**Output:** Identifies system-level improvements — new Skills needed, missing policies, recurring failures, automation opportunities.
**Gate (v0.32 P0):** DB-dependent scans fall back to `reports/` and `docs/` file scans if backend unavailable.

---

## 2. Opportunity Engine Types

Every signal is classified into one or more commercial engines, with an optional horizontal tag:

### Five Commercial Engines

| Engine | Description | Example Outputs |
|:-------|:------------|:----------------|
| **Cash Engine** | Quick-to-monetize tools, vertical products, micro-SaaS | Paid report, template, micro-SaaS |
| **Attention Engine** | Demo-worthy, shareable projects that attract audience/capital | Viral demo, GitHub star project |
| **Platform / Ecosystem Play** | Opportunities from platform hooks | Chrome extension, Shopify app, Roblox game |
| **Content / Entertainment Engine** | AI-generated content, IP, traffic products | AI short drama, AI music, knowledge videos |
| **Knowledge Asset** | Books, courses, case studies, Operating Kits, Skill packs | OS Kit, course, methodology book |

### Horizontal Tag: OS Evolution
Any signal can also carry the `os_compounding` or `os_improvement` tag. This indicates the signal isn't just about commercial value — it also strengthens AI Company OS itself.

Examples:
```
Amazon P&L Analyzer = Cash Engine + Knowledge Asset + OS Evolution
Evidence Dashboard = Knowledge Asset + Attention Engine + OS Evolution
Policy Resolver enhancement = OS Evolution + Governance improvement
```

**Design:** `primary_engine` (single) + `secondary_engines` (array, including os_evolution). Not single-select.

---

## 3. Candidate Types

Every candidate signal has a type:

| Type | Description | Example |
|:-----|:------------|:--------|
| **venture_opportunity** | Commercial opportunity — can become a product, tool, content, service | "AI Seller Finance Report" |
| **os_improvement** | System improvement opportunity — OS should evolve | "Recurring workflow block needs auto-recovery Skill" |

---

## 4. Scoring Model (10 Dimensions)

Each candidate signal is scored 1-5:

| # | Dimension | Description |
|:-:|:----------|:------------|
| 1 | pain_score | User pain intensity |
| 2 | evidence_score | Evidence strength (how many data points, complaint volume) |
| 3 | why_now_score | Timing window |
| 4 | founder_fit_score | Founder's fit (experience, resources, domain knowledge) |
| 5 | asset_leverage_score | Existing assets that can be reused |
| 6 | mvp_speed_score | Can MVP be validated in 3-7 days |
| 7 | distribution_score | Where first users come from |
| 8 | monetization_score | Can it be charged for |
| 9 | attention_score | Shareability / virality potential |
| 10 | os_compounding_score | Does it strengthen AI Company OS long-term |

---

## 5. Evidence Gate (Hard Rules)

A candidate signal MUST pass these gates before it can be promoted:

| Gate | Rule | Fail Behavior |
|:-----|:-----|:--------------|
| **source_ref** | Must have at least one verifiable source reference | Cannot generate candidate |
| **target_user** | Must identify a real user segment | Cannot generate candidate |
| **pain_description** | Pain must be grounded in source evidence, not LLM common sense | Cannot generate candidate |
| **why_now** | Must explain timing window | Outputs `needs_more_evidence` |
| **C-tier news** | Generic news without complaint/asset backing | Outputs `weak_candidate` only |

**LLM may NOT create pain from general knowledge. Pain must come from source evidence or existing company assets.**

---

## 6. Company Context

The discovery loop evaluates every signal against company context. Context is defined in `config/company-context.yaml` (local only, never committed):

| Context Field | Purpose |
|:--------------|:--------|
| founder_profile | Strengths, constraints, domain expertise |
| strategic_principles | Decision rules (e.g., "user complaints first", "cashflow before scale") |
| active_product_lines | Which lines are actively being built |
| current_focus | What the company is prioritizing now |
| asset_inventory | Known reusable assets (code, docs, methodologies) |

Without Company Context, the system cannot answer "is this opportunity right for us?"

---

## 7. Product Line Mapping

Every signal MUST map to at least one product line:

| Product Line ID | Description |
|:----------------|:------------|
| ai_company_os | Core OS capabilities |
| ai_seller_finance | Cross-border e-commerce finance |
| ai_content_products | AI content (articles/video/podcast) |
| ai_game_products | AI games / Roblox |
| ai_short_drama | AI short drama production |
| knowledge_assets | Books, courses, kits |
| saas_microtools | Micro-SaaS, Chrome extensions |
| platform_ecosystem_experiments | Platform play experiments |

---

## 8. Candidate Signal Schema

### venture_opportunity

```yaml
candidate_id: "CD-20260531-001"
candidate_type: "venture_opportunity"
title: "Signal title"
created_at: "2026-05-31T10:00:00Z"
signal_source:
  source_type: "user_complaint | ai_capability | market_trend | platform_shift | asset_scan | os_feedback"
  source_tier: 1 | 2 | 3
  source_refs:
    - url: "https://..."
      excerpt: "..."
signal_type: "pain | capability | trend | platform | asset | system_gap"
primary_engine: "cash_engine | attention_engine | platform_play | content_engine | knowledge_asset"
secondary_engines:
  - "os_evolution"  # optional
related_product_lines:
  - "ai_seller_finance"
company_context_refs:
  - "founder_fit: finance_domain_experience"
  - "asset_leverage: ai_company_os_codebase"
target_user: "Target user description"
pain: "Pain description grounded in source evidence"
evidence_summary: "Evidence summary"
why_now: "Why now is the window"
founder_fit_score: 4
asset_leverage_score: 4
mvp_wedge: "Minimum viable validation wedge"
distribution_hint: "Possible acquisition channels"
risk: "Risk factors"
missing_evidence: "What still needs validation"
evidence_gate_status: "passed | needs_more_evidence | weak_candidate"
recommended_route: "promote_signal | request_card | request_deep_research | park | dismiss"
status: "candidate"
```

### os_improvement

```yaml
candidate_id: "CD-20260531-002"
candidate_type: "os_improvement"
title: "Recurring workflow X85 failures suggest need for auto-retry Skill"
created_at: "2026-05-31T10:00:00Z"
signal_source:
  source_type: "os_feedback"
  source_tier: 1
  source_refs:
    - type: "run_ledger_pattern"
      detail: "Workflow X85 failed 3 times in 7 days, same step"
signal_type: "system_gap"
primary_engine: "os_evolution"
secondary_engines: []
related_product_lines:
  - "ai_company_os"
target_user: "Founder / OS Operator"
pain: "Manual recovery overhead for recurring workflow failures"
evidence_summary: "Run Ledger shows 3 identical failures in 7 days"
why_now: "Failure rate is increasing; manual recovery takes ~15min per incident"
founder_fit_score: 5
asset_leverage_score: 3
mvp_wedge: "Add auto-retry logic to workflow_runner.py"
distribution_hint: "N/A — internal improvement"
risk: "Auto-retry may mask underlying issues"
missing_evidence: "Need to verify failures are transient, not structural"
evidence_gate_status: "passed"
recommended_route: "create_os_improvement_task"
status: "candidate"
```

---

## 9. Data Boundaries

- **Layer 1 (AI-Knowledge-OS/):** Full methodology, personal notes — NEVER git
- **Layer 2 (research/, config/company-context.yaml):** Real watchlists, real signals, real cards, real context — NEVER git
- **Layer 3 (this repo):** Rules schema, example configs, runner code — GIT

---

## 10. Guardrails

1. **User complaints first** — Prevents AI from hallucinating opportunities
2. **Own asset scan required** — Many opportunities are 60-80% built already
3. **Multi-classify** — One signal can hit multiple engines + OS Evolution tag
4. **Product line required** — Every signal must map to a product line
5. **Company Context required** — Without it, the system cannot assess Founder Fit
6. **Evidence Gate enforced** — No source_ref, no target_user, no pain → no candidate
7. **No auto-execute** — v0.32 only generates candidates for Founder review
8. **No scraping protected content** — WeChat paywalled articles, Zhihu login-walled, etc.
9. **C-tier news = weak_candidate** — Generic news alone is never promoted
10. **No inventing pain** — LLM must not create pain from general knowledge
