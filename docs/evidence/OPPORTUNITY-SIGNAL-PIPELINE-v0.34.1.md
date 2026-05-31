# v0.34.1 — Opportunity Signal Pipeline Validation Report

> **Date:** 2026-05-31
> **Scope:** Validate the v0.33+v0.34 signal pipeline end-to-end with product-line-specific data
> **Product Line:** AI Seller Finance
> **Pipeline:** SourceNote → Enrichment → Founder Review → Candidate → Draft

---

## Results

| Metric | Value |
|:-------|:-----:|
| Input SourceNotes | 6 |
| Enriched Signals | 6 |
| Auto-passed Evidence Gate | 1 (17%) |
| Founder Review required | 2 (33%) |
| Deep Research routed | 3 (50%) |
| Candidates generated | 2 |
| Draft generated | 1 |

---

## Key Findings

### 1. Pipeline is operational

The full pipeline ran end-to-end:
`SourceNote → Enrichment → Candidate → Draft`

### 2. Evidence Gate behaves correctly

- 5/6 signals were rightfully blocked from auto-promotion
- 0 false positives
- Conservative design prevents AI hallucination of users/pain

### 3. Two real gaps identified

| Gap | Impact | Fix |
|:----|:-------|:----|
| Chinese timing keywords missing | Chinese-language signals get stuck at why_now gate | v0.34.2: Add Chinese why_now keyword list |
| No `signal_role` type system | Market-validation signals (funding news, competitor moves) forced into pain detection pipeline | v0.34.2: Add signal_role enum (primary_pain / supporting_evidence / competitor_validation) |

---

## Architecture Verified

```
SourceNote (raw signal from connector)
    ↓
Enrichment Layer (v0.34)
    → Extract target_user / pain / why_now
    → Tag each field with evidence_status
    → Route: enrich_and_promote / review_needed / request_deep_research / dismiss
    ↓
Founder Review Patch (v0.34 Sprint C)
    → Generate review template
    → Founder fills gaps
    → apply-review updates enriched signal
    ↓
Candidate Pipeline (v0.32)
    → enriched_to_candidate_data() mapping
    → Evidence Gate
    → Scoring (10 dimensions)
    → Classification (engine / product line)
    ↓
Candidate Signal → Draft
```

---

## Next Steps

1. **v0.34.2 Signal Calibration Patch**
   - Chinese why_now keyword list
   - signal_role field on enriched signals
   - supporting_evidence reference linking

2. **v0.35 Source Coverage P0**
   - Expand signal sources (RSS, Product Hunt, G2)
   - More comprehensive product-line queries
