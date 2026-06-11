# Public / Private Release Boundary v0.1

**Status:** Accepted
**Date:** 2026-06-12
**Scope:** Public Git history, GitHub pushes, releases, and public evidence

## 1. Purpose

AI Company OS currently uses a **source-visible public repository**, not an
OSI-approved open-source license. The repository is All Rights Reserved.
Whether the project later becomes Open Core or adopts another licensing model
is a separate commercial and licensing decision.

The current operating model is:

> Source-visible public repository + public evidence layer + private
> commercial asset protection.

GitHub exists to prove that AI Company OS has real architecture, interfaces,
tests, auditability, commits, and working loops. It is not the storage location
for all company knowledge, operational data, commercial judgment, or
proprietary capability.

This document adds the missing release decision layer: whether a file or
commit may enter public Git history. It does not replace:

- `README.md` repository and license statements;
- `.gitignore` as the first filesystem safeguard;
- `docs/GITHUB-UPDATE-SOP.md` as the public evidence update policy;
- `docs/governance/SAFE-OUTPUT-POLICY.md` as the output redaction policy;
- `docs/architecture/ai-company-os-core-architecture-map.md` as the
  architecture-level public/private boundary; or
- `docs/known-issues/PRIVATE-RESEARCH-DATA-CLEANUP-v0.30.1.md` as the record of
  the previous history-cleanup incident.

For GitHub publication decisions, this boundary is stricter than a general
"safe output" classification. An output being valid for internal use does not
make it safe to publish.

## 2. Core Principles

1. AI Company OS uses limited public visibility, not complete open source.
2. Public material demonstrates architecture, interfaces, governance, tests,
   redacted evidence, and accepted public build history.
3. Founder judgment, real product-line execution data, customer/user data,
   raw capability requests, private playbooks, raw materials, commercial
   secrets, and proprietary modules remain private.
4. Methodology, templates, and playbooks require classification. Unclassified
   material is not public.
5. Every push requires an incremental Push Readiness Gate over
   `upstream..HEAD`.
6. A push may contain only accepted commits. It must not acquire untracked
   files, local media, pilot databases, CEO briefs, temporary scripts, or
   private data.
7. Ambiguous material enters `needs_founder_decision` and is not pushed by
   default.

## 3. Classification Model

Every proposed public file must receive one of these classifications:

| Classification | Meaning | Default action |
|---|---|---|
| `public_safe` | Reviewed and suitable for permanent public Git history | May be proposed for commit and push |
| `private_only` | Must remain in local or private storage | Do not commit or push |
| `needs_redaction` | Source is private, but a new reviewed derivative may be public | Keep original private; review derivative separately |
| `archive_only` | Retained as internal historical evidence, not current public guidance | Do not push as active public material |
| `needs_founder_decision` | Sensitivity, competitive value, or publication value is unclear | Fail closed; Founder decides |
| `must_not_push` | Secrets, databases, customer data, private raw material, or equivalent hard prohibition | Block push immediately |

`must_not_push` cannot be downgraded by an ordinary technical or governance
review. Publication requires a newly generated, separately reviewed redacted
derivative. Renaming or moving the original file does not make it public-safe.

Classification applies to content, not merely paths or extensions. A Markdown
file can be private, and a JSON report can be public-safe only after
field-level review.

## 4. Public-Safe Candidates

The following may become `public_safe` after acceptance and content review:

- public architecture documents, ADRs, public roadmaps, and architecture maps;
- public-safe PRDs and plans without real customer, operational, or commercial
  secrets;
- interfaces, schemas, and contracts, including public-safe WorkOrder,
  Attempt, Review, Audit, Runtime Adapter, CEO Agent, and Promotion contracts;
- migration harnesses, read-only validation, no-write tests, and other
  non-mutating verification;
- evidence derivatives containing only approved fields such as aggregate
  counts, hashes, state, classification, and timestamps;
- `pilot_non_authoritative` demo code that contains no private data and cannot
  be mistaken for operational authority;
- methodology, templates, rules, and playbooks that have been individually
  reviewed and accepted as public-safe; and
- accepted public build records that do not expose private paths, raw prompts,
  operational payloads, or proprietary judgment.

No category is automatically public-safe by filename, directory, or document
type. Evidence reports require field-level inspection. Methodology, templates,
Opportunity Rules, and playbooks remain `needs_founder_decision` until
explicitly classified, especially when they contain proprietary scoring or
decision logic.

## 5. Private and Prohibited Material

### 5.1 Must Not Push

The following are hard blockers:

- `private/`;
- `backend/data/` and operational database files;
- Pilot databases, including `.ai-company-os/pilot/`;
- `AI-Knowledge-OS/private/` and private personal knowledge;
- `.env` files, API keys, tokens, credentials, private keys, account data, and
  contracts;
- customer, user, employee, or personal sensitive data;
- local absolute paths or machine-specific identifiers;
- raw prompts, transcripts, entity notes, raw notes, and unsanitized context;
- raw capability request inputs and outputs;
- unredacted product-line inputs, outputs, cost records, and operational data;
- unredacted operational-derived reports;
- proprietary scoring, evaluation rules, commercial judgment, and core
  proprietary modules; and
- any file known to contain secrets or third-party data without publication
  rights.

### 5.2 Private by Default

The following are `private_only` or `needs_founder_decision` unless separately
approved:

- CEO briefs and Founder private judgment;
- real commercial routes, pricing hypotheses, and product-line roadmaps;
- `.codex-task.md`, `read_script.py`, temporary tools, one-off execution
  scripts, and generated local artifacts;
- TC-001, illegal or anomalous filenames, and malformed task artifacts;
- unaccepted S0/F0/RT/VSDP/PRD drafts;
- images, audio, video, and demo assets not separately approved;
- private methodology, playbooks, templates, and capability supply-chain
  material; and
- raw Approved Asset examples or AI Army Live/Replay data.

## 6. Founder Decision Zone

The following always require explicit classification rather than automatic
publication:

- RT3 / RT4 and other migration or reconciliation reports;
- methodology, templates, and playbooks;
- product-line roadmaps and Opportunity rules;
- AI Army Live or Replay demo data;
- Approved Asset examples;
- `os-assets` or registry-related documents; and
- operational-derived reports.

Founder review must consider both privacy and competitive value. Redaction is
not sufficient when the remaining structure reveals proprietary strategy.

## 7. Push Readiness Gate v0.1

Every push must be separately authorized and preceded by a gate over the exact
increment:

```text
upstream..HEAD
```

The gate must refresh the remote reference without merging or rebasing, then
report:

- `WILL_PUSH`: commits and files included in the increment;
- `WILL_NOT_PUSH`: unstaged, untracked, ignored, or otherwise local material;
- `MUST_NOT_PUSH`: prohibited content found in the increment;
- `NEEDS_FOUNDER_DECISION`: ambiguous content in the increment.

The gate must confirm:

1. upstream branch and fetch result;
2. ahead/behind status after fetch;
3. exact unpushed commit list;
4. exact unpushed file list;
5. every unpushed commit has been accepted;
6. secret, token, credential, and private-key scan;
7. local absolute-path scan;
8. prohibited directory and filename scan;
9. staged and untracked material cannot be accidentally included;
10. the recommended push command and target branch; and
11. no push occurred without separate Founder authorization.

Any `must_not_push` finding makes the gate `BLOCK`. Any unresolved
`needs_founder_decision` finding makes the gate `REVISE`. Only an empty blocker
set permits `PASS`.

`.gitignore` is only the first line of defense. It does not protect sensitive
files already tracked by Git, content placed outside an ignored path, or
secrets embedded in otherwise public-safe files. It never replaces the Push
Readiness Gate.

## 8. Known Repository Gap: CEO Briefs

`reports/ceo-briefs/` contains historical tracked files, while newer briefs
remain untracked. CEO briefs can contain real WorkOrder summaries, runtime
health, budget warnings, and Founder decisions.

The v0.1 rule is:

- no new or modified CEO brief may enter a public commit;
- whether to retain or remove the historical tracked briefs requires a
  separate Founder decision; and
- this v0.1 boundary does not authorize history rewriting or cleanup.

## 9. Non-Goals and Mainline Impact

This document does not:

- decide the final open-source or Open Core license;
- authorize publication of any currently untracked file;
- clean directories or rewrite Git history;
- change `.gitignore`;
- move private, raw, report, or media files;
- implement automated release scanning; or
- classify the entire repository retrospectively.

This is a lightweight governance side-track. It does not block VS-003 or other
accepted product work. Until automation is separately authorized, the manual
Push Readiness Gate remains mandatory.
