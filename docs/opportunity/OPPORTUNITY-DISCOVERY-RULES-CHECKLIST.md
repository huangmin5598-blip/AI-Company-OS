# Opportunity Discovery Rules — Acceptance Checklist

> **Sprint A Verification** — Run this checklist after Sprint A to confirm the rules layer is complete and ready for Runner implementation.

---

## Rules Layer Verification

### 1. Candidate Types
- [ ] Schema distinguishes `venture_opportunity` and `os_improvement`
- [ ] Both types have unique required fields documented
- [ ] `recommended_route` enum covers both types (promote_signal, request_card, create_os_improvement_task, etc.)

### 2. Signal Sources
- [ ] 6 source types defined: user_complaint, ai_capability, market_trend, platform_shift, asset_scan, os_feedback
- [ ] Priority order documented (user_complaint = first)
- [ ] Each source has clear filter/gate criteria

### 3. Opportunity Engines
- [ ] 5 commercial engines: cash, attention, platform, content, knowledge_asset
- [ ] OS Evolution defined as horizontal tag (not separate engine)
- [ ] `primary_engine` + `secondary_engines` design adopted (not single-select)

### 4. Company Context
- [ ] `config/company-context.example.yaml` exists with public-safe fields
- [ ] Real `config/company-context.yaml` in `.gitignore`
- [ ] Context fields cover: founder_profile, strategic_principles, active_product_lines, current_focus

### 5. Evidence Gate
- [ ] Hard rules documented: no source_ref = no candidate
- [ ] Hard rules documented: C-tier news = weak_candidate only
- [ ] Hard rules documented: LLM must not invent pain
- [ ] `evidence_gate_status` field in schema (passed / needs_more_evidence / weak_candidate)

### 6. Product Line Mapping
- [ ] 8 product lines defined
- [ ] Every candidate must map to at least one product line
- [ ] `product-lines.example.yaml` includes preferred_engines, validation_style, distribution_channels per line

---

## Skill Verification

- [ ] `ai-company-os-opportunity-discovery` Skill updated with hard rules
- [ ] Skill explicitly states: "Do not invent pain. Do not invent users."
- [ ] Skill explicitly states: "User complaints have priority over generic trends."
- [ ] Skill explicitly states: "Weak evidence → weak_candidate or needs_more_evidence"
- [ ] Skill references Company Context and Evidence Gate

---

## Documentation Verification

- [ ] `OPPORTUNITY-DISCOVERY-RULES.md` covers dual-loop (venture + self-improvement)
- [ ] `CANDIDATE-SIGNAL-SCHEMA.md` covers both candidate types with examples
- [ ] `config/schemas/candidate_signal.schema.json` validates schema
- [ ] `config/examples/manual-source-note.example.yaml` defines Sprint B input format
- [ ] `config/company-context.example.yaml` defines Company Context structure
- [ ] `platform-profiles.example.yaml` covers all major platforms with connector_status
- [ ] `product-lines.example.yaml` includes mapping rules per line
- [ ] README/ROADMAP updated with constrained positioning (vision vs current layers)

---

## Data Boundary Verification

- [ ] `config/company-context.yaml` in `.gitignore`
- [ ] No real signals in any public example files
- [ ] All example files use sanitized/abstracted content
- [ ] OPPORTUNITY-DATA-BOUNDARY.md still current
