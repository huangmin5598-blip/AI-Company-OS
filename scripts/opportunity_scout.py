#!/usr/bin/env python3
"""
v0.32 — Opportunity Scout Runner P0

AI Company OS 机会发现层核心引擎。
Three-layer architecture — Layer 3 (public framework code).

Input Entry Points:
  scan --source-file <file>    Generate candidates from manual source notes
  scan-assets                  Scan docs/ directory for reusable asset signals
  scan-os-feedback             Scan reports/ + docs/ OS runtime feedback signals
  scan-enriched                Scan reviewed Enriched Signals -> candidates

Rule Chain:
  Load Rules → Evidence Gate → Signal Classification → Scoring (10 Dims)
  → Product Line Mapping → Engine Classification → Candidate Output

Output: JSON candidates -> research/opportunity-candidates/

Usage:
  python3 scripts/opportunity_scout.py scan --source-file config/examples/manual-source-note.example.yaml
  python3 scripts/opportunity_scout.py scan-assets
  python3 scripts/opportunity_scout.py scan-os-feedback
  python3 scripts/opportunity_scout.py list-candidates
  python3 scripts/opportunity_scout.py show-candidate CD-20260531-001

NOT in scope (Sprint A/B): RSS/GitHub/ProductHunt/Reddit connectors, Web UI,
  cron/launchd scheduling, auto-generate card, auto-approve.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from typing import Optional

# ── PyYAML (required for source note parsing) ──
try:
    import yaml
except ImportError:
    print("❌ PyYAML required. Install: pip install pyyaml", file=sys.stderr)
    sys.exit(1)


# ════════════════════════════════════════════════════════════════════
# Constants & Enums
# ════════════════════════════════════════════════════════════════════

SOURCE_TYPES = [
    "user_complaint", "ai_capability", "market_trend",
    "platform_shift", "asset_scan", "os_feedback",
]

SIGNAL_TYPES = ["pain", "capability", "trend", "platform", "asset", "system_gap"]

ENGINE_TYPES = [
    "cash_engine", "attention_engine", "platform_play",
    "content_engine", "knowledge_asset", "os_evolution",
]

CANDIDATE_TYPES = ["venture_opportunity", "os_improvement"]

RECOMMENDED_ROUTES = [
    "promote_signal", "request_card", "request_deep_research",
    "park", "dismiss", "create_os_improvement_task",
]

EVIDENCE_GATE_STATUSES = ["passed", "needs_more_evidence", "weak_candidate"]

STATUSES = ["candidate", "promoted", "dismissed", "needs_more_evidence"]

PRODUCT_LINES = [
    "ai_company_os", "ai_seller_finance", "ai_content_products",
    "ai_game_products", "ai_short_drama", "knowledge_assets",
    "saas_microtools", "platform_ecosystem_experiments",
]

# Source type -> signal_type mapping
SOURCE_TYPE_TO_SIGNAL = {
    "user_complaint": "pain",
    "ai_capability": "capability",
    "market_trend": "trend",
    "platform_shift": "platform",
    "asset_scan": "asset",
    "os_feedback": "system_gap",
}

# Scoring dimension labels
SCORING_DIMENSIONS = [
    "pain_score",
    "evidence_score",
    "why_now_score",
    "founder_fit_score",
    "asset_leverage_score",
    "mvp_speed_score",
    "distribution_score",
    "monetization_score",
    "attention_score",
    "os_compounding_score",
]

# Pain keywords (lowercase) for heuristic scoring
PAIN_KEYWORDS = [
    "spend hours", "manual", "frustrat", "pain", "headache",
    "waste", "expensive", "hard", "difficult", "no good solution",
    "too much time", "tedious", "annoying", "broken", "sucks",
]

# Timing / urgency keywords for why_now scoring
WHY_NOW_KEYWORDS = [
    "new", "recent", "launch", "announced", "trend", "growing",
    "accelerat", "shift", "change", "regulation", "policy",
    "funding", "raise", "investment", "competitor", "window",
    "now", "before", "early", "first mover",
]

# Distribution channel keywords
DISTRIBUTION_KEYWORDS = [
    "wechat", "xiaohongshu", "red book", "tiktok", "douyin",
    "youtube", "github", "zhihu", "product hunt", "chrome",
    "roblox", "shopify", "amazon", "app store", "community",
    "group", "forum", "email", "blog", "newsletter",
]

# Monetization keywords
MONETIZATION_KEYWORDS = [
    "pay", "price", "subscription", "premium", "charge",
    "monetize", "revenue", "sell", "pricing", "saas",
    "fee", "cost", "afford",
]

# Attention / virality keywords
ATTENTION_KEYWORDS = [
    "viral", "demo", "showcase", "share", "trend",
    "popular", "hype", "attention", "social", "media",
    "wow", "impressive", "cool", "interesting",
]

# Assets that can be reused — mapped to product lines
ASSET_KEYWORDS_MAP = {
    "ai_seller_finance": [
        "seller", "finance", "p&l", "reconciliation", "amazon",
        "cross-border", "ecommerce", "csv", "reporting",
    ],
    "ai_company_os": [
        "os", "workflow", "governance", "policy", "agent",
        "run ledger", "asset", "skill", "capability",
    ],
    "knowledge_assets": [
        "book", "course", "methodology", "kit", "guide",
        "framework", "template", "os kit",
    ],
    "ai_content_products": [
        "content", "article", "video", "podcast", "knowledge",
        "entertainment", "education",
    ],
    "ai_short_drama": [
        "short drama", "drama", "episode", "script", "video gen",
    ],
    "ai_game_products": [
        "game", "roblox", "play", "gaming", "prototype",
    ],
    "saas_microtools": [
        "saas", "micro", "tool", "extension", "chrome",
        "standalone", "cli",
    ],
    "platform_ecosystem_experiments": [
        "platform", "ecosystem", "api", "integration",
        "shopify", "notion", "feishu",
    ],
}

# Founder expertise domains (from Company Context defaults)
FOUNDER_EXPERTISE_DOMAINS = [
    "finance", "accounting", "cross-border", "ecommerce",
    "ai agent", "agent os", "operating system",
    "knowledge management", "methodology",
]

# Paths
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
_DEFAULT_OUTPUT_DIR = os.path.join(_PROJECT_ROOT, "research", "opportunity-candidates")
_DOCS_DIR = os.path.join(_PROJECT_ROOT, "docs")
_REPORTS_DIR = os.path.join(_PROJECT_ROOT, "reports")
_ENRICHED_DIR = os.path.join(_PROJECT_ROOT, "research", "opportunity-enriched")
_SOURCE_NOTES_DIR = os.path.join(_PROJECT_ROOT, "research", "opportunity-source-notes")


# ════════════════════════════════════════════════════════════════════
# Utility Functions
# ════════════════════════════════════════════════════════════════════

def _now_iso() -> str:
    """Return current UTC time in ISO 8601."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today_compact() -> str:
    """Return YYYYMMDD for candidate ID generation."""
    return datetime.now(timezone.utc).strftime("%Y%m%d")


_BATCH_SEQ_COUNTER = 0

def _generate_candidate_id(output_dir: str = None) -> str:
    global _BATCH_SEQ_COUNTER
    _BATCH_SEQ_COUNTER += 1
    return _generate_candidate_id_internal(output_dir, _BATCH_SEQ_COUNTER)


def _generate_candidate_id_internal(output_dir: str = None, seq: int = 0) -> str:
    """Generate a candidate ID in format CD-YYYYMMDD-NNN."""
    output_dir = output_dir or _DEFAULT_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)

    today = _today_compact()
    prefix = f"CD-{today}-"

    # If seq is provided, use it directly (batch mode)
    if seq > 0:
        return f"{prefix}{seq:03d}"

    # Otherwise, scan existing files for max sequence
    max_seq = 0
    try:
        for fname in os.listdir(output_dir):
            if fname.startswith(prefix) and fname.endswith(".json"):
                seq_str = fname[len(prefix):-5]
                try:
                    s = int(seq_str)
                    max_seq = max(max_seq, s)
                except ValueError:
                    pass
    except FileNotFoundError:
        pass

    return f"{prefix}{max_seq + 1:03d}"


def _load_yaml(filepath: str) -> dict:
    """Load a YAML file safely. Returns {} on failure."""
    if not os.path.exists(filepath):
        print(f"  ❌ File not found: {filepath}", file=sys.stderr)
        return {}
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        if data is None:
            data = {}
        return data
    except Exception as e:
        print(f"  ❌ Error loading {filepath}: {e}", file=sys.stderr)
        return {}


def _load_text(filepath: str) -> str:
    """Load a text file. Returns '' on failure."""
    if not os.path.exists(filepath):
        return ""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def _ensure_output_dir(output_dir: str = None) -> str:
    """Ensure output directory exists and return its path."""
    output_dir = output_dir or _DEFAULT_OUTPUT_DIR
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def _extract_text_between(content: str, start_marker: str, end_marker: str = None) -> str:
    """Extract text between markers from markdown content."""
    idx = content.find(start_marker)
    if idx == -1:
        return ""
    start = idx + len(start_marker)
    if end_marker:
        end = content.find(end_marker, start)
        if end == -1:
            return content[start:].strip()
        return content[start:end].strip()
    return content[start:].strip()


def _keyword_match_count(text: str, keywords: list) -> int:
    """Count how many keywords appear in the given text (case-insensitive)."""
    if not text:
        return 0
    text_lower = text.lower()
    return sum(1 for kw in keywords if kw in text_lower)


def _keyword_match_any(text: str, keywords: list) -> bool:
    """Check if any keyword appears in the given text."""
    return _keyword_match_count(text, keywords) > 0


# ════════════════════════════════════════════════════════════════════
# Evidence Gate
# ════════════════════════════════════════════════════════════════════

def validate_evidence_gate(data: dict) -> dict:
    """Apply evidence gate rules to determine if a candidate can be generated.

    Returns:
        dict with keys:
            passed (bool): Can the signal proceed?
            gate_status (str): 'passed', 'needs_more_evidence', 'weak_candidate'
            failures (list): Description of each gate failure
    """
    failures = []
    source_ref = data.get("source_ref", data.get("url", ""))
    excerpt = data.get("excerpt", "")
    target_user = data.get("target_user", "")
    pain = data.get("pain", "")
    why_now = data.get("why_now", "")
    source_type = data.get("source_type", "")
    source_category = data.get("source_category", "")

    # Gate 1: source_ref
    if not source_ref and not excerpt:
        failures.append("GATE_FAILURE: No source_ref or excerpt — cannot generate candidate")
    elif not source_ref and excerpt:
        # Has excerpt but no URL — treat as weak source but not fatal
        pass  # Allow with excerpt only

    # Gate 2: target_user
    if not target_user:
        failures.append("GATE_FAILURE: No target_user — cannot generate candidate")

    # Gate 3: pain_description grounded in source evidence
    if not pain:
        # For non-pain signal types, this is optional
        signal_type = data.get("signal_type", SOURCE_TYPE_TO_SIGNAL.get(source_type, ""))
        if signal_type in ("pain", ""):
            failures.append("GATE_FAILURE: No pain description — cannot generate candidate")
        # capability/trend/platform signals don't require pain

    # Gate 4: why_now (timing window)
    if not why_now:
        failures.append("GATE_WEAK: No why_now — outputs needs_more_evidence")

    # Gate 5: C-tier generic news without complaint/asset backing
    is_generic_news = source_category in ("market_trend", "platform_shift") and not pain and not target_user
    if is_generic_news:
        failures.append("GATE_WEAK: C-tier news without user complaint or asset backing — weak_candidate only")

    # Determine result
    fatal_failures = [f for f in failures if f.startswith("GATE_FAILURE")]
    weak_failures = [f for f in failures if f.startswith("GATE_WEAK")]

    if fatal_failures:
        return {
            "passed": False,
            "gate_status": "weak_candidate" if not fatal_failures else "needs_more_evidence",
            "failures": fatal_failures,
            "can_generate": False,
        }

    if weak_failures:
        return {
            "passed": True,
            "gate_status": "weak_candidate" if any("C-tier" in f for f in weak_failures) else "needs_more_evidence",
            "failures": weak_failures,
            "can_generate": True,
        }

    return {
        "passed": True,
        "gate_status": "passed",
        "failures": [],
        "can_generate": True,
    }


# ════════════════════════════════════════════════════════════════════
# Scoring Engine — 10 Dimensions (1-5 each)
# ════════════════════════════════════════════════════════════════════

def _score_pain(data: dict) -> int:
    """Score pain intensity 1-5. Higher = stronger user pain."""
    excerpt = data.get("excerpt", "") or ""
    founder_note = data.get("founder_note", "") or ""
    source_type = data.get("source_type", "")

    combined = f"{excerpt} {founder_note}"
    kw_count = _keyword_match_count(combined, PAIN_KEYWORDS)
    excerpt_len = len(excerpt)

    if source_type == "user_complaint":
        base = 3
    elif source_type == "os_feedback":
        base = 2
    else:
        base = 1

    # Bonus: multiple pain keywords
    bonus = min(kw_count, 2)  # cap at +2

    # Bonus: substantial excerpt with specific complaint
    if excerpt_len > 150:
        bonus += 1

    return min(base + bonus, 5)


def _score_evidence(data: dict) -> int:
    """Score evidence strength 1-5."""
    excerpt = data.get("excerpt", "") or ""
    founder_note = data.get("founder_note", "") or ""
    source_refs = data.get("source_refs", data.get("url", ""))
    source_type = data.get("source_type", "")

    score = 1

    # Has content
    if len(excerpt) > 50:
        score += 1
    if len(excerpt) > 200:
        score += 1

    # Has source URL / refs
    if source_refs:
        score += 1

    # Detailed founder note
    if len(founder_note) > 100:
        score += 1

    # Specific details (numbers, dates, names)
    if re.search(r'\d+', combined := f"{excerpt} {founder_note}"):
        score += 1

    # Primary source (user complaint > secondary)
    if source_type == "user_complaint":
        score += 1

    return min(score, 5)


def _score_why_now(data: dict) -> int:
    """Score timing window urgency 1-5."""
    excerpt = data.get("excerpt", "") or ""
    founder_note = data.get("founder_note", "") or ""
    why_now = data.get("why_now", "") or ""

    combined = f"{excerpt} {founder_note} {why_now}"
    kw_count = _keyword_match_count(combined, WHY_NOW_KEYWORDS)
    has_explicit_why_now = bool(why_now and len(why_now) > 30)

    score = 1
    if has_explicit_why_now:
        score += 2
    if kw_count >= 2:
        score += 1
    if kw_count >= 4:
        score += 1
    if has_explicit_why_now and kw_count >= 3:
        score += 1

    return min(score, 5)


def _score_founder_fit(data: dict) -> int:
    """Score founder fit 1-5. How well does this match founder expertise?"""
    excerpt = data.get("excerpt", "") or ""
    founder_note = data.get("founder_note", "") or ""
    related_watchlist = data.get("related_watchlist", [])
    related_pl = data.get("related_product_lines", [])

    combined = f"{excerpt} {founder_note}".lower()
    score = 1  # Default low

    # Match against known expertise domains
    domain_matches = sum(1 for d in FOUNDER_EXPERTISE_DOMAINS if d.lower() in combined)
    if domain_matches >= 1:
        score += 1
    if domain_matches >= 2:
        score += 1

    # Related watchlist/product lines == founder has already identified this area
    if related_watchlist:
        score += 1
    if related_pl:
        score += 1

    # Detailed founder note suggests deep understanding
    if len(founder_note) > 150:
        score += 1

    return min(score, 5)


def _score_asset_leverage(data: dict) -> int:
    """Score existing asset leverage 1-5."""
    founder_note = data.get("founder_note", "") or ""
    related_pl = data.get("related_product_lines", [])
    related_watchlist = data.get("related_watchlist", [])
    source_type = data.get("source_type", "")

    combined = founder_note.lower() + " " + " ".join(related_pl + related_watchlist)
    score = 1

    # Asset scan source = high leverage
    if source_type == "asset_scan":
        score += 2

    # Related to existing product lines
    if related_pl:
        score += 1

    # Related watchlist = already monitoring this
    if related_watchlist:
        score += 1

    # Keywords suggesting existing code/asset reuse
    if _keyword_match_any(founder_note, ["codebase", "already", "existing", "built", "have"]):
        score += 1

    return min(score, 5)


def _score_mvp_speed(data: dict) -> int:
    """Score how fast an MVP can be validated 1-5."""
    founder_note = data.get("founder_note", "") or ""
    related_pl = data.get("related_product_lines", [])
    source_type = data.get("source_type", "")
    suggested_engine = data.get("suggested_engine", "")

    combined = founder_note.lower()
    score = 2  # Default mid-low

    # Asset scan = faster MVP (already have building blocks)
    if source_type == "asset_scan":
        score += 2

    # Knowledge Asset / Content / Cash Engine are faster
    if suggested_engine in ("knowledge_asset", "content_engine", "cash_engine"):
        score += 1

    # Keywords suggesting fast build
    if _keyword_match_any(combined, ["template", "already", "reuse", "quick", "simple", "small"]):
        score += 1

    # Platform plays tend to be slower
    if suggested_engine == "platform_play":
        score -= 1

    # Seller finance has codebase
    if "ai_seller_finance" in related_pl:
        score += 1

    return max(min(score, 5), 1)


def _score_distribution(data: dict) -> int:
    """Score distribution channel readiness 1-5."""
    founder_note = data.get("founder_note", "") or ""
    distribution = data.get("distribution_hint", "") or ""
    related_watchlist = data.get("related_watchlist", [])

    combined = f"{founder_note} {distribution} {' '.join(related_watchlist)}"
    kw_count = _keyword_match_count(combined, DISTRIBUTION_KEYWORDS)

    score = 1
    if kw_count >= 1:
        score += 1
    if kw_count >= 2:
        score += 1
    if kw_count >= 3:
        score += 1
    if distribution:
        score += 1  # Explicit distribution hint

    return min(score, 5)


def _score_monetization(data: dict) -> int:
    """Score monetization potential 1-5."""
    founder_note = data.get("founder_note", "") or ""
    suggested_engine = data.get("suggested_engine", "")
    related_watchlist = data.get("related_watchlist", [])
    combined = f"{founder_note} {' '.join(related_watchlist)}"
    kw_count = _keyword_match_count(combined, MONETIZATION_KEYWORDS)

    # Engine-based baseline
    engine_base = {
        "cash_engine": 4,
        "knowledge_asset": 3,
        "content_engine": 2,
        "platform_play": 2,
        "attention_engine": 1,
        "os_evolution": 1,
        "": 1,
    }.get(suggested_engine, 1)

    # Bonus for monetization keywords
    bonus = min(kw_count, 1)  # cap at +1

    return min(engine_base + bonus, 5)


def _score_attention(data: dict) -> int:
    """Score attention/virality potential 1-5."""
    founder_note = data.get("founder_note", "") or ""
    suggested_engine = data.get("suggested_engine", "")
    combined = founder_note.lower()
    kw_count = _keyword_match_count(combined, ATTENTION_KEYWORDS)

    engine_base = {
        "attention_engine": 4,
        "content_engine": 3,
        "platform_play": 2,
        "knowledge_asset": 2,
        "cash_engine": 1,
        "os_evolution": 1,
        "": 1,
    }.get(suggested_engine, 1)

    bonus = min(kw_count, 1)
    return min(engine_base + bonus, 5)


def _score_os_compounding(data: dict) -> int:
    """Score OS compounding effect 1-5. Does this strengthen the OS?"""
    related_pl = data.get("related_product_lines", [])
    founder_note = data.get("founder_note", "") or ""
    suggested_engine = data.get("suggested_engine", "")

    combined = founder_note.lower()
    score = 1

    # Directly maps to ai_company_os
    if "ai_company_os" in related_pl:
        score += 2

    # OS evolution engine
    if suggested_engine == "os_evolution":
        score += 2

    # os_feedback source = system improvement
    if data.get("source_type") == "os_feedback":
        score += 2

    # Knowledge assets can be sold as OS Kits
    if "knowledge_assets" in related_pl:
        score += 1

    # Keywords suggesting tooling / automation
    if _keyword_match_any(combined, ["tool", "automate", "workflow", "skill", "template"]):
        score += 1

    return min(score, 5)


def score_candidate(data: dict) -> dict:
    """Score all 10 dimensions for a candidate signal.

    Returns:
        dict with all 10 scoring dimension keys (1-5 each).
    """
    scores = {
        "pain_score": {"value": _score_pain(data), "label": "Pain Intensity"},
        "evidence_score": {"value": _score_evidence(data), "label": "Evidence Strength"},
        "why_now_score": {"value": _score_why_now(data), "label": "Timing Window"},
        "founder_fit_score": {"value": _score_founder_fit(data), "label": "Founder Fit"},
        "asset_leverage_score": {"value": _score_asset_leverage(data), "label": "Asset Leverage"},
        "mvp_speed_score": {"value": _score_mvp_speed(data), "label": "MVP Speed"},
        "distribution_score": {"value": _score_distribution(data), "label": "Distribution Readiness"},
        "monetization_score": {"value": _score_monetization(data), "label": "Monetization Potential"},
        "attention_score": {"value": _score_attention(data), "label": "Attention/Virality"},
        "os_compounding_score": {"value": _score_os_compounding(data), "label": "OS Compounding"},
    }
    return scores


# ════════════════════════════════════════════════════════════════════
# Classification Functions
# ════════════════════════════════════════════════════════════════════

def classify_signal_type(data: dict) -> str:
    """Determine signal type from source data."""
    source_type = data.get("source_type", "")
    if source_type in SOURCE_TYPE_TO_SIGNAL:
        return SOURCE_TYPE_TO_SIGNAL[source_type]

    # Fallback: heuristic from content
    excerpt = data.get("excerpt", "") or ""
    founder_note = data.get("founder_note", "") or ""
    combined = f"{excerpt} {founder_note}".lower()

    if _keyword_match_any(combined, ["pain", "frustrat", "complaint", "problem", "issue", "bug"]):
        return "pain"
    if _keyword_match_any(combined, ["new", "just launched", "released", "api", "model"]):
        return "capability"
    if _keyword_match_any(combined, ["trend", "growing", "shift", "market", "change"]):
        return "trend"
    if _keyword_match_any(combined, ["platform", "ecosystem", "store", "marketplace", "api"]):
        return "platform"

    return "pain"  # Default


def classify_engine(data: dict, scores: dict) -> tuple:
    """Determine primary engine and secondary engines.

    Returns:
        (primary_engine: str, secondary_engines: list)
    """
    suggested = data.get("suggested_engine", "")
    source_type = data.get("source_type", "")
    related_pl = data.get("related_product_lines", [])
    excerpt = data.get("excerpt", "") or ""
    founder_note = data.get("founder_note", "") or ""
    combined = f"{excerpt} {founder_note}".lower()

    # If explicitly suggested, use it
    if suggested in ENGINE_TYPES:
        primary = suggested
    else:
        # Heuristic classification
        if source_type == "os_feedback":
            primary = "os_evolution"
        elif "ai_seller_finance" in related_pl or _keyword_match_any(combined, ["seller", "finance", "p&l", "reconciliation"]):
            primary = "cash_engine"
        elif _keyword_match_any(combined, ["viral", "share", "social", "attention", "demo"]):
            primary = "attention_engine"
        elif "platform_ecosystem_experiments" in related_pl or _keyword_match_any(combined, ["plugin", "extension", "app store", "shopify", "roblox"]):
            primary = "platform_play"
        elif "ai_content_products" in related_pl or "ai_short_drama" in related_pl or _keyword_match_any(combined, ["content", "video", "drama", "short"]):
            primary = "content_engine"
        elif "knowledge_assets" in related_pl or _keyword_match_any(combined, ["book", "course", "guide", "methodology", "kit"]):
            primary = "knowledge_asset"
        elif _keyword_match_any(combined, ["tool", "saas", "micro"]):
            primary = "cash_engine"
        else:
            primary = "cash_engine"  # Default

    # Secondary engines
    secondary = []

    # OS compounding check
    if _score_os_compounding(data) >= 3 and primary != "os_evolution":
        secondary.append("os_evolution")

    # Knowledge asset potential
    if primary != "knowledge_asset" and (
        _keyword_match_any(combined, ["book", "course", "guide", "template", "methodology", "kit"])
        or "knowledge_assets" in related_pl
    ):
        secondary.append("knowledge_asset")

    return primary, secondary


def map_product_lines(data: dict) -> list:
    """Map signal to related product lines.

    Returns:
        list of product line IDs (1-3 max).
    """
    # If explicitly provided, use them (max 3)
    explicit = data.get("related_product_lines", [])
    if explicit:
        valid = [pl for pl in explicit if pl in PRODUCT_LINES]
        return valid[:3]

    # Heuristic mapping
    excerpt = data.get("excerpt", "") or ""
    founder_note = data.get("founder_note", "") or ""
    combined = f"{excerpt} {founder_note}".lower()
    related = data.get("related_watchlist", [])

    matched = []
    for pl_id, keywords in ASSET_KEYWORDS_MAP.items():
        if _keyword_match_any(combined, keywords):
            matched.append(pl_id)

    # Deduplicate and limit
    seen = set()
    result = []
    for pl in matched:
        if pl not in seen:
            seen.add(pl)
            result.append(pl)
        if len(result) >= 3:
            break

    # Default fallback
    if not result:
        result = ["ai_company_os"]

    return result


def recommend_route(data: dict, gate_result: dict, scores: dict) -> str:
    """Determine recommended route for the candidate signal."""
    gate_status = gate_result.get("gate_status", "needs_more_evidence")
    candidate_type = data.get("candidate_type", "venture_opportunity")

    # OS improvement -> create task
    if candidate_type == "os_improvement":
        return "create_os_improvement_task"

    # Gate-based routing
    if gate_status == "weak_candidate":
        return "park"

    if gate_status == "needs_more_evidence":
        return "request_deep_research"

    # Score-based routing
    avg_score = sum(
        scores[dim]["value"] for dim in SCORING_DIMENSIONS
    ) / len(SCORING_DIMENSIONS)

    if avg_score >= 3.5:
        return "request_card"
    elif avg_score >= 2.5:
        return "promote_signal"
    else:
        return "request_deep_research"


# ════════════════════════════════════════════════════════════════════
# Candidate Builder
# ════════════════════════════════════════════════════════════════════

def build_candidate(data: dict, output_dir: str = None, seq_override: int = 0) -> Optional[dict]:
    """Build a complete candidate signal from input data.

    This is the main pipeline function that runs the full rule chain.

    Args:
        data: Input data dict (from source note, asset scan, or OS feedback)
        output_dir: Override output directory

    Returns:
        Complete candidate dict if passed evidence gate, None otherwise.
    """
    # ── Step 1: Evidence Gate ──
    gate_result = validate_evidence_gate(data)
    if not gate_result.get("can_generate", True):
        print(f"  ⛔ Evidence Gate blocked: {'; '.join(gate_result['failures'])}")
        return None

    # ── Step 2: Classifications ──
    signal_type = classify_signal_type(data)
    product_lines = map_product_lines(data)
    scores = score_candidate(data)
    primary_engine, secondary_engines = classify_engine(data, scores)
    gate_status = gate_result["gate_status"]
    recommended_route = recommend_route(data, gate_result, scores)

    # ── Step 3: Determine candidate type ──
    if data.get("candidate_type"):
        candidate_type = data["candidate_type"]
    elif primary_engine == "os_evolution" and data.get("source_type") == "os_feedback":
        candidate_type = "os_improvement"
    else:
        candidate_type = "venture_opportunity"

    # ── Step 4: Build candidate ──
    candidate_id = _generate_candidate_id_internal(output_dir, seq=seq_override)
    candidate = {
        "candidate_id": candidate_id,
        "candidate_type": candidate_type,
        "title": data.get("title", f"Signal: {data.get('excerpt', '')[:60]}...")[:120],
        "created_at": _now_iso(),
        "signal_source": {
            "source_type": data.get("source_type", "manual_source_note"),
            "source_tier": data.get("source_tier", 3),
        },
        "signal_type": signal_type,
        "primary_engine": primary_engine,
        "secondary_engines": secondary_engines,
        "related_product_lines": product_lines,
        "company_context_refs": data.get("company_context_refs", []),
        "target_user": data.get("target_user", ""),
        "pain": data.get("pain", data.get("excerpt", "")[:200]),
        "evidence_summary": data.get("evidence_summary",
                                      f"Source: {data.get('source_type', 'manual')} | "
                                      f"{len(data.get('excerpt', ''))} chars excerpt"),
        "why_now": data.get("why_now", ""),
        "scoring": scores,
        "founder_fit_score": scores["founder_fit_score"]["value"],
        "asset_leverage_score": scores["asset_leverage_score"]["value"],
        "mvp_wedge": data.get("mvp_wedge", ""),
        "distribution_hint": data.get("distribution_hint", ""),
        "risk": data.get("risk", ""),
        "missing_evidence": data.get("missing_evidence", ""),
        "evidence_gate_status": gate_status,
        "recommended_route": recommended_route,
        "status": "candidate",
    }

    # Add source refs if present
    if data.get("url"):
        candidate["signal_source"]["source_refs"] = [{
            "url": data["url"],
            "excerpt": (data.get("excerpt", "") or "")[:200],
        }]
    elif data.get("source_refs"):
        candidate["signal_source"]["source_refs"] = data["source_refs"]

    return candidate


# ════════════════════════════════════════════════════════════════════
# Scanner Implementations
# ════════════════════════════════════════════════════════════════════

def scan_from_source_file(filepath: str, output_dir: str = None) -> Optional[dict]:
    """Scan a manual source note YAML file -> candidate signal.

    Args:
        filepath: Path to YAML source note file
        output_dir: Override output directory

    Returns:
        Candidate dict if generated, None if blocked.
    """
    data = _load_yaml(filepath)
    if not data:
        print(f"  ❌ Empty or invalid source note: {filepath}")
        return None

    print(f"  📄 Processing source note: {os.path.basename(filepath)}")

    # Normalize fields from source note format
    data.setdefault("title", data.get("excerpt", "Untitled signal")[:100])
    data.setdefault("source_ref", data.get("url", ""))

    # Run the pipeline
    candidate = build_candidate(data, output_dir, seq_override=0)
    return candidate


def scan_assets(output_dir: str = None) -> list:
    """Scan docs/ directory for existing assets that could become signals.

    Examines docs/ structure: methodology docs, build logs, evidence,
    governance docs, known issues, etc.

    Returns:
        List of candidate dicts generated.
    """
    print(f"\n  🔍 Scanning docs/ for reusable asset signals...")
    candidates = []
    seq_counter = 1

    # Scan docs/ subdirectories for notable files
    scan_targets = [
        ("docs/evidence/", "Knowledge Asset", "evidence"),
        ("docs/build-logs/", "Build Log", "build_log"),
        ("docs/registry/", "Registry", "capability_manifest"),
        ("docs/governance/", "Governance", "policy"),
        ("docs/known-issues/", "Known Issue", "system_gap"),
        ("docs/opportunity/", "Opportunity Doc", "methodology"),
        ("docs/operating-kit/", "Operating Kit", "methodology"),
    ]

    for subdir, label, asset_type in scan_targets:
        full_path = os.path.join(_DOCS_DIR, os.path.basename(subdir.rstrip("/")))
        if not os.path.isdir(full_path):
            continue

        files = []
        for f in os.listdir(full_path):
            if f.endswith(".md") and not f.startswith("."):
                files.append(os.path.join(full_path, f))

        if files:
            # Only take the most substantial file per directory
            best_file = max(files, key=lambda f: os.path.getsize(f) if os.path.isfile(f) else 0)
            content = _load_text(best_file)
            if len(content) < 200:
                continue

            rel_path = os.path.relpath(best_file, _PROJECT_ROOT)
            excerpt_first_line = content.strip().split("\n")[0].strip("# \t")[:80]

            data = {
                "source_type": "asset_scan",
                "source_tier": 2,
                "source_refs": [{"type": asset_type, "detail": rel_path}],
                "title": f"Asset: {label} — {excerpt_first_line}",
                "excerpt": f"Found at {rel_path}. {excerpt_first_line}.",
                "founder_note": f"Existing {label} in {rel_path}. "
                                f"Could be packaged as a Standalone Kit / Knowledge Asset.",
                "target_user": "Founder / OS Operator",
                "pain": "Underutilized existing asset — could generate revenue or attract attention.",
                "why_now": "Asset already exists at 60-80% completion. Low incremental effort to productize.",
                "related_product_lines": ["knowledge_assets"],
                "suggested_engine": "knowledge_asset",
                "mvp_wedge": "Package as standalone document + template",
                "distribution_hint": "github + wechat_public_account + xiaohongshu",
                "missing_evidence": "Need to assess if this asset has standalone value outside the OS context.",
            }

            candidate = build_candidate(data, output_dir, seq_override=seq_counter)
            if candidate:
                candidate["related_product_lines"].append("ai_company_os")
                # Limit to 3
                candidate["related_product_lines"] = candidate["related_product_lines"][:3]
                candidates.append(candidate)
                seq_counter += 1
                print(f"    📦 [{label}] {rel_path}")

    if not candidates:
        print("    No new asset signals generated.")

    return candidates


def scan_os_feedback(output_dir: str = None) -> list:
    """Scan reports/ and docs/ for OS runtime feedback signals.

    Examines: ceo-briefs, ceo-brief-reviews, decision-log, workflows,
    build-logs for recurring patterns, failures, automation gaps.

    Returns:
        List of candidate dicts generated.
    """
    print(f"\n  🔍 Scanning OS runtime feedback for improvement signals...")
    candidates = []
    seq_counter = 1

    # ── Scan known-issues ──
    known_issues_dir = os.path.join(_DOCS_DIR, "known-issues")
    if os.path.isdir(known_issues_dir):
        for fname in os.listdir(known_issues_dir):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(known_issues_dir, fname)
            content = _load_text(fpath)
            if len(content) < 100:
                continue

            title_line = content.strip().split("\n")[0].strip("# \t")[:80]
            rel_path = os.path.relpath(fpath, _PROJECT_ROOT)

            data = {
                "source_type": "os_feedback",
                "source_tier": 1,
                "source_refs": [{"type": "known_issue", "detail": rel_path}],
                "title": f"OS Issue: {title_line}",
                "excerpt": f"Known issue documented at {rel_path}.",
                "founder_note": f"Recurring issue needs systematic fix or Skill.",
                "target_user": "Founder / OS Operator",
                "pain": "Known issue affecting OS reliability requires ongoing manual attention.",
                "why_now": "Issue is documented and reproducible — fix before it compounds.",
                "related_product_lines": ["ai_company_os"],
                "suggested_engine": "os_evolution",
                "candidate_type": "os_improvement",
                "mvp_wedge": "Create auto-remediation Skill or patch",
                "risk": "Fix may reveal deeper architectural limitations.",
            }

            candidate = build_candidate(data, output_dir, seq_override=seq_counter)
            if candidate:
                candidates.append(candidate)
                seq_counter += 1
                print(f"    🔧 [Known Issue] {rel_path}: {title_line}")

    # ── Scan workflows for gaps ──
    workflows_dir = os.path.join(_DOCS_DIR, "workflows")
    if os.path.isdir(workflows_dir):
        for fname in os.listdir(workflows_dir):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(workflows_dir, fname)
            content = _load_text(fpath)
            if len(content) < 200:
                continue

            rel_path = os.path.relpath(fpath, _PROJECT_ROOT)
            # Check for patterns suggesting missing automation
            if _keyword_match_any(content, ["manual", "todo", "founder fill", "TBD", "future"]):
                data = {
                    "source_type": "os_feedback",
                    "source_tier": 2,
                    "source_refs": [{"type": "workflow_gap", "detail": rel_path}],
                    "title": f"Workflow Gap: {fname.replace('.md', '')} has manual steps",
                    "excerpt": f"Workflow at {rel_path} contains manual/TODO steps.",
                    "founder_note": "Automating these steps would reduce founder overhead.",
                    "target_user": "Founder / OS Operator",
                    "pain": "Workflow has manual steps requiring founder attention.",
                    "why_now": "As OS scales, manual steps become bottleneck.",
                    "related_product_lines": ["ai_company_os"],
                    "suggested_engine": "os_evolution",
                    "candidate_type": "os_improvement",
                    "mvp_wedge": "Automate one manual step as proof",
                }
                candidate = build_candidate(data, output_dir, seq_override=seq_counter)
                if candidate:
                    candidates.append(candidate)
                    seq_counter += 1
                    print(f"    🔧 [Workflow Gap] {rel_path}")

    # ── Scan decision-log for patterns ──
    decision_log = os.path.join(_REPORTS_DIR, "ceo-brief-reviews", "DECISION-LOG.md")
    if os.path.isfile(decision_log):
        content = _load_text(decision_log)
        if content:
            rel_path = os.path.relpath(decision_log, _PROJECT_ROOT)
            # Count decisions
            decision_count = len(re.findall(r'DEC-\d{8}-\d{3}', content))
            if decision_count > 10:
                data = {
                    "source_type": "os_feedback",
                    "source_tier": 2,
                    "source_refs": [{"type": "decision_log_pattern", "detail": rel_path}],
                    "title": f"OS Scale Signal: {decision_count} decisions logged",
                    "excerpt": f"Decision log has {decision_count} entries.",
                    "founder_note": f"Growing decision volume suggests need for decision automation or delegation.",
                    "target_user": "Founder / OS Operator",
                    "pain": f"{decision_count} decisions requires significant founder review overhead.",
                    "why_now": "Decision volume grows as OS matures — invest in automation now.",
                    "related_product_lines": ["ai_company_os"],
                    "suggested_engine": "os_evolution",
                    "candidate_type": "os_improvement",
                    "mvp_wedge": "Auto-classify decisions by risk level",
                }
                candidate = build_candidate(data, output_dir, seq_override=seq_counter)
                if candidate:
                    candidates.append(candidate)
                    seq_counter += 1
                    print(f"    🔧 [Decision Volume] {rel_path}: {decision_count} decisions")

    if not candidates:
        print("    No OS feedback signals generated.")

    return candidates


# ════════════════════════════════════════════════════════════════════
# Enriched Signal Scanner (v0.34 Sprint D — Integration)
# ════════════════════════════════════════════════════════════════════

def load_source_note_from_id(source_note_id: str) -> Optional[dict]:
    """Load a SourceNote JSON by its ID from research/opportunity-source-notes/.

    Args:
        source_note_id: Format SN-{connector_id}-{YYYYMMDD}-{NNN}

    Returns:
        SourceNote dict or None if not found.
    """
    if not source_note_id.startswith("SN-"):
        return None

    # Extract connector_id from the ID: SN-{connector_id}-{YYYYMMDD}-{NNN}
    parts = source_note_id.split("-")
    if len(parts) >= 4:
        connector_id = parts[1]
        fpath = os.path.join(_SOURCE_NOTES_DIR, connector_id, f"{source_note_id}.json")
        if os.path.exists(fpath):
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return None

    # Fallback: search recursively
    if os.path.isdir(_SOURCE_NOTES_DIR):
        for root, _, files in os.walk(_SOURCE_NOTES_DIR):
            if f"{source_note_id}.json" in files:
                try:
                    with open(os.path.join(root, f"{source_note_id}.json"), "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    return None

    return None


def load_enriched_signals(status_filter: str = "reviewed",
                           output_dir: str = None) -> list:
    """Load all enriched signals matching the given status.

    Args:
        status_filter: Status to filter by (default: "reviewed")
        output_dir: Override enriched signal directory

    Returns:
        List of enriched signal dicts matching the filter.
    """
    output_dir = output_dir or _ENRICHED_DIR
    if not os.path.isdir(output_dir):
        return []

    signals = []
    for fname in sorted(os.listdir(output_dir)):
        if not fname.startswith("ES-") or not fname.endswith(".json"):
            continue
        fpath = os.path.join(output_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                signal = json.load(f)
            if signal.get("status") == status_filter:
                signals.append(signal)
        except Exception:
            continue

    return signals


def enriched_to_candidate_data(enriched: dict) -> dict:
    """Map an enriched signal to the build_candidate() input format.

    Combines the enriched signal data with the original SourceNote data
    where available. Fields from the enriched signal take priority.

    Args:
        enriched: An enriched signal dict (reviewed status)

    Returns:
        data dict ready for build_candidate()
    """
    sn_id = enriched.get("source_note_id", "")
    source_note = load_source_note_from_id(sn_id)

    # ── Extract field values ──
    target_user = enriched.get("target_user", {}).get("value", "")
    pain = enriched.get("pain", {}).get("value", "")
    why_now = enriched.get("why_now", {}).get("value", "")
    signal_type_val = enriched.get("signal_type", {}).get("value", "")
    engine_hints = enriched.get("engine_hints", [])
    product_hints = enriched.get("product_line_hints", [])
    evidence_summary = enriched.get("evidence_summary", "")
    evidence_gaps = enriched.get("evidence_gaps", [])

    # SourceNote fields (fallback)
    excerpt = source_note.get("excerpt", "") if source_note else ""
    url = source_note.get("url", enriched.get("source_note_ref", "")) if source_note else enriched.get("source_note_ref", "")
    source_category = source_note.get("source_category", "") if source_note else ""
    source_tier = source_note.get("source_tier", 3) if source_note else 3
    source_platform = source_note.get("source_platform", "") if source_note else ""

    # ── Build data dict ──
    data = {
        "source_type": source_category or "enriched_signal",
        "source_tier": source_tier,
        "source_refs": [{"url": url, "excerpt": excerpt[:200]}] if url else [],
        "title": f"Enriched: {target_user[:50]} | {pain[:50]}"[:120],
        "excerpt": excerpt or evidence_summary[:300],
        "target_user": target_user,
        "pain": pain,
        "why_now": why_now,
        "signal_type": signal_type_val,
        "suggested_engine": engine_hints[0] if engine_hints else "",
        "related_product_lines": product_hints[:3],
        "evidence_summary": evidence_summary,
        "missing_evidence": "; ".join(evidence_gaps) if evidence_gaps else "",
        "founder_note": (
            "Enriched signal reviewed by Founder. "
            f"Fields: target_user={target_user}, pain filled, why_now filled. "
            f"Original source: {url}"
        ),
        "enriched_signal_ref": enriched.get("enriched_signal_id", ""),
    }

    return data


def scan_enriched(output_dir: str = None, seq_start: int = 1) -> list:
    """Scan reviewed enriched signals -> generate candidate signals.

    This is the v0.34 integration bridge: Enriched Signal -> Candidate.

    Only processes signals with:
      - status == "reviewed"
      - recommended_next_step == "enrich_and_promote"

    Args:
        output_dir: Candidate output directory
        seq_start: Starting sequence number

    Returns:
        List of candidate dicts generated.
    """
    enriched_signals = load_enriched_signals(status_filter="reviewed", output_dir=_ENRICHED_DIR)

    if not enriched_signals:
        print("  No reviewed enriched signals found.")
        print("     Run enricher first, then apply-review to promote signals.")
        return []

    # Filter for those ready to promote
    promotable = [
        es for es in enriched_signals
        if es.get("recommended_next_step") in ("enrich_and_promote",)
    ]

    if not promotable:
        print("  No enriched signals ready to promote.")
        print("     All reviewed signals have recommended_next_step != enrich_and_promote.")
        return []

    print(f"\n  Found {len(promotable)} enriched signal(s) ready for candidate generation:\n")

    candidates = []
    seq_counter = seq_start

    for es in promotable:
        es_id = es.get("enriched_signal_id", "?")
        sn_id = es.get("source_note_id", "?")
        conf = es.get("confidence", 0)
        target_user = es.get("target_user", {}).get("value", "?")[:50]
        pain = es.get("pain", {}).get("value", "?")[:50]

        print(f"  [{es_id}] from {sn_id}")
        print(f"     Conf: {conf:.2f} | Target: {target_user}")

        # Map to candidate input format
        data = enriched_to_candidate_data(es)

        # Run through build_candidate pipeline
        candidate = build_candidate(data, output_dir, seq_override=seq_counter)

        if candidate:
            # Add enriched_signal_ref for traceability
            candidate["enriched_signal_ref"] = es_id
            candidates.append(candidate)
            seq_counter += 1
            print(f"     -> {candidate['candidate_id']} (Gate: {candidate['evidence_gate_status']})")
        else:
            print(f"     -> Evidence Gate blocked")
            print(f"        Target: '{data.get('target_user', '')[:50]}' | Pain: '{data.get('pain', '')[:50]}'")

    return candidates


def cmd_scan_enriched(args):
    """Handle `scan-enriched` command."""
    output_dir = args.output_dir
    dry_run = args.dry_run

    candidates = scan_enriched(output_dir)

    if not candidates:
        print(f"\n  No candidates generated from enriched signals.")
        return

    print(f"\n  Generated {len(candidates)} candidate(s) from enriched signals:")

    for c in candidates:
        if dry_run:
            _print_candidate_summary(c)
            print()
        else:
            fp = write_candidate(c, output_dir)
            if fp:
                _print_candidate_summary(c)
                print(f"     +-- {fp}")
            print()

    # Write run ledger entry
    from datetime import datetime as dt  # noqa
    from datetime import timezone as tz  # noqa
    ledger_dir = os.path.join(_PROJECT_ROOT, "reports", "run-ledger")
    os.makedirs(ledger_dir, exist_ok=True)
    ledger_path = os.path.join(ledger_dir, f"{_today_compact()}-scan-enriched.md")
    try:
        with open(ledger_path, "w", encoding="utf-8") as f:
            f.write(f"# Scan Enriched Run\n\n")
            f.write(f"- **Date:** {_now_iso()}\n")
            f.write(f"- **Signals processed:** (in scan_enriched)\\n")
            f.write(f"- **Candidates generated:** {len(candidates)}\n\n")
            for c in candidates:
                f.write(f"- {c.get('candidate_id', '?')}: {c.get('title', '?')[:60]}\n")
        print(f"  Run ledger: {ledger_path}")
    except Exception:
        pass

# ════════════════════════════════════════════════════════════════════
# Output Writer
# ════════════════════════════════════════════════════════════════════

def write_candidate(candidate: dict, output_dir: str = None) -> Optional[str]:
    """Write a candidate signal to JSON file.

    Args:
        candidate: Complete candidate dict
        output_dir: Output directory (default: research/opportunity-candidates/)

    Returns:
        File path if written, None on failure.
    """
    output_dir = _ensure_output_dir(output_dir)
    candidate_id = candidate.get("candidate_id", "CD-UNKNOWN")
    filepath = os.path.join(output_dir, f"{candidate_id}.json")

    # Pretty-print with Chinese-friendly encoding
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(candidate, f, ensure_ascii=False, indent=2)
        return filepath
    except Exception as e:
        print(f"  ❌ Error writing candidate: {e}", file=sys.stderr)
        return None


def read_candidate(candidate_id: str, output_dir: str = None) -> Optional[dict]:
    """Read a candidate signal from JSON file."""
    output_dir = output_dir or _DEFAULT_OUTPUT_DIR
    filepath = os.path.join(output_dir, f"{candidate_id}.json")
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def list_candidates(output_dir: str = None) -> list:
    """List all candidate signals in the output directory.

    Returns:
        List of candidate summary dicts sorted by creation time (newest first).
    """
    output_dir = output_dir or _DEFAULT_OUTPUT_DIR
    if not os.path.isdir(output_dir):
        return []

    candidates = []
    for fname in os.listdir(output_dir):
        if not fname.endswith(".json") or not fname.startswith("CD-"):
            continue
        filepath = os.path.join(output_dir, fname)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            candidates.append({
                "candidate_id": data.get("candidate_id", fname[:-5]),
                "title": data.get("title", "Untitled")[:60],
                "candidate_type": data.get("candidate_type", "?"),
                "primary_engine": data.get("primary_engine", "?"),
                "gate_status": data.get("evidence_gate_status", "?"),
                "status": data.get("status", "?"),
                "recommended_route": data.get("recommended_route", "?"),
                "created_at": data.get("created_at", "?"),
                "filepath": filepath,
            })
        except (json.JSONDecodeError, KeyError):
            candidates.append({
                "candidate_id": fname[:-5],
                "title": "(parse error)",
                "candidate_type": "?",
                "primary_engine": "?",
                "gate_status": "?",
                "status": "?",
                "recommended_route": "?",
                "created_at": "?",
                "filepath": filepath,
            })

    # Sort by creation time (newest first)
    candidates.sort(key=lambda c: c.get("created_at", ""), reverse=True)
    return candidates


# ════════════════════════════════════════════════════════════════════
# CLI Commands
# ════════════════════════════════════════════════════════════════════

def cmd_scan_source_file(args):
    """Handle `scan --source-file <file>` command."""
    filepath = args.source_file
    output_dir = args.output_dir
    dry_run = args.dry_run

    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return

    candidate = scan_from_source_file(filepath, output_dir)
    if not candidate:
        return

    if dry_run:
        print(f"\n  📋 DRY RUN — candidate would be written:")
        _print_candidate_summary(candidate)
        return

    filepath_out = write_candidate(candidate, output_dir)
    if filepath_out:
        print(f"\n  ✅ Candidate written: {filepath_out}")
        _print_candidate_summary(candidate)


def cmd_scan_assets(args):
    """Handle `scan-assets` command."""
    output_dir = args.output_dir
    dry_run = args.dry_run

    candidates = scan_assets(output_dir)

    if not candidates:
        print(f"\n  ℹ️  No asset candidates generated.")
        return

    print(f"\n  📊 Generated {len(candidates)} asset candidate(s):")

    for c in candidates:
        if dry_run:
            _print_candidate_summary(c)
            print()
        else:
            fp = write_candidate(c, output_dir)
            if fp:
                _print_candidate_summary(c)
                print(f"     └── {fp}")
            print()


def cmd_scan_os_feedback(args):
    """Handle `scan-os-feedback` command."""
    output_dir = args.output_dir
    dry_run = args.dry_run

    candidates = scan_os_feedback(output_dir)

    if not candidates:
        print(f"\n  ℹ️  No OS feedback candidates generated.")
        return

    print(f"\n  📊 Generated {len(candidates)} OS feedback candidate(s):")

    for c in candidates:
        if dry_run:
            _print_candidate_summary(c)
            print()
        else:
            fp = write_candidate(c, output_dir)
            if fp:
                _print_candidate_summary(c)
                print(f"     └── {fp}")
            print()


def cmd_list_candidates(args):
    """Handle `list-candidates` command."""
    output_dir = args.output_dir
    candidates = list_candidates(output_dir)

    if not candidates:
        print(f"  ℹ️  No candidates found in {output_dir}")
        print(f"     Run a scan first: python3 scripts/opportunity_scout.py scan --source-file <file>")
        return

    # Count by type
    type_counts = {}
    for c in candidates:
        ct = c["candidate_type"]
        type_counts[ct] = type_counts.get(ct, 0) + 1

    print(f"\n{'ID':<16} {'Title':<50} {'Type':<20} {'Engine':<18} {'Gate':<18} {'Route':<22}")
    print("-" * 144)
    for c in candidates:
        title = c["title"][:48]
        print(f"{c['candidate_id']:<16} {title:<50} {c['candidate_type']:<20} "
              f"{c['primary_engine']:<18} {c['gate_status']:<18} {c['recommended_route']:<22}")

    print(f"\n📊 Total: {len(candidates)} candidates")
    for ct, count in sorted(type_counts.items()):
        print(f"   {ct}: {count}")


def cmd_show_candidate(args):
    """Handle `show-candidate <id>` command."""
    output_dir = args.output_dir
    candidate_id = args.candidate_id
    verbose = args.verbose

    candidate = read_candidate(candidate_id, output_dir)
    if not candidate:
        print(f"❌ Candidate not found: {candidate_id}")
        print(f"   Looked in: {os.path.join(output_dir or _DEFAULT_OUTPUT_DIR, f'{candidate_id}.json')}")
        return

    print(f"\n{'=' * 60}")
    print(f"  Candidate: {candidate.get('candidate_id', '?')}")
    print(f"  Title:     {candidate.get('title', '?')}")
    print(f"{'=' * 60}")
    print(f"  Type:       {candidate.get('candidate_type', '?')}")
    print(f"  Status:     {candidate.get('status', '?')}")
    print(f"  Gate:       {candidate.get('evidence_gate_status', '?')}")
    print(f"  Route:      {candidate.get('recommended_route', '?')}")
    print(f"  Source:     {candidate.get('signal_source', {}).get('source_type', '?')} "
          f"(Tier {candidate.get('signal_source', {}).get('source_tier', '?')})")
    print(f"  Created:    {candidate.get('created_at', '?')}")
    print(f"")
    print(f"  Signal Type:  {candidate.get('signal_type', '?')}")
    print(f"  Primary:      {candidate.get('primary_engine', '?')}")
    if candidate.get('secondary_engines'):
        print(f"  Secondary:    {', '.join(candidate['secondary_engines'])}")
    print(f"  Product Lines: {', '.join(candidate.get('related_product_lines', []))}")
    print(f"")
    print(f"  Target User:    {candidate.get('target_user', '—')}")
    print(f"  Pain:           {candidate.get('pain', '—')[:100]}")
    print(f"  Evidence:       {candidate.get('evidence_summary', '—')[:100]}")
    print(f"  Why Now:        {candidate.get('why_now', '—')[:100]}")
    print(f"  MVP Wedge:      {candidate.get('mvp_wedge', '—')}")
    print(f"  Distribution:   {candidate.get('distribution_hint', '—')}")
    print(f"  Risk:           {candidate.get('risk', '—')[:100]}")
    print(f"  Missing Evid:   {candidate.get('missing_evidence', '—')[:100]}")

    if verbose:
        print(f"\n  {'─' * 40}")
        print(f"  Scoring (1-5):")
        scoring = candidate.get("scoring", {})
        for dim in SCORING_DIMENSIONS:
            entry = scoring.get(dim, {})
            value = entry.get("value", "?")
            label = entry.get("label", dim)
            bar = "█" * value + "░" * (5 - value) if isinstance(value, int) else "?" * 5
            print(f"    {label:<22} {value}/5 {bar}")

        if candidate.get("signal_source", {}).get("source_refs"):
            print(f"\n  Source Refs:")
            for ref in candidate["signal_source"]["source_refs"]:
                ref_url = ref.get("url", ref.get("detail", "?"))
                ref_excerpt = (ref.get("excerpt", ref.get("detail", "")) or "")[:80]
                print(f"    • {ref_excerpt}")
                print(f"      {ref_url}")

    print(f"{'=' * 60}")


def _print_candidate_summary(candidate: dict):
    """Print a brief summary of a candidate."""
    cid = candidate.get("candidate_id", "?")
    title = candidate.get("title", "?")[:70]
    ctype = candidate.get("candidate_type", "?")
    engine = candidate.get("primary_engine", "?")
    gate = candidate.get("evidence_gate_status", "?")
    route = candidate.get("recommended_route", "?")
    status_field = candidate.get("status", "candidate")
    pl = ", ".join(candidate.get("related_product_lines", [])[:2])

    # Average score
    scoring = candidate.get("scoring", {})
    scores_vals = [s.get("value", 0) for s in scoring.values() if isinstance(s.get("value"), (int, float))]
    avg = sum(scores_vals) / len(scores_vals) if scores_vals else 0
    avg_display = f"{avg:.1f}" if avg else "?"

    type_icon = "💼" if ctype == "venture_opportunity" else "🔧"
    gate_icon = "✅" if gate == "passed" else "⚠️" if gate == "needs_more_evidence" else "🟡"

    print(f"  {type_icon} [{cid}] {title}")
    print(f"     Type: {ctype} | Engine: {engine} | Gate: {gate_icon} {gate} | Score: {avg_display}/5")
    print(f"     Status: {status_field} | Route: {route} | Lines: {pl}")


# ════════════════════════════════════════════════════════════════════
# Founder Review Commands
# ════════════════════════════════════════════════════════════════════

def _update_candidate_status(candidate_id: str, new_status: str,
                              note: str = "", output_dir: str = None) -> bool:
    """Update the status field of a candidate JSON file.

    Args:
        candidate_id: CD-YYYYMMDD-NNN
        new_status: 'promoted', 'dismissed', 'needs_more_evidence'
        note: Optional founder note
        output_dir: Override output directory

    Returns:
        True if updated, False if not found.
    """
    output_dir = output_dir or _DEFAULT_OUTPUT_DIR
    filepath = os.path.join(output_dir, f"{candidate_id}.json")

    if not os.path.exists(filepath):
        print(f"  ❌ Candidate not found: {candidate_id}")
        return False

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            candidate = json.load(f)

        old_status = candidate.get("status", "candidate")
        candidate["status"] = new_status

        # Add founder note if provided
        if note:
            if "founder_notes" not in candidate:
                candidate["founder_notes"] = []
            candidate["founder_notes"].append({
                "timestamp": _now_iso(),
                "action": new_status,
                "note": note,
            })

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(candidate, f, ensure_ascii=False, indent=2)

        print(f"  ✅ {candidate_id} — {old_status} → {new_status}")
        if note:
            print(f"     Founder note: {note}")
        return True

    except Exception as e:
        print(f"  ❌ Error updating {candidate_id}: {e}")
        return False


def cmd_candidates(args):
    """Handle `candidates` command — list all with scoring summary."""
    output_dir = args.output_dir
    status_filter = args.status
    all_candidates = list_candidates(output_dir)

    if not all_candidates:
        print(f"  ℹ️  No candidates found.")
        print(f"     Run a scan first: python3 scripts/opportunity_scout.py scan --source-file <file>")
        return

    # Apply status filter
    if status_filter:
        all_candidates = [c for c in all_candidates if c.get("status") == status_filter]

    if not all_candidates:
        print(f"  ℹ️  No candidates with status '{status_filter}'")
        return

    # Read full data for each to get scoring
    enriched = []
    for c in all_candidates:
        full = read_candidate(c["candidate_id"], output_dir)
        if full:
            scores = full.get("scoring", {})
            score_values = [s.get("value", 0) for s in scores.values() if isinstance(s.get("value"), (int, float))]
            avg = sum(score_values) / len(score_values) if score_values else 0
            enriched.append({
                **c,
                "avg_score": f"{avg:.1f}",
                "status": full.get("status", "candidate"),
                "recommended_route": full.get("recommended_route", "?"),
                "pain_score": str(scores.get("pain_score", {}).get("value", "?")),
                "founder_fit_score": str(scores.get("founder_fit_score", {}).get("value", "?")),
                "mvp_speed_score": str(scores.get("mvp_speed_score", {}).get("value", "?")),
            })

    if not enriched:
        print("  ℹ️  No parseable candidates")
        return

    # Count by status
    status_counts = {}
    for c in enriched:
        s = c["status"]
        status_counts[s] = status_counts.get(s, 0) + 1

    print(f"\n{'ID':<16} {'Title':<48} {'Type':<18} {'Score':<6} {'Pain':<5} {'Founder':<7} {'MVP':<4} {'Status':<18} {'Route':<22}")
    print("-" * 148)
    for c in enriched:
        title = c["title"][:46]
        print(f"{c['candidate_id']:<16} {title:<48} {c['candidate_type']:<18} "
              f"{c['avg_score']:<6} {c['pain_score']:<5} {c['founder_fit_score']:<7} "
              f"{c['mvp_speed_score']:<4} {c['status']:<18} {c['recommended_route']:<22}")

    print(f"\n📊 Total: {len(enriched)} candidates")
    for s, count in sorted(status_counts.items()):
        print(f"   {s}: {count}")


def cmd_promote_signal(args):
    """Handle `promote-signal <id>` command."""
    candidate_id = args.candidate_id
    note = args.note or ""
    output_dir = args.output_dir

    success = _update_candidate_status(candidate_id, "promoted", note, output_dir)
    if success:
        candidate = read_candidate(candidate_id, output_dir)
        if candidate:
            print(f"\n  📋 Next step: review candidate and decide next action")
            print(f"     Route: {candidate.get('recommended_route', '?')}")
            print(f"     → python3 scripts/opportunity_scout.py show-candidate {candidate_id} --verbose")
            print(f"     → python3 scripts/opportunity_scout.py request-card {candidate_id}")


def cmd_dismiss_signal(args):
    """Handle `dismiss-signal <id>` command."""
    candidate_id = args.candidate_id
    note = args.note or ""
    output_dir = args.output_dir

    success = _update_candidate_status(candidate_id, "dismissed", note, output_dir)
    if success:
        print(f"\n  🗑️  Signal dismissed. It remains in the candidates directory for reference.")
        print(f"     To re-activate: python3 scripts/opportunity_scout.py update-signal {candidate_id} --status candidate")


def cmd_request_card(args):
    """Handle `request-card <id>` command — generate Draft based on evidence.

    Routing:
      - weak_candidate / needs_more_evidence → deep_research Draft
      - passed → opportunity_followup Draft
    """
    candidate_id = args.candidate_id
    note = args.note or ""
    output_dir = args.output_dir

    candidate = read_candidate(candidate_id, output_dir)
    if not candidate:
        print(f"  ❌ Candidate not found: {candidate_id}")
        return

    gate_status = candidate.get("evidence_gate_status", "needs_more_evidence")
    route = candidate.get("recommended_route", "")
    title = candidate.get("title", "Untitled")[:80]
    ctype = candidate.get("candidate_type", "venture_opportunity")
    engine = candidate.get("primary_engine", "?")

    print(f"\n  📄 Generating Draft for {candidate_id}")
    print(f"     Title: {title}")
    print(f"     Gate:  {gate_status}")
    print(f"     Route: {route}")
    print()

    # Determine draft type
    needs_research = gate_status in ("weak_candidate", "needs_more_evidence") or route in ("request_deep_research",)

    # Generate WO-DRAFT filename
    drafts_dir = os.path.join(_PROJECT_ROOT, "reports", "work-order-drafts")
    os.makedirs(drafts_dir, exist_ok=True)

    existing_drafts = [f for f in os.listdir(drafts_dir) if f.startswith("WO-DRAFT-") and f.endswith(".md")] if os.path.isdir(drafts_dir) else []
    next_idx = len(existing_drafts) + 1
    today = _today_compact()
    draft_id = f"WO-DRAFT-{today}-{next_idx:03d}"

    if needs_research:
        # ── Deep Research Draft ──
        missing_evidence = candidate.get("missing_evidence", "Not specified")
        pain = candidate.get("pain", "—")[:200]
        why_now = candidate.get("why_now", "—")[:200]

        content = f"""# Deep Research Draft — {candidate_id}

**Draft ID:** {draft_id}
**Source Candidate:** {candidate_id}
**Source Type:** {ctype}
**Primary Engine:** {engine}
**Created:** {_now_iso()}
**Generated By:** opportunity-scout

---

## Research Goal

Validate whether this signal warrants a full opportunity card:

> {title}

## Evidence Gap

The signal passed the Evidence Gate but has **{gate_status}** status.
Missing or weak evidence:

```
{missing_evidence}
```

## What to Research

1. **Target User Validation** — Can we find 3+ real users expressing this pain?
2. **Market Sizing** — How large is the addressable market?
3. **Competitive Landscape** — Who else is solving this?
4. **Willingness to Pay** — Would users actually pay?
5. **MVP Feasibility** — Can we build a validation wedge in 3-7 days?

## Context

**Pain:** {pain}

**Why Now:** {why_now}

---

## Output

After research, produce:
1. Updated candidate signal with stronger evidence
2. OR a dismiss recommendation with clear reasoning
3. OR a request for full opportunity card creation

---

## Founder Note

{note or "(none)"}

---

_draft_status: draft_
_draft_type: deep_research_
_source_candidate: {candidate_id}_
"""
    else:
        # ── Opportunity Follow-up Draft ──
        pl = ", ".join(candidate.get("related_product_lines", []))
        pain = candidate.get("pain", "—")[:200]
        mvp = candidate.get("mvp_wedge", "Not specified")
        distribution = candidate.get("distribution_hint", "Not specified")
        risk = candidate.get("risk", "None identified")[:200]

        content = f"""# Opportunity Follow-up Draft — {candidate_id}

**Draft ID:** {draft_id}
**Source Candidate:** {candidate_id}
**Source Type:** {ctype}
**Primary Engine:** {engine}
**Product Lines:** {pl}
**Created:** {_now_iso()}
**Generated By:** opportunity-scout

---

## Opportunity Summary

> {title}

**Pain:** {pain}

**Why Now:** {candidate.get('why_now', '—')[:200]}

**Target User:** {candidate.get('target_user', '—')}

## MVP Wedge

> {mvp}

## Distribution

> {distribution}

## Risk

> {risk}

## Suggested Next Steps

1. [ ] Validate MVP wedge with 3-5 target users
2. [ ] Define pricing model ({engine})
3. [ ] Identify first distribution channel
4. [ ] Build prototype
5. [ ] Set success criteria

---

## Scoring Summary

| Dimension | Score |
|:----------|:-----:|
"""

        scoring = candidate.get("scoring", {})
        for dim in SCORING_DIMENSIONS:
            entry = scoring.get(dim, {})
            val = entry.get("value", "?")
            label = entry.get("label", dim)
            content += f"| {label} | {val}/5 |\n"

        content += f"""
---

## Founder Note

{note or "(none)"}

---

_draft_status: draft_
_draft_type: opportunity_followup_
_source_candidate: {candidate_id}_
"""

    # Write the draft
    draft_path = os.path.join(drafts_dir, f"{draft_id}.md")
    with open(draft_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"  ✅ Draft generated: reports/work-order-drafts/{draft_id}.md")
    print(f"     Type: {'🔬 Deep Research' if needs_research else '💼 Opportunity Follow-up'}")
    print()
    print(f"  ℹ️  Next step: Founder reviews the draft")
    print(f"     → review at reports/work-order-drafts/{draft_id}.md")
    print(f"     → or run: cat reports/work-order-drafts/{draft_id}.md")


# ════════════════════════════════════════════════════════════════════
# CLI Parser
# ════════════════════════════════════════════════════════════════════

def build_parser(subparsers=None) -> argparse.ArgumentParser:
    """Build the argument parser.

    Can work standalone or as a subparser of opportunity.py's 'scout' command.
    """
    if subparsers:
        parser = subparsers.add_parser("scout", help="Opportunity Scout — run the discovery engine")
        sub = parser.add_subparsers(dest="scout_cmd", required=True)
    else:
        parser = argparse.ArgumentParser(
            description="v0.32 — Opportunity Scout Runner P0",
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  python3 scripts/opportunity_scout.py scan --source-file config/examples/manual-source-note.example.yaml
  python3 scripts/opportunity_scout.py scan-assets
  python3 scripts/opportunity_scout.py scan-os-feedback
  python3 scripts/opportunity_scout.py scan-enriched
  python3 scripts/opportunity_scout.py candidates
  python3 scripts/opportunity_scout.py promote-signal CD-20260531-001 --note "Good fit"
  python3 scripts/opportunity_scout.py request-card CD-20260531-001
            """,
        )
        sub = parser.add_subparsers(dest="command", required=True)

    # --- scan (source file) ---
    scan_p = sub.add_parser("scan", help="Scan a manual source note file -> candidate signal")
    scan_p.add_argument("--source-file", "-f", required=True,
                        help="Path to YAML source note file")
    scan_p.add_argument("--output-dir", "-o", default=None,
                        help="Override output directory (default: research/opportunity-candidates/)")
    scan_p.add_argument("--dry-run", "-n", action="store_true",
                        help="Show candidate without writing to disk")

    # --- scan-assets ---
    assets_p = sub.add_parser("scan-assets", help="Scan docs/ for existing asset signals")
    assets_p.add_argument("--output-dir", "-o", default=None,
                          help="Override output directory")
    assets_p.add_argument("--dry-run", "-n", action="store_true",
                          help="Show candidates without writing to disk")

    # --- scan-os-feedback ---
    osf_p = sub.add_parser("scan-os-feedback", help="Scan OS runtime feedback for improvement signals")
    osf_p.add_argument("--output-dir", "-o", default=None,
                       help="Override output directory")
    osf_p.add_argument("--dry-run", "-n", action="store_true",
                       help="Show candidates without writing to disk")

    # --- scan-enriched ---
    enriched_p = sub.add_parser("scan-enriched", help="Scan reviewed Enriched Signals -> candidates")
    enriched_p.add_argument("--output-dir", "-o", default=None,
                            help="Override candidate output directory")
    enriched_p.add_argument("--dry-run", "-n", action="store_true",
                            help="Show candidates without writing to disk")

    # --- list-candidates ---
    list_p = sub.add_parser("list-candidates", help="List all generated candidate signals")
    list_p.add_argument("--output-dir", "-o", default=None,
                        help="Override output directory")

    # --- show-candidate ---
    show_p = sub.add_parser("show-candidate", help="Show a specific candidate signal")
    show_p.add_argument("candidate_id", help="Candidate ID (e.g., CD-20260531-001)")
    show_p.add_argument("--output-dir", "-o", default=None,
                        help="Override output directory")
    show_p.add_argument("--verbose", "-v", action="store_true",
                        help="Show full scoring details and source refs")

    # --- candidates (Founder Review) ---
    cand_p = sub.add_parser("candidates", help="List all candidates with scoring summary for Founder review")
    cand_p.add_argument("--status", "-s", default=None,
                        help="Filter by status (candidate, promoted, dismissed)")
    cand_p.add_argument("--output-dir", "-o", default=None,
                        help="Override output directory")

    # --- promote-signal ---
    prom_p = sub.add_parser("promote-signal", help="Promote a candidate signal")
    prom_p.add_argument("candidate_id", help="Candidate ID (e.g., CD-20260531-001)")
    prom_p.add_argument("--note", "-n", default="", help="Founder note")
    prom_p.add_argument("--output-dir", "-o", default=None,
                        help="Override output directory")

    # --- dismiss-signal ---
    dismiss_p = sub.add_parser("dismiss-signal", help="Dismiss a candidate signal")
    dismiss_p.add_argument("candidate_id", help="Candidate ID (e.g., CD-20260531-001)")
    dismiss_p.add_argument("--note", "-n", default="", help="Founder note")
    dismiss_p.add_argument("--output-dir", "-o", default=None,
                           help="Override output directory")

    # --- request-card ---
    req_p = sub.add_parser("request-card", help="Generate a Draft from a candidate signal")
    req_p.add_argument("candidate_id", help="Candidate ID (e.g., CD-20260531-001)")
    req_p.add_argument("--note", "-n", default="", help="Founder note for the draft")
    req_p.add_argument("--output-dir", "-o", default=None,
                       help="Override candidate output directory")

    return parser if subparsers is None else parser


def main(args_list: list = None):
    """Main entry point.

    Args:
        args_list: Optional list of args (excluding program name).
                   If None, uses sys.argv[1:].
                   Supports both standalone and delegation mode.
    """
    parser = build_parser()
    args = parser.parse_args(args_list)

    # Determine command name (standalone = cmd.command; delegation = cmd.scout_cmd)
    cmd = getattr(args, "scout_cmd", None) or getattr(args, "command", None)
    if not cmd:
        parser.print_help()
        return

    # Dispatch
    if cmd == "scan":
        cmd_scan_source_file(args)
    elif cmd == "scan-assets":
        cmd_scan_assets(args)
    elif cmd == "scan-os-feedback":
        cmd_scan_os_feedback(args)
    elif cmd == "scan-enriched":
        cmd_scan_enriched(args)
    elif cmd == "list-candidates":
        cmd_list_candidates(args)
    elif cmd == "show-candidate":
        cmd_show_candidate(args)
    elif cmd == "candidates":
        cmd_candidates(args)
    elif cmd == "promote-signal":
        cmd_promote_signal(args)
    elif cmd == "dismiss-signal":
        cmd_dismiss_signal(args)
    elif cmd == "request-card":
        cmd_request_card(args)
    else:
        print(f"Unknown command: {cmd}")
        parser.print_help()


if __name__ == "__main__":
    main()
