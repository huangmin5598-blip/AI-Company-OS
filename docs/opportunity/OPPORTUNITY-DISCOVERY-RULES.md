# Opportunity Discovery Engine — Rules & Methodology

> **Part of AI Company OS — the Venture Engine Layer**
> Version: v1.0 / 2026-05-31

---

## Core Principle

AI Company OS is a **venture engine** — it continuously discovers opportunities, launches projects, builds products, and validates revenue. The Opportunity Discovery Engine is the layer that makes this possible.

This document defines the **rules** that govern how opportunities are discovered, classified, scored, and mapped to product lines. It is a **framework** — instance data (your watchlists, signals, cards) stays in `research/`.

---

## 1. Five Opportunity Engines

Every signal must be classified into one or more of these engines:

| Engine | Description | Example Outputs |
|:-------|:------------|:----------------|
| **Cash Engine** | Quick-to-monetize tools, vertical products, micro-SaaS | Paid report, template, micro-SaaS |
| **Attention Engine** | Demo-worthy, shareable projects that attract capital/audience | Viral demo, GitHub star project |
| **Platform / Ecosystem Play** | Opportunities from platform ecosystem shifts/hooks | Chrome extension, Shopify app, Roblox game |
| **Content / Entertainment Engine** | AI-generated content, IP, traffic products | AI short drama, AI music, knowledge videos |
| **Knowledge Asset** | Books, courses, case studies, Operating Kits, Skill packs | OS Kit, course, methodology book |

A single signal can hit multiple engines:
```
cash_engine + platform_play
content_engine + attention_engine
knowledge_asset + os_evolution
```

---

## 2. Five Signal Sources

### 2.1 User Complaints (Priority #1)
**Sources:** User comments, forum posts, community questions, product reviews, Reddit, G2, App Store, Xiaohongshu, Zhihu, WeChat groups

**Filter:** Is the pain real? Recurring? Do users pay for alternatives? Why are existing solutions bad?

### 2.2 New AI Capabilities
**Sources:** New models, new APIs, agent frameworks, multimodal, code gen, video gen, voice, browser automation, OCR, local models

**Filter:** Was it impossible before? Was it too expensive before? Can it become a micro-tool?

### 2.3 Market Trends / Structural Shifts
**Sources:** Funding news, policy changes, platform rule changes, major launches, industry shifts, regulatory changes

**Filter:** Why now? Is this short-term noise or structural shift? Can it convert to Cash or Attention?

### 2.4 Platform Ecosystem Shifts
**Platforms to watch:** Roblox, Shopify, Amazon, TikTok Shop, Feishu, Notion, Chrome Extension, App Store, HarmonyOS, WeChat ecosystem

**Filter:** Developer incentive? New API? New distribution mechanism? Low barrier for solo devs?

### 2.5 Own Asset Scan (Often Overlooked)
**Scan your own:** Existing code, docs, methodologies, course material, cases, knowledge base, GitHub evidence, AI Operating System, existing Skills, existing business judgments

**Filter:** Can this be packaged? Become a template? Become a course/book? Be an MVP starting point?

---

## 3. Scoring Model (10 Dimensions)

Each candidate signal is scored 1-5 on:

| # | Dimension | Description |
|:-:|:----------|:------------|
| 1 | pain_score | User pain intensity |
| 2 | evidence_score | Evidence strength (how many people complain, data points) |
| 3 | why_now_score | Timing window |
| 4 | founder_fit_score | Founder's fit (experience/resources/interest) |
| 5 | asset_leverage_score | Existing assets that can be reused |
| 6 | mvp_speed_score | Can MVP be validated in 3-7 days |
| 7 | distribution_score | Where first users come from |
| 8 | monetization_score | Can it be charged for |
| 9 | attention_score | Shareability / virality potential |
| 10 | os_compounding_score | Does it strengthen AI Company OS long-term |

---

## 4. Product Line Mapping

Each candidate signal must be mapped to at least one product line:

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

## 5. Candidate Signal Schema

```yaml
candidate_id: "CD-20260531-001"
title: "Signal title"
source_type: "user_complaint | ai_capability | market_trend | platform_shift | asset_scan"
source_tier: 1 | 2 | 3
signal_type: "pain | capability | trend | platform | asset"
opportunity_engine_types:
  - cash_engine
  - attention_engine
  - platform_play
  - content_engine
  - knowledge_asset
related_product_lines:
  - ai_company_os
  - ai_seller_finance
target_user: "Target user description"
pain: "Pain description"
evidence: "Evidence summary"
why_now: "Why now is the window"
founder_fit: "Founder match analysis"
asset_leverage: "Reusable existing assets"
mvp_wedge: "Minimum viable validation wedge"
possible_distribution: "Possible acquisition channels"
risk: "Risk factors"
missing_evidence: "What still needs validation"
recommended_next_step: "Recommended next action"
status: "candidate"  # candidate | dismissed | deep_research | promoted
```

---

## 6. Data Boundaries

What belongs where:
- **Layer 1 (AI-Knowledge-OS/):** Full methodology, personal notes — NEVER git
- **Layer 2 (research/):** Real watchlists, real signals, real cards — NEVER git
- **Layer 3 (this repo):** Rules schema, example configs, runner code — GIT

---

## 7. Guardrails

1. **User complaints first** — Prevents AI from hallucinating opportunities
2. **Own asset scan required** — Many opportunities are 60-80% built already
3. **Multi-classify** — One signal can hit multiple engines
4. **Product line required** — Every signal must map to a product line
5. **No auto-execute** — v0.32 only generates candidate signals for Founder review
6. **No scraping protected content** — WeChat paywalled articles, Zhihu login-walled, etc.
