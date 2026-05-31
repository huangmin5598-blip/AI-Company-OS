#!/usr/bin/env python3
"""
v0.34 — Opportunity Enricher P0

Reads a SourceNote and produces an Enriched Signal by extracting/inferring
analytical fields (target_user, pain, why_now, signal_type) and tagging
each with its evidence status.

This is a RULE-BASED enricher — no LLM calls. All extraction is deterministic.
The goal is transparency: every field declares whether it is backed by
evidence, inferred, or missing.

Usage:
  python3 scripts/opportunity_enricher.py enrich --source-note <file>
  python3 scripts/opportunity_enricher.py enrich-batch --dir <dir>
  python3 scripts/opportunity_enricher.py review-needed
  python3 scripts/opportunity_enricher.py generate-review --id <id>
  python3 scripts/opportunity_enricher.py apply-review --id <id>
  python3 scripts/opportunity_enricher.py dismiss --id <id>
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Optional

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
_DEFAULT_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "research", "opportunity-enriched")
_SOURCE_DIR = os.path.join(_PROJECT_ROOT, "research", "opportunity-source-notes")

# ── Pain keywords (matches opportunity_scout.py) ──
_PAIN_KEYWORDS = [
    "spend hours", "manual", "frustrat", "pain", "headache",
    "waste", "expensive", "hard", "difficult", "no good solution",
    "too much time", "tedious", "annoying", "broken", "sucks",
    "problem", "issue", "struggling", "challenge",
]

# ── Timing keywords for why_now ──
_WHY_NOW_KEYWORDS = [
    "new", "recent", "launch", "announced", "trend", "growing",
    "accelerat", "shift", "change", "regulation", "policy",
    "funding", "raise", "investment", "competitor", "window",
    "now", "before", "early", "first mover",
]

# ── User segment patterns ──
_USER_SEGMENT_PATTERNS = [
    (r"(?i)\b(amazon.?seller|seller|small.?business.owner)\b", "ecommerce seller"),
    (r"(?i)\b(founder|entrepreneur|solo.?founder|indie.?hacker)\b", "founder / entrepreneur"),
    (r"(?i)\b(developer|engineer|programmer)\b", "developer"),
    (r"(?i)\b(cross.?border.?seller|export|import)\b", "cross-border seller"),
    (r"(?i)\b(freelancer|consultant|independent)\b", "freelancer / independent professional"),
    (r"(?i)\b(shopify.?merchant|shopify.?store)\b", "Shopify merchant"),
    (r"(?i)\b(content.?creator|creator|youtuber|streamer)\b", "content creator"),
    (r"(?i)\b(accountant|bookkeeper|cfo|finance.?manager)\b", "finance professional"),
]

# ── Engine hint mappings ──
_ENGINE_BY_PRODUCT_LINE = {
    "ai_seller_finance": ["cash_engine", "knowledge_asset"],
    "ai_company_os": ["os_evolution", "knowledge_asset"],
    "knowledge_assets": ["knowledge_asset", "cash_engine"],
    "ai_content_products": ["content_engine", "attention_engine"],
    "ai_short_drama": ["content_engine", "attention_engine"],
    "ai_game_products": ["content_engine", "platform_play"],
    "saas_microtools": ["cash_engine", "platform_play"],
    "platform_ecosystem_experiments": ["platform_play", "attention_engine"],
}

_ENGINE_KEYWORDS = [
    (r"(?i)\b(profit|revenue|revenue|sell|price|payment|subscription)\b", "cash_engine"),
    (r"(?i)\b(viral|share|social|attention|trending|demo)\b", "attention_engine"),
    (r"(?i)\b(plugin|extension|app.?store|shopify|roblox|platform|marketplace)\b", "platform_play"),
    (r"(?i)\b(content|video|drama|short|podcast|article)\b", "content_engine"),
    (r"(?i)\b(book|course|guide|methodology|template|kit|framework)\b", "knowledge_asset"),
    (r"(?i)\b(os|workflow|skill|agent|automation|governance)\b", "os_evolution"),
]

_PRODUCT_LINE_KEYWORDS = {
    "ai_seller_finance": ["seller", "finance", "p&l", "reconciliation", "amazon", "ecommerce",
                          "accounting", "bookkeeping", "invoice", "settlement"],
    "ai_company_os": ["agent os", "workflow", "governance", "operating system"],
    "knowledge_assets": ["book", "course", "template", "methodology", "kit", "guide"],
    "ai_content_products": ["content", "video", "article", "knowledge"],
    "ai_short_drama": ["short drama", "drama", "script", "episode"],
    "ai_game_products": ["game", "roblox", "gaming"],
    "saas_microtools": ["saas", "micro", "tool", "extension", "chrome"],
    "platform_ecosystem_experiments": ["platform", "ecosystem", "api", "integration"],
}

SIGNAL_TYPE_MAP = {
    "user_complaint": "pain",
    "ai_capability": "capability",
    "market_trend": "trend",
    "platform_shift": "platform",
    "asset_scan": "asset",
    "os_feedback": "system_gap",
}


# ════════════════════════════════════════════════════════════════════
# Extraction Functions
# ════════════════════════════════════════════════════════════════════

def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _keyword_match_count(text: str, keywords: list) -> int:
    if not text:
        return 0
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


def _generate_enriched_id(seq: int = 1) -> str:
    today = datetime.now(timezone.utc).strftime("%Y%m%d")
    return f"ES-{today}-{seq:03d}"


def extract_target_user(source_note: dict) -> dict:
    """Extract or infer target_user from SourceNote."""
    excerpt = source_note.get("excerpt", "") or ""
    title = source_note.get("title", "") or ""
    product_lines = source_note.get("product_line_refs", [])
    watchlist = source_note.get("watchlist_refs", [])
    combined = f"{title} {excerpt}"

    # 1. Check for explicit user segment in excerpt
    for pattern, segment in _USER_SEGMENT_PATTERNS:
        if re.search(pattern, combined):
            return {
                "value": segment,
                "evidence_status": "evidence_backed",
                "evidence": f"User segment '{segment}' matched in excerpt",
            }

    # 2. Infer from product_line_refs
    if product_lines:
        pl = product_lines[0]
        pl_map = {
            "ai_seller_finance": "ecommerce seller / cross-border seller",
            "ai_company_os": "founder / AI-native operator",
            "ai_content_products": "knowledge consumer",
            "ai_game_products": "gamer / Roblox player",
            "ai_short_drama": "short video consumer",
            "knowledge_assets": "aspiring founder / AI practitioner",
            "saas_microtools": "niche professional / power user",
            "platform_ecosystem_experiments": "platform user / developer",
        }
        inferred = pl_map.get(pl, "small business owner")
        return {
            "value": inferred,
            "evidence_status": "inferred",
            "evidence": f"Inferred from product_line_refs: {pl}",
        }

    # 3. Infer from watchlist
    if watchlist:
        return {
            "value": "target audience in watchlist domain",
            "evidence_status": "inferred",
            "evidence": f"Inferred from watchlist_refs: {', '.join(watchlist)}",
        }

    # 4. Nothing found
    return {
        "value": "",
        "evidence_status": "missing",
        "evidence": "No user segment pattern found in excerpt, title, or refs",
    }


def extract_pain(source_note: dict) -> dict:
    """Extract or infer pain from SourceNote."""
    excerpt = source_note.get("excerpt", "") or ""
    title = source_note.get("title", "") or ""
    source_category = source_note.get("source_category", "")
    combined = f"{title} {excerpt}"

    kw_count = _keyword_match_count(combined, _PAIN_KEYWORDS)

    # 1. Direct user complaint -> excerpt IS the pain
    if source_category == "user_complaint" and len(excerpt) > 30:
        return {
            "value": excerpt[:300],
            "evidence_status": "evidence_backed",
            "evidence": "SourceNote.source_category=user_complaint. Direct user quote in excerpt.",
        }

    # 2. Multiple pain keywords found
    if kw_count >= 2:
        return {
            "value": excerpt[:300],
            "evidence_status": "evidence_backed",
            "evidence": f"{kw_count} pain-related keywords found in title/excerpt",
        }

    # 3. One pain keyword
    if kw_count == 1:
        return {
            "value": excerpt[:200],
            "evidence_status": "inferred",
            "evidence": "1 pain keyword found. Pain not explicitly stated.",
        }

    # 4. No pain signal
    return {
        "value": "",
        "evidence_status": "missing",
        "evidence": "No pain-related keywords found in title or excerpt",
    }


def extract_why_now(source_note: dict) -> dict:
    """Extract or infer why_now from SourceNote."""
    excerpt = source_note.get("excerpt", "") or ""
    title = source_note.get("title", "") or ""
    combined = f"{title} {excerpt}"

    kw_count = _keyword_match_count(combined, _WHY_NOW_KEYWORDS)

    # 1. Explicit timing language
    if kw_count >= 3:
        return {
            "value": f"Timing signals detected: {kw_count} keywords. {excerpt[:200]}",
            "evidence_status": "evidence_backed",
            "evidence": f"{kw_count} timing keywords found in title/excerpt",
        }

    # 2. Some timing language
    if kw_count >= 1:
        return {
            "value": f"Weak timing signal ({kw_count} keywords): {excerpt[:100]}",
            "evidence_status": "inferred",
            "evidence": f"{kw_count} timing keywords found, but no strong urgency signal",
        }

    # 3. No timing signal
    return {
        "value": "",
        "evidence_status": "missing",
        "evidence": "No timing-related keywords found in title or excerpt",
    }


def extract_signal_type(source_note: dict) -> dict:
    """Extract signal_type from SourceNote source_category or keywords."""
    source_category = source_note.get("source_category", "")
    excerpt = source_note.get("excerpt", "") or ""
    title = source_note.get("title", "") or ""
    combined = f"{title} {excerpt}".lower()

    # 1. Direct mapping from source_category
    if source_category in SIGNAL_TYPE_MAP:
        return {
            "value": SIGNAL_TYPE_MAP[source_category],
            "evidence_status": "evidence_backed",
            "evidence": f"SourceNote.source_category = {source_category}",
        }

    # 2. Keyword fallback
    for keyword, stype in [
        ("pain", "pain"), ("frustrat", "pain"), ("complaint", "pain"),
        ("launch", "capability"), ("api", "capability"), ("model", "capability"),
        ("trend", "trend"), ("growing", "trend"), ("shift", "trend"), ("market", "trend"),
        ("platform", "platform"), ("ecosystem", "platform"), ("store", "platform"),
    ]:
        if keyword in combined:
            return {
                "value": stype,
                "evidence_status": "inferred",
                "evidence": f"Inferred from keyword '{keyword}' in title/excerpt",
            }

    return {
        "value": "",
        "evidence_status": "missing",
        "evidence": "Cannot determine signal type from source data",
    }


def infer_engine_hints(source_note: dict) -> tuple:
    """Infer engine hints from SourceNote data.

    Returns:
        (hints: list, status: str)
    """
    product_lines = source_note.get("product_line_refs", [])
    excerpt = source_note.get("excerpt", "") or ""
    title = source_note.get("title", "") or ""
    combined = f"{title} {excerpt}".lower()

    hints = set()

    # 1. From product_line_refs
    for pl in product_lines:
        if pl in _ENGINE_BY_PRODUCT_LINE:
            for engine in _ENGINE_BY_PRODUCT_LINE[pl]:
                hints.add(engine)

    # 2. From keyword matching
    for pattern, engine in _ENGINE_KEYWORDS:
        if re.search(pattern, combined):
            hints.add(engine)

    if hints:
        return (list(hints)[:3], "inferred")

    return (["cash_engine"], "inferred")


def infer_product_lines(source_note: dict) -> tuple:
    """Infer product line hints from SourceNote data.

    Returns:
        (hints: list, status: str)
    """
    explicit = source_note.get("product_line_refs", [])
    if explicit:
        return (explicit[:3], "evidence_backed")

    excerpt = source_note.get("excerpt", "") or ""
    title = source_note.get("title", "") or ""
    combined = f"{title} {excerpt}".lower()

    matched = []
    for pl_id, keywords in _PRODUCT_LINE_KEYWORDS.items():
        if any(kw in combined for kw in keywords):
            matched.append(pl_id)

    if matched:
        return (matched[:3], "inferred")

    return ([], "missing")


def assess_evidence_gaps(target_user: dict, pain: dict, why_now: dict) -> list:
    """Identify what evidence is still missing."""
    gaps = []
    if target_user.get("evidence_status") in ("missing",):
        gaps.append("No target user identified")
    elif target_user.get("evidence_status") == "inferred":
        gaps.append("Target user is inferred, not directly confirmed")

    if pain.get("evidence_status") in ("missing",):
        gaps.append("No pain point identified")
    elif pain.get("evidence_status") == "inferred":
        gaps.append("Pain point is inferred, not directly stated in source")

    if why_now.get("evidence_status") in ("missing",):
        gaps.append("No timing window identified")
    elif why_now.get("evidence_status") == "inferred":
        gaps.append("Timing window is inferred, not explicit")

    return gaps


def calculate_confidence(target_user: dict, pain: dict, why_now: dict) -> float:
    """Calculate overall confidence based on evidence status of critical fields."""
    status_scores = {"evidence_backed": 1.0, "inferred": 0.5, "missing": 0.0, "inferred_founder": 1.0}
    fields = [target_user, pain, why_now]
    scores = [status_scores.get(f.get("evidence_status", "missing"), 0.0) for f in fields]
    return sum(scores) / len(scores) if scores else 0.0


def enrich(source_note: dict, seq: int = 1) -> dict:
    """Enrich a single SourceNote into an Enriched Signal.

    Args:
        source_note: A valid SourceNote dict
        seq: Sequence number for ID generation

    Returns:
        An Enriched Signal dict conforming to enriched_signal.schema.json
    """
    # Extract fields
    target_user = extract_target_user(source_note)
    pain = extract_pain(source_note)
    why_now = extract_why_now(source_note)
    signal_type = extract_signal_type(source_note)
    engine_hints, engine_hints_status = infer_engine_hints(source_note)
    product_line_hints, product_line_hints_status = infer_product_lines(source_note)

    # Assess
    evidence_gaps = assess_evidence_gaps(target_user, pain, why_now)
    confidence = calculate_confidence(target_user, pain, why_now)
    requires_review = (
        target_user.get("evidence_status") == "missing"
        or pain.get("evidence_status") == "missing"
        or confidence < 0.6
    )

    # Determine next step
    if target_user.get("evidence_status") == "missing" and pain.get("evidence_status") == "missing":
        recommended_next_step = "dismiss"
    elif requires_review:
        recommended_next_step = "review_needed"
    elif confidence >= 0.7:
        recommended_next_step = "enrich_and_promote"
    else:
        recommended_next_step = "request_deep_research"

    enriched = {
        "enriched_signal_id": _generate_enriched_id(seq),
        "source_note_id": source_note.get("source_note_id", ""),
        "source_note_ref": source_note.get("url", source_note.get("source_ref", "")),
        "created_at": _now_iso(),
        "target_user": target_user,
        "pain": pain,
        "why_now": why_now,
        "signal_type": signal_type,
        "engine_hints": engine_hints,
        "engine_hints_status": engine_hints_status,
        "product_line_hints": product_line_hints,
        "product_line_hints_status": product_line_hints_status,
        "evidence_summary": f"SourceNote {source_note.get('source_note_id', '?')}: {source_note.get('excerpt', '')[:100]}...",
        "evidence_gaps": evidence_gaps,
        "confidence": round(confidence, 2),
        "requires_founder_review": requires_review,
        "recommended_next_step": recommended_next_step,
        "status": "enriched",
    }

    return enriched


# ════════════════════════════════════════════════════════════════════
# I/O
# ════════════════════════════════════════════════════════════════════

def read_source_note(filepath: str) -> Optional[dict]:
    """Read a SourceNote JSON file."""
    if not os.path.exists(filepath):
        print(f"  X File not found: {filepath}")
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"  X Error reading {filepath}: {e}")
        return None


def write_enriched_signal(signal: dict, output_dir: str = None):
    """Write an Enriched Signal to JSON file."""
    output_dir = output_dir or _DEFAULT_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    es_id = signal.get("enriched_signal_id", "ES-UNKNOWN")
    filepath = os.path.join(output_dir, f"{es_id}.json")

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(signal, f, ensure_ascii=False, indent=2)
        return filepath
    except Exception as e:
        print(f"  X Error writing {filepath}: {e}")
        return None


def find_source_notes(source_dir: str = None) -> list:
    """Find all SourceNote JSON files in a directory."""
    source_dir = source_dir or _SOURCE_DIR
    if not os.path.isdir(source_dir):
        return []

    notes = []
    for root, _, files in os.walk(source_dir):
        for fname in files:
            if fname.startswith("SN-") and fname.endswith(".json"):
                notes.append(os.path.join(root, fname))
    return sorted(notes)


def list_review_needed(output_dir: str = None) -> list:
    """List all Enriched Signals that need founder review."""
    output_dir = output_dir or _DEFAULT_OUTPUT_DIR
    if not os.path.isdir(output_dir):
        return []

    needs_review = []
    for fname in sorted(os.listdir(output_dir)):
        if not fname.startswith("ES-") or not fname.endswith(".json"):
            continue
        fpath = os.path.join(output_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                signal = json.load(f)
            if signal.get("requires_founder_review") or signal.get("recommended_next_step") == "review_needed":
                needs_review.append(signal)
        except Exception:
            pass
    return needs_review


def find_enriched_by_id(enriched_id: str, output_dir: str = None) -> Optional[dict]:
    """Find an enriched signal by ID in the output directory."""
    output_dir = output_dir or _DEFAULT_OUTPUT_DIR
    fpath = os.path.join(output_dir, f"{enriched_id}.json")
    if not os.path.exists(fpath):
        return None
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def write_enriched_signal_update(signal: dict, output_dir: str = None) -> Optional[str]:
    """Write an updated enriched signal back to disk."""
    output_dir = output_dir or _DEFAULT_OUTPUT_DIR
    es_id = signal.get("enriched_signal_id", "ES-UNKNOWN")
    fpath = os.path.join(output_dir, f"{es_id}.json")
    try:
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(signal, f, ensure_ascii=False, indent=2)
        return fpath
    except Exception as e:
        print(f"  X Error writing update: {e}")
        return None


# ════════════════════════════════════════════════════════════════════
# Review Generation (Sprint C — Founder Review Patch)
# ════════════════════════════════════════════════════════════════════

_REVIEW_DIR_SUFFIX = "reviews"

_STATUS_EMOJI = {
    "evidence_backed": ":white_check_mark:",
    "inferred": ":mag:",
    "missing": ":x:",
    "inferred_founder": ":bust_in_silhouette:",
}


def _field_summary(field: dict, field_name: str) -> str:
    """Generate a markdown summary block for a single analytical field."""
    value = field.get("value", "") or "(empty)"
    status = field.get("evidence_status", "missing")
    evidence = field.get("evidence", "(none)")
    emoji = _STATUS_EMOJI.get(status, ":grey_question:")

    lines = [
        f"### {field_name.capitalize().replace('_', ' ')}",
        "",
        f"**Current Value:** {value}",
        f"**Evidence Status:** {emoji} `{status}`",
        f"**Enricher's Note:** {evidence}",
        "",
        "#### Founder Decision",
        "",
    ]

    if status == "missing":
        lines += [
            "- [ ] **Fill in**: [FOUNDER_INPUT: Provide the missing value]",
            "- [ ] **Dismiss**: This signal has no clear insight -> dismiss",
            "",
            "If filled, evidence status becomes: `inferred_founder`",
        ]
    elif status == "inferred":
        lines += [
            "- [ ] **Approve as-is**: The inferred value looks correct",
            "- [ ] **Replace**: [FOUNDER_INPUT: Provide corrected value]",
            "- [ ] **Dismiss**: Signal not useful -> dismiss",
            "",
            "If approved, evidence status stays: `inferred` (with Founder validation).",
        ]
    else:
        lines += [
            "- [ ] **Confirmed**: The evidence-backed value is correct",
            "- [ ] **Replace**: [FOUNDER_INPUT: Provide corrected value]",
            "",
            "If confirmed, evidence status stays: `evidence_backed`.",
        ]

    return "\n".join(lines)


def generate_review_markdown(signal: dict) -> str:
    """Generate the full review markdown for an enriched signal."""
    sid = signal.get("enriched_signal_id", "?")
    sn_id = signal.get("source_note_id", "?")
    url = signal.get("source_note_ref", "(no URL)")
    status = signal.get("status", "enriched")
    next_step = signal.get("recommended_next_step", "?")
    confidence = signal.get("confidence", 0.0)
    created = signal.get("created_at", "?")
    gaps = signal.get("evidence_gaps", [])
    summary = signal.get("evidence_summary", "")

    gap_bullets = "\n".join(f"- {g}" for g in gaps) if gaps else "- (none noted)"

    lines = [
        f"# Enrichment Review: {sid}",
        "",
        "---",
        "",
        "## A. Summary",
        "",
        "| Field | Value |",
        "|:------|:------|",
        f"| Source Note | `{sn_id}` |",
        f"| Source URL | {url} |",
        f"| Current Status | `{status}` |",
        f"| Recommended Action | `{next_step}` |",
        f"| Overall Confidence | {confidence:.2f} / 1.0 |",
        f"| Generated | {created} |",
        "| Evidence Gaps | |",
        f"{gap_bullets}",
        "",
        f"**Summary:** {summary}",
        "",
        "---",
        "",
        "## B. Field-by-Field Review",
        "",
        _field_summary(signal.get("target_user", {}), "target_user"),
        "",
        "---",
        "",
        _field_summary(signal.get("pain", {}), "pain"),
        "",
        "---",
        "",
        _field_summary(signal.get("why_now", {}), "why_now"),
        "",
        "---",
        "",
        "## C. Overall Decision",
        "",
        "Choose one:",
        "",
        "- [ ] **Promote to Evidence Gate** - All critical fields filled or confirmed",
        "- [ ] **Request deep research** - Signal is promising but needs more data",
        "- [ ] **Dismiss** - Not relevant to current product direction",
        "",
        "---",
        "",
        "## D. Founder Notes",
        "",
        "[FOUNDER_NOTE: Optional reasoning, observations, or context]",
        "",
        "---",
        "",
        "## E. Review Metadata",
        "",
        "| Field | Value |",
        "|:------|:------|",
        "| Reviewed By | [FOUNDER_INPUT: Your name or initials] |",
        "| Review Date | *(auto-filled on apply)* |",
        "",
    ]

    return "\n".join(lines)


def _parse_review_decision(review_text: str) -> dict:
    """Parse a filled review .md file back into structured data.

    Returns:
        dict with keys: founder_fields (dict), decision (str), notes (str), reviewer (str)
    """
    result = {
        "founder_fields": {},
        "decision": None,
        "notes": "",
        "reviewer": "",
    }

    # Parse decision section
    for label, value in [
        ("Promote to Evidence Gate", "promote"),
        ("Request deep research", "request_deep_research"),
        ("Dismiss", "dismiss"),
    ]:
        if re.search(
            rf"- \[x\] .*{re.escape(label)}",
            review_text,
            re.IGNORECASE,
        ):
            result["decision"] = value
            break

    # Parse Founder notes
    note_match = re.search(
        r"\[FOUNDER_NOTE:\s*(.*?)\]", review_text, re.IGNORECASE | re.DOTALL
    )
    if note_match:
        result["notes"] = note_match.group(1).strip()

    # Parse reviewer name
    reviewer_match = re.search(
        r"Reviewed By\s*\|\s*\[FOUNDER_INPUT:\s*(.*?)\]",
        review_text,
        re.IGNORECASE,
    )
    if reviewer_match:
        result["reviewer"] = reviewer_match.group(1).strip()

    # Parse field decisions
    for field_key, field_label in [("target_user", "Target User"), ("pain", "Pain"), ("why_now", "Why Now")]:
        section_match = re.search(
            rf"### {re.escape(field_label)}.*?(?=\n### |\n## C\.|\n# |$)",
            review_text,
            re.IGNORECASE | re.DOTALL,
        )
        if not section_match:
            continue

        section = section_match.group(0)

        is_checked = bool(re.search(r"- \[x\]", section, re.IGNORECASE))
        dismissed_field = bool(re.search(r"- \[x\].*Dismiss", section, re.IGNORECASE))

        if not is_checked:
            continue

        if dismissed_field:
            result["founder_fields"][field_key] = {
                "action": "dismiss_field",
                "value": None,
            }
            continue

        # Extract the value from the checked checkbox line
        # Format: - [x] **Fill in**: <value> or - [x] **Replace**: <value>
        value_match = re.search(
            r"- \[x\] \*\*(?:Fill in|Replace|Confirmed)\*\*:\s*(.*?)(?:\n|$)",
            section,
            re.IGNORECASE,
        )
        if value_match:
            replacement = value_match.group(1).strip()
            if replacement and replacement not in (
                "Provide corrected value",
                "Provide the missing value",
            ):
                result["founder_fields"][field_key] = {
                    "action": "replace",
                    "value": replacement,
                }
            else:
                # Checked but no real value filled in - treat as approve
                result["founder_fields"][field_key] = {
                    "action": "approve",
                    "value": None,
                }
        else:
            # Checked but no value extraction - could be "Approve as-is" or "Confirmed"
            result["founder_fields"][field_key] = {
                "action": "approve",
                "value": None,
            }

    return result


# ════════════════════════════════════════════════════════════════════
# CLI Commands
# ════════════════════════════════════════════════════════════════════

def cmd_enrich(args):
    """Enrich a single SourceNote file."""
    filepath = args.source_note
    note = read_source_note(filepath)
    if not note:
        return

    print(f"  Enriching: {os.path.basename(filepath)}")
    seq = args.seq or 1
    signal = enrich(note, seq)

    if args.dry_run:
        _print_summary(signal)
        return

    fp = write_enriched_signal(signal, args.output_dir)
    if fp:
        print(f"  Enriched signal: {fp}")
        _print_summary(signal)


def cmd_enrich_batch(args):
    """Enrich all SourceNotes in a directory."""
    source_dir = args.dir or _SOURCE_DIR
    notes = find_source_notes(source_dir)

    if not notes:
        print(f"  No SourceNotes found in {source_dir}")
        print(f"     Run a connector first to generate SourceNotes")
        return

    print(f"  Found {len(notes)} SourceNotes in {source_dir}")

    enriched_count = 0
    for i, fpath in enumerate(notes):
        note = read_source_note(fpath)
        if not note:
            continue
        seq = i + 1
        signal = enrich(note, seq)

        if not args.dry_run:
            fp = write_enriched_signal(signal, args.output_dir)
            if fp:
                enriched_count += 1

        status_icon = ":white_check_mark:" if signal["recommended_next_step"] == "enrich_and_promote" else (
            ":warning:" if signal["recommended_next_step"] == "review_needed" else ":x:"
        )
        title = signal.get("target_user", {}).get("value", "?")[:40]
        print(f"  {status_icon} [{seq}/{len(notes)}] {signal['enriched_signal_id']} | "
              f"Conf: {signal['confidence']:.2f} | "
              f"User: {title} | "
              f"Next: {signal['recommended_next_step']}")

    print(f"\n  Enriched: {enriched_count}/{len(notes)} signals "
          f"(rest failed or skipped)")


def cmd_review_needed(args):
    """List Enriched Signals that need founder review."""
    output_dir = args.output_dir
    signals = list_review_needed(output_dir)

    if not signals:
        print(f"  No enriched signals need review")
        return

    print(f"\n  {len(signals)} enriched signal(s) need founder review:")
    print()
    for s in signals:
        es_id = s.get("enriched_signal_id", "?")
        sn_id = s.get("source_note_id", "?")
        conf = s.get("confidence", 0)
        gaps = ", ".join(s.get("evidence_gaps", [])) or "none"
        print(f"  [{es_id}] from {sn_id}")
        print(f"     Confidence: {conf:.2f} | Gaps: {gaps}")
        print(f"     Target: {s.get('target_user', {}).get('value', '?')[:60]}")
        print(f"     Pain:   {s.get('pain', {}).get('value', '?')[:60]}")
        print()

    print(f"  Total: {len(signals)} signals need review")


def cmd_generate_review(args):
    """Generate a review .md file for an enriched signal."""
    signal = find_enriched_by_id(args.id, args.output_dir)
    if not signal:
        print(f"  Enriched signal not found: {args.id}")
        return

    review_text = generate_review_markdown(signal)
    review_dir = os.path.join(args.output_dir or _DEFAULT_OUTPUT_DIR, _REVIEW_DIR_SUFFIX)
    os.makedirs(review_dir, exist_ok=True)
    review_path = os.path.join(review_dir, f"{args.id}_REVIEW.md")

    with open(review_path, "w", encoding="utf-8") as f:
        f.write(review_text)

    next_step = signal.get("recommended_next_step", "?")
    print(f"  Review template: {review_path}")
    print(f"     Signal: {args.id} (next step: {next_step})")
    print(f"     Edit the file, fill [FOUNDER_INPUT] blocks, then run:")
    print(f"        python3 scripts/opportunity_enricher.py apply-review --id {args.id}")


def cmd_apply_review(args):
    """Apply a filled review .md file, updating the enriched signal."""
    signal = find_enriched_by_id(args.id, args.output_dir)
    if not signal:
        print(f"  Enriched signal not found: {args.id}")
        return

    output_dir = args.output_dir or _DEFAULT_OUTPUT_DIR
    review_dir = os.path.join(output_dir, _REVIEW_DIR_SUFFIX)
    review_path = os.path.join(review_dir, f"{args.id}_REVIEW.md")

    if not os.path.exists(review_path):
        print(f"  Review file not found: {review_path}")
        print(f"     Run 'generate-review --id {args.id}' first")
        return

    with open(review_path, "r", encoding="utf-8") as f:
        review_text = f.read()

    parsed = _parse_review_decision(review_text)

    # Apply field changes
    changes_made = 0
    for field_key in ["target_user", "pain", "why_now"]:
        if field_key not in parsed["founder_fields"]:
            continue
        action = parsed["founder_fields"][field_key]["action"]
        value = parsed["founder_fields"][field_key]["value"]

        if action == "approve":
            changes_made += 1
        elif action == "replace" and value:
            signal[field_key] = {
                "value": value,
                "evidence_status": "inferred_founder",
                "evidence": f"Founder review: {parsed.get('reviewer', 'founder')} provided value",
            }
            changes_made += 1
            # Remove related gap
            gap_map = {
                "target_user": "Target user",
                "pain": "No pain",
                "why_now": "No timing",
            }
            g = gap_map.get(field_key, "")
            signal["evidence_gaps"] = [
                gap for gap in signal.get("evidence_gaps", [])
                if g.lower() not in gap.lower()
            ]
        elif action == "dismiss_field" and signal[field_key].get("evidence_status") == "missing":
            changes_made += 1

    # Apply decision
    decision = parsed.get("decision") or args.default_decision
    if not decision:
        print(f"  No decision found in review file")
        print(f"     Section C must have a checked [x] option")
        print(f"     Or use: --default promote|dismiss|request_deep_research")
        return

    if decision == "dismiss":
        signal["status"] = "dismissed"
        signal["recommended_next_step"] = "dismiss"
    elif decision == "request_deep_research":
        signal["status"] = "enriched"
        signal["recommended_next_step"] = "request_deep_research"
    else:
        # promote
        signal["status"] = "reviewed"
        signal["recommended_next_step"] = "enrich_and_promote"
        signal["requires_founder_review"] = False

        new_conf = calculate_confidence(
            signal.get("target_user", {}),
            signal.get("pain", {}),
            signal.get("why_now", {}),
        )
        signal["confidence"] = round(new_conf, 2)

    # Append founder notes
    founder_notes = signal.setdefault("founder_notes", [])
    note_entry = {
        "timestamp": _now_iso(),
        "action": decision,
        "note": parsed.get("notes", f"Review: {decision}. Fields updated: {changes_made}."),
    }
    if parsed.get("reviewer"):
        note_entry["reviewer"] = parsed["reviewer"]
    founder_notes.append(note_entry)

    # Write
    fp = write_enriched_signal_update(signal, args.output_dir)
    if fp:
        print(f"  Updated: {fp}")
        print(f"     Status: {signal['status']} | Next: {signal['recommended_next_step']}")
        print(f"     Confidence: {signal.get('confidence', 0):.2f}")


def cmd_dismiss(args):
    """Dismiss an enriched signal immediately (skip review)."""
    signal = find_enriched_by_id(args.id, args.output_dir)
    if not signal:
        print(f"  Enriched signal not found: {args.id}")
        return

    signal["status"] = "dismissed"
    signal["recommended_next_step"] = "dismiss"

    founder_notes = signal.setdefault("founder_notes", [])
    founder_notes.append({
        "timestamp": _now_iso(),
        "action": "dismiss",
        "note": args.reason or "Dismissed by Founder (cli).",
    })

    fp = write_enriched_signal_update(signal, args.output_dir)
    if fp:
        print(f"  Dismissed: {args.id}")


def cmd_request_research(args):
    """Mark an enriched signal for deep research (skip review)."""
    signal = find_enriched_by_id(args.id, args.output_dir)
    if not signal:
        print(f"  Enriched signal not found: {args.id}")
        return

    signal["status"] = "enriched"
    signal["recommended_next_step"] = "request_deep_research"

    founder_notes = signal.setdefault("founder_notes", [])
    founder_notes.append({
        "timestamp": _now_iso(),
        "action": "request_deep_research",
        "note": args.reason or "Requested deep research (cli).",
    })

    fp = write_enriched_signal_update(signal, args.output_dir)
    if fp:
        print(f"  Requested deep research: {args.id}")


def _print_summary(signal: dict):
    """Print a brief summary of an Enriched Signal."""
    es_id = signal.get("enriched_signal_id", "?")
    conf = signal.get("confidence", 0)
    target = signal.get("target_user", {}).get("value", "?")[:60]
    target_status = signal.get("target_user", {}).get("evidence_status", "?")
    pain = signal.get("pain", {}).get("value", "?")[:60]
    pain_status = signal.get("pain", {}).get("evidence_status", "?")
    why_now_status = signal.get("why_now", {}).get("evidence_status", "?")
    next_step = signal.get("recommended_next_step", "?")
    review = signal.get("requires_founder_review", False)

    print(f"     Target User:  [{target_status.upper()}] {target}")
    print(f"     Pain:         [{pain_status.upper()}] {pain}")
    print(f"     Why Now:      [{why_now_status.upper()}]")
    print(f"     Confidence:   {conf:.2f} | Review: {'YES' if review else 'No'} | Next: {next_step}")


# ════════════════════════════════════════════════════════════════════
# CLI
# ════════════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="v0.34 - Opportunity Enricher P0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python3 scripts/opportunity_enricher.py enrich --source-note research/opportunity-source-notes/search_query/SN-xxx.json
  python3 scripts/opportunity_enricher.py enrich-batch --dir research/opportunity-source-notes/search_query/
  python3 scripts/opportunity_enricher.py enrich-batch --dir research/opportunity-source-notes/search_query/ --dry-run
  python3 scripts/opportunity_enricher.py review-needed
  python3 scripts/opportunity_enricher.py generate-review --id ES-20260531-001
  python3 scripts/opportunity_enricher.py apply-review --id ES-20260531-001
  python3 scripts/opportunity_enricher.py dismiss --id ES-20260531-001 --reason "Not relevant"
        """,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # --- enrich (single file) ---
    enrich_p = sub.add_parser("enrich", help="Enrich a single SourceNote file")
    enrich_p.add_argument("--source-note", "-f", required=True,
                          help="Path to SourceNote JSON file")
    enrich_p.add_argument("--output-dir", "-o", default=None,
                          help="Override output directory")
    enrich_p.add_argument("--seq", type=int, default=None,
                          help="Sequence number for ID generation")
    enrich_p.add_argument("--dry-run", "-n", action="store_true",
                          help="Preview without writing")

    # --- enrich-batch ---
    batch_p = sub.add_parser("enrich-batch", help="Enrich all SourceNotes in a directory")
    batch_p.add_argument("--dir", "-d", default=None,
                         help="Directory containing SourceNote JSON files")
    batch_p.add_argument("--output-dir", "-o", default=None,
                         help="Override output directory")
    batch_p.add_argument("--dry-run", "-n", action="store_true",
                         help="Preview without writing")

    # --- review-needed ---
    review_p = sub.add_parser("review-needed", help="List Enriched Signals needing founder review")
    review_p.add_argument("--output-dir", "-o", default=None,
                          help="Override output directory")

    # --- generate-review ---
    gen_p = sub.add_parser("generate-review", help="Generate review .md for an enriched signal")
    gen_p.add_argument("--id", required=True, help="Enriched signal ID (e.g. ES-20260531-001)")
    gen_p.add_argument("--output-dir", "-o", default=None,
                       help="Override output directory")

    # --- apply-review ---
    apply_p = sub.add_parser("apply-review", help="Apply a filled review .md to update enriched signal")
    apply_p.add_argument("--id", required=True, help="Enriched signal ID")
    apply_p.add_argument("--output-dir", "-o", default=None,
                         help="Override output directory")
    apply_p.add_argument("--default", dest="default_decision", default=None,
                         choices=["promote", "dismiss", "request_deep_research"],
                         help="Default decision if none found in review file")

    # --- dismiss ---
    dismiss_p = sub.add_parser("dismiss", help="Dismiss an enriched signal (skip review)")
    dismiss_p.add_argument("--id", required=True, help="Enriched signal ID")
    dismiss_p.add_argument("--reason", default=None, help="Dismissal reason")
    dismiss_p.add_argument("--output-dir", "-o", default=None,
                           help="Override output directory")

    # --- request-research ---
    research_p = sub.add_parser("request-research", help="Request deep research for a signal")
    research_p.add_argument("--id", required=True, help="Enriched signal ID")
    research_p.add_argument("--reason", default=None, help="Why more research is needed")
    research_p.add_argument("--output-dir", "-o", default=None,
                            help="Override output directory")

    args = parser.parse_args()

    if args.command == "enrich":
        cmd_enrich(args)
    elif args.command == "enrich-batch":
        cmd_enrich_batch(args)
    elif args.command == "review-needed":
        cmd_review_needed(args)
    elif args.command == "generate-review":
        cmd_generate_review(args)
    elif args.command == "apply-review":
        cmd_apply_review(args)
    elif args.command == "dismiss":
        cmd_dismiss(args)
    elif args.command == "request-research":
        cmd_request_research(args)


if __name__ == "__main__":
    main()
