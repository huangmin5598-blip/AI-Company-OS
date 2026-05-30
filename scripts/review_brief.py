#!/usr/bin/env python3
"""
v0.19 — CEO Brief Review & Decision Layer Lite

Subcommands:
  index                    — Scan reports/ceo-briefs/ → INDEX.md
  review <brief>           — Extract decision items + generate review template
  decide <review-file>     — Read filled-out review → DECISION-LOG.md (dedup + conflict check)
  status                   — Overview of all Briefs and review statuses

No LLM — pure Markdown rule parsing.
No changes to launchd, worker, operating loop.
"""

import os
import re
import sys
import json
from datetime import datetime
from pathlib import Path

# ── Paths ─────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
BRIEFS_DIR = PROJECT_ROOT / "reports" / "ceo-briefs"
REVIEWS_DIR = PROJECT_ROOT / "reports" / "ceo-brief-reviews"
INDEX_PATH = BRIEFS_DIR / "INDEX.md"
DECISION_LOG_PATH = REVIEWS_DIR / "DECISION-LOG.md"
DRAFTS_DIR = PROJECT_ROOT / "reports" / "work-order-drafts"
DRAFTS_INDEX_PATH = DRAFTS_DIR / "INDEX.md"

# ── Helpers ───────────────────────────────────────────────────────────

def parse_date_from_filename(filename):
    """Extract YYYY-MM-DD from filename like 2026-05-30.md or DRY-RUN-2026-05-30.md."""
    m = re.search(r'(\d{4}-\d{2}-\d{2})', filename)
    return m.group(1) if m else None


def parse_brief(path):
    """Parse a CEO Brief markdown file into a structured dict."""
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    lines = text.split("\n")
    filename = os.path.basename(path)
    date = parse_date_from_filename(filename)

    # ── brief_type from footer (last 10 lines) ──
    brief_type = "unknown"
    for line in lines[-10:]:
        m = re.search(r'_brief_type:\s*(.+)_', line)
        if m:
            brief_type = m.group(1).strip()
            break

    # ── Work order counts from Section 1 ──
    work_orders_count = 0
    completed_count = 0
    failed_count = 0
    needs_review_count = 0

    sec1_match = re.search(r'## 1\.\s*运行摘要(.+?)(?=^---|\Z)', text, re.DOTALL | re.MULTILINE)
    if sec1_match:
        sec1 = sec1_match.group(1)
        m = re.search(r'执行 Work Orders[^0-9]*(\d+)', sec1)
        if m: work_orders_count = int(m.group(1))
        m = re.search(r'✅ 成功[^0-9]*(\d+)', sec1)
        if m: completed_count = int(m.group(1))
        m = re.search(r'❌ 失败[^0-9]*(\d+)', sec1)
        if m: failed_count = int(m.group(1))
        m = re.search(r'Needs Review[^0-9]*(\d+)', sec1)
        if m: needs_review_count = int(m.group(1))

    # ── Warnings from Section 5 ──
    warnings_count = 0
    sec5_match = re.search(r'## 5\.\s*Budget & Failure Warnings(.+?)(?=^---|\Z)', text, re.DOTALL | re.MULTILINE)
    if sec5_match:
        sec5 = sec5_match.group(1)
        budget_match = re.search(r'Budget Warning', sec5)
        failure_match = re.search(r'Failure', sec5)
        if budget_match or failure_match:
            warnings_count += 1
        # Count items in "⚠️需要关注" subsection
        urgent_warnings = re.findall(r'^##', sec5, re.MULTILINE)
        # Actually count bullet items
        bullet_items = re.findall(r'^- ', sec5)
        warnings_count = max(warnings_count, len(bullet_items))

    # ── Decision items from Section 7 ──
    decision_items = []
    sec7_match = re.search(r'## 7\.\s*需要 Founder 决策的事项(.+?)(?=^---|\Z)', text, re.DOTALL | re.MULTILINE)
    has_decision_items = True

    if sec7_match:
        sec7 = sec7_match.group(1)
        # Check for "no decision items" marker
        if re.search(r'本次无需要 Founder 决策的事项', sec7):
            has_decision_items = False
        else:
            # Find subsections: ### ⚠️ or ### ℹ️
            subsections = re.findall(r'###\s*([^\n]+)(.*?)(?=###|\Z)', sec7, re.DOTALL)
            for heading, body in subsections:
                heading = heading.strip()
                if '⚠️' in heading:
                    dtype = 'urgent'
                elif 'ℹ️' in heading:
                    dtype = 'maintenance'
                else:
                    dtype = 'unknown'

                # Extract bullet items
                bullets = re.findall(r'^- (.+)$', body, re.MULTILINE)
                for bullet in bullets:
                    # Clean up the bullet text (remove emoji prefix)
                    clean_text = re.sub(r'^[📦🔴🟡🟢⚠️ℹ️✅❌📊📋⚡💼⏳📡🔧🎯🔄🚀]\s*', '', bullet).strip()
                    decision_items.append({
                        "summary": clean_text,
                        "decision_type": dtype,
                        "bullet_raw": bullet,
                    })
    else:
        has_decision_items = False

    decision_items_count = len(decision_items)

    # ── Determine review_status ──
    review_path = REVIEWS_DIR / f"{date}-review.md"
    decision_log_path = REVIEWS_DIR / "DECISION-LOG.md"

    if not has_decision_items:
        review_status = "no_decision_items"
    elif review_path.exists():
        # Check if it has been decided (logged in DECISION-LOG)
        if decision_log_path.exists():
            log_text = decision_log_path.read_text(encoding="utf-8")
            # Check if this brief's decisions are in the log
            brief_rel = f"reports/ceo-briefs/{filename}"
            if brief_rel in log_text:
                # Check for invalid_review marker in the review file
                review_text = review_path.read_text(encoding="utf-8")
                if "invalid_review" in review_text:
                    review_status = "invalid_review"
                else:
                    review_status = "reviewed"
            else:
                review_status = "review_generated"
        else:
            review_status = "review_generated"
    else:
        review_status = "pending_review"

    return {
        "date": date,
        "filename": filename,
        "brief_path": f"reports/ceo-briefs/{filename}",
        "brief_type": brief_type,
        "work_orders_count": work_orders_count,
        "completed_count": completed_count,
        "failed_count": failed_count,
        "warnings_count": warnings_count,
        "decision_items_count": decision_items_count,
        "decision_items": decision_items,
        "has_decision_items": has_decision_items,
        "review_status": review_status,
        "review_path": f"reports/ceo-brief-reviews/{date}-review.md" if has_decision_items else "",
    }


def scan_all_briefs():
    """Scan reports/ceo-briefs/ and parse all Briefs."""
    if not BRIEFS_DIR.exists():
        return []
    briefs = []
    for f in sorted(BRIEFS_DIR.glob("*.md")):
        if f.name == "INDEX.md":
            continue
        try:
            briefs.append(parse_brief(str(f)))
        except Exception as e:
            print(f"  ⚠️  Skipping {f.name}: {e}", file=sys.stderr)
    # Sort by date descending
    briefs.sort(key=lambda b: b.get("date", ""), reverse=True)
    return briefs


# ── Subcommand: index ────────────────────────────────────────────────

def cmd_index():
    """Scan all Briefs and generate/update INDEX.md."""
    briefs = scan_all_briefs()
    if not briefs:
        print("  ℹ️  No Briefs found in reports/ceo-briefs/")
        return

    lines = [
        "# CEO Brief Index",
        "",
        "_Auto-generated by review_brief.py index_",
        f"_Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_",
        "",
        "| Date | Brief | Type | WOs | ✅ | ❌ | Warnings | Decisions | Review Status | Review File |",
        "|------|-------|------|:---:|:--:|:--:|:--------:|:---------:|:-------------:|:-----------:|",
    ]

    for b in briefs:
        review_link = f"[review]({b['review_path']})" if b['has_decision_items'] and b['review_status'] != 'no_decision_items' else "—"
        date_link = f"[{b['date']}]({b['brief_path']})"
        lines.append(
            f"| {date_link} "
            f"| {b['brief_type']} "
            f"| {b['work_orders_count']} "
            f"| {b['completed_count']} "
            f"| {b['failed_count']} "
            f"| {b['warnings_count']} "
            f"| {b['decision_items_count']} "
            f"| {status_icon(b['review_status'])} {b['review_status']} "
            f"| {review_link} |"
        )

    INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    INDEX_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  ✅ INDEX.md updated — {len(briefs)} Brief(s) indexed")


def status_icon(status):
    icons = {
        "pending_review": "🟡",
        "review_generated": "🟢",
        "reviewed": "✅",
        "no_decision_items": "ℹ️",
        "invalid_review": "🔴",
    }
    return icons.get(status, "⚪")


# ── Subcommand: review ───────────────────────────────────────────────

def cmd_review(brief_path):
    """Extract decision items from a Brief and generate review template."""
    brief = parse_brief(brief_path)
    if not brief["date"]:
        print(f"  ❌ Could not parse date from: {brief_path}")
        return

    review_path = REVIEWS_DIR / f"{brief['date']}-review.md"
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)

    if not brief["has_decision_items"]:
        # Generate minimal review file for no-decision case
        content = [
            f"# CEO Brief Review — {brief['date']}",
            "",
            f"_Source: {brief['brief_path']}_",
            f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_",
            "",
            "---",
            "## Decision Items",
            "",
            "_没有需要决策的事项。_",
            "",
            "---",
            "## Founder Review",
            "",
            "- [ ] no_decision_items (无需操作)",
            "",
            "---",
            "_review_status: no_decision_items_",
        ]
        review_path.write_text("\n".join(content) + "\n", encoding="utf-8")
        print(f"  ✅ Review generated (no decision items): {review_path}")
        return

    lines = [
        f"# CEO Brief Review — {brief['date']}",
        "",
        f"_Source: {brief['brief_path']}_",
        f"_Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_",
        "",
        "---",
        "## Brief Summary",
        f"- **Type:** {brief['brief_type']}",
        f"- **Work Orders:** {brief['work_orders_count']} (✅ {brief['completed_count']}, ❌ {brief['failed_count']})",
        f"- **Warnings:** {brief['warnings_count']}",
        "",
        "---",
        "## Decision Items",
        "",
    ]

    for i, item in enumerate(brief["decision_items"]):
        did = f"DEC-{brief['date'].replace('-', '')}-{i+1:03d}"
        type_icon = "⚠️" if item["decision_type"] == "urgent" else "ℹ️"
        lines.append(f"### {type_icon} {did}: {item['summary']}")
        lines.append("")
        lines.append(f"_Type: {item['decision_type']}_")
        lines.append("")
        lines.append("**Founder Decision:**")
        lines.append("")
        lines.append("- [ ] approve (批准)")
        lines.append("- [ ] dismiss (忽略)")
        lines.append("- [ ] park (暂缓)")
        lines.append("- [ ] create_work_order_later (后续创建 Work Order)")
        lines.append("- [ ] needs_follow_up (需跟进)")
        lines.append("")
        lines.append("**Notes:**")
        lines.append("")
        lines.append("```")
        lines.append("")
        lines.append("```")
        lines.append("")

    lines.append("---")
    lines.append("## Overall Review Status")
    lines.append("")
    lines.append("- [ ] all_decided (所有决策项已勾选)")
    lines.append("")
    lines.append("---")
    lines.append(f"_review_status: review_generated_")

    review_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  ✅ Review generated: {review_path}")
    print(f"  📋 {len(brief['decision_items'])} decision item(s) extracted")

    # Print extracted items to stdout for clarity
    for i, item in enumerate(brief["decision_items"]):
        did = f"DEC-{brief['date'].replace('-', '')}-{i+1:03d}"
        print(f"     {i+1}. [{item['decision_type']}] {did}: {item['summary']}")


# ── Subcommand: decide ────────────────────────────────────────────────

def cmd_decide(review_path):
    """Read a filled-out review file and append decisions to DECISION-LOG.md."""
    if not os.path.exists(review_path):
        print(f"  ❌ Review file not found: {review_path}")
        return

    with open(review_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Extract source brief from the _Source: header
    source_brief = None
    m = re.search(r'_Source:\s*(.+)_', text)
    if m:
        source_brief = m.group(1).strip()

    # Extract date from filename or review header
    date = None
    m = re.search(r'# CEO Brief Review — (\d{4}-\d{2}-\d{2})', text)
    if m:
        date = m.group(1)
    if not date:
        m = re.search(r'(\d{4}-\d{2}-\d{2})', os.path.basename(review_path))
        if m:
            date = m.group(1)

    if not date:
        print(f"  ❌ Could not determine date from: {review_path}")
        return

    # Check for no_decision_items
    if re.search(r'\[x\] no_decision_items', text, re.IGNORECASE):
        print(f"  ℹ️  Brief marked as no_decision_items — nothing to decide")
        return

    # Parse decision items and their checked actions
    # Each decision item is a section: ### ⚠️ DEC-... or ### ℹ️ DEC-...
    decisions = []
    sections = re.findall(
        r'###\s*[⚠️ℹ️]*\s*(DEC-\d+-\d+):\s*(.*?)(?=###\s*[⚠️ℹ️]*\s*DEC-|\Z|^##)',
        text, re.DOTALL | re.MULTILINE
    )

    if not sections:
        print(f"  ❌ No decision items found in: {review_path}")
        return

    for did, body in sections:
        did = did.strip()
        summary = body.split('\n')[0].strip() if body.split('\n')[0].strip() else "（见上方）"

        # Find checked boxes: - [x] action
        checked = re.findall(r'-\s*\[x\]\s*(.+?)$', body, re.MULTILINE | re.IGNORECASE)
        checked = [c.strip() for c in checked]

        # Determine decision_type from the section header
        # Look backwards from the DID to find the header context
        dtype = "unknown"

        # Find notes if any (between ``` markers)
        notes_m = re.search(r'```\s*(.*?)\s*```', body, re.DOTALL)
        notes = notes_m.group(1).strip() if notes_m else ""

        decisions.append({
            "decision_id": did,
            "summary": summary,
            "checked": checked,
            "notes": notes,
        })

    # ── Validate: each item must have exactly 1 checked action ──
    valid_decisions = []
    has_conflicts = False

    for d in decisions:
        if len(d["checked"]) == 0:
            print(f"  ⚠️  {d['decision_id']}: no decision made (nothing checked) — skipping")
        elif len(d["checked"]) > 1:
            print(f"  ❌ {d['decision_id']}: MULTIPLE decisions checked: {', '.join(d['checked'])} — INVALID")
            has_conflicts = True
        else:
            valid_decisions.append(d)

    if has_conflicts:
        print(f"")
        print(f"  🔴 Conflict detected! Some items have multiple decisions.")
        print(f"  Fix the review file so each item has exactly 1 checked action,")
        print(f"  then re-run this command with the same review file.")
        print(f"")

        # Mark review as invalid
        invalid_marker = "\n_review_status: invalid_review_\n"
        if invalid_marker.strip() not in text:
            text += invalid_marker
            with open(review_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"  ✏️  Marked review as invalid_review")

        # Write what we can (valid ones) but flag the overall status
        if not valid_decisions:
            print(f"  ❌ No valid decisions to log")
            return
        print(f"  ℹ️  Logging {len(valid_decisions)} valid decision(s), but review is marked invalid")

    # ── Dedup check ──
    REVIEWS_DIR.mkdir(parents=True, exist_ok=True)

    existing_log_ids = set()
    if DECISION_LOG_PATH.exists():
        with open(DECISION_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                m = re.match(r'^\|\s*([A-Za-z0-9-]+)\s*\|.*?reports/ceo-briefs/', line)
                if m:
                    existing_log_ids.add(m.group(1))

    # Also build (did, source_brief) pairs for dedup
    existing_pairs = set()
    if DECISION_LOG_PATH.exists() and source_brief:
        with open(DECISION_LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                parts = [p.strip() for p in line.split('|')]
                if len(parts) >= 5 and parts[2] and parts[3] and not parts[1].startswith('-'):
                    log_did = parts[2]
                    log_source = parts[3]
                    existing_pairs.add((log_did, log_source))

    # ── Append to DECISION-LOG.md ──
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_entries = []
    skipped = 0

    # Check if date section exists
    needs_date_header = True
    if DECISION_LOG_PATH.exists():
        with open(DECISION_LOG_PATH, "r", encoding="utf-8") as f:
            if f"## {date}" in f.read():
                needs_date_header = False

    for d in valid_decisions:
        pair = (d["decision_id"], source_brief or "")
        if pair in existing_pairs:
            print(f"  ℹ️  {d['decision_id']}: already logged, skipped")
            skipped += 1
            continue

        action = d["checked"][0]
        new_entries.append({
            "decision_id": d["decision_id"],
            "source_brief": source_brief or "unknown",
            "summary": d["summary"],
            "founder_decision": action,
            "notes": d["notes"],
            "created_at": now,
        })

    if not new_entries:
        if skipped > 0:
            print(f"  ✅ All {skipped} decision(s) already logged — nothing to add")
        else:
            print(f"  ℹ️  No new decisions to log")
        return

    # Build log content
    log_lines = []

    # If log doesn't exist, create with header
    if not DECISION_LOG_PATH.exists():
        log_lines = [
            "# CEO Brief — Decision Log",
            "",
            "_Auto-generated. Append-only._",
            f"_Created: {now}_",
            "",
            "| Date | Decision ID | Source Brief | Summary | Decision | Notes | Logged At |",
            "|------|-------------|--------------|---------|----------|-------|-----------|",
        ]
    else:
        # Read existing content, we'll append entries before the end
        with open(DECISION_LOG_PATH, "r", encoding="utf-8") as f:
            existing_content = f.read()

        # Check if the file has the table header
        if "| Date | Decision ID |" not in existing_content:
            log_lines = existing_content.rstrip().split("\n")
            log_lines.extend([
                "",
                "| Date | Decision ID | Source Brief | Summary | Decision | Notes | Logged At |",
                "|------|-------------|--------------|---------|----------|-------|-----------|",
            ])
        else:
            # Find where the table data starts (skip header + separator rows)
            lines = existing_content.rstrip().split("\n")
            log_lines = lines

    # Add new entries
    action_labels = {
        "approve": "✅ approve",
        "dismiss": "⏭️ dismiss",
        "park": "📦 park",
        "create_work_order_later": "📋 create_WO_later",
        "needs_follow_up": "🔍 needs_follow_up",
    }

    for entry in new_entries:
        action_clean = entry["founder_decision"].strip().lower().replace("(", "").replace(")", "")
        action_label = action_labels.get(entry["founder_decision"].strip(), entry["founder_decision"].strip())
        notes_clean = entry["notes"].replace("\n", " ")[:80] if entry["notes"] else "—"
        log_lines.append(
            f"| {date} "
            f"| {entry['decision_id']} "
            f"| {entry['source_brief']} "
            f"| {entry['summary'][:60]} "
            f"| {action_label} "
            f"| {notes_clean} "
            f"| {entry['created_at']} |"
        )

    DECISION_LOG_PATH.write_text("\n".join(log_lines) + "\n", encoding="utf-8")
    print(f"  ✅ DECISION-LOG.md updated — {len(new_entries)} new decision(s) logged")
    if skipped:
        print(f"  ℹ️  {skipped} already-logged decision(s) skipped")

    # Also update the review file's status if not already invalid
    with open(review_path, "r", encoding="utf-8") as f:
        rev_text = f.read()
    if "_review_status: invalid_review" not in rev_text:
        # Remove any existing review_status line and add reviewed
        rev_text = re.sub(r'_review_status:.*', '', rev_text)
        rev_text += "\n_review_status: reviewed_\n"
        with open(review_path, "w", encoding="utf-8") as f:
            f.write(rev_text)
        print(f"  ✏️  Review status updated to: reviewed")

    # ── Generate Work Order Drafts for create_work_order_later ──
    draft_decisions = [e for e in new_entries if "create_work_order_later" in e["founder_decision"]]
    if draft_decisions:
        DRAFTS_DIR.mkdir(parents=True, exist_ok=True)
        dt = datetime.now()
        for idx, entry in enumerate(draft_decisions):
            draft_id = f"WO-DRAFT-{dt.strftime('%Y%m%d')}-{idx+1:03d}"
            draft_path = DRAFTS_DIR / f"{draft_id}.md"
            draft_content = _generate_draft(draft_id, entry, date)
            draft_path.write_text(draft_content, encoding="utf-8")
            print(f"  📄 Draft generated: {draft_path}")
        _update_draft_index()
        print(f"  📋 {len(draft_decisions)} draft(s) generated in reports/work-order-drafts/")


# ── Draft generation helpers ─────────────────────────────────────────

def _generate_draft(draft_id, entry, brief_date):
    """Generate a Work Order Draft markdown file from a decision entry."""
    title = entry["summary"][:80]
    return f"""# Work Order Draft

**Draft ID:** {draft_id}
**Source Brief:** {entry['source_brief']}
**Source Decision:** {entry['decision_id']}
**Decision Type:** maintenance
**Risk Level:** medium
**Approval Required:** true
**Created:** {entry['created_at']}

---
## Auto-filled Title

{title}

---
## Founder To Fill

**Suggested Task Type:**
```
TODO: Founder to fill
```

**Suggested Skill:**
```
TODO: Founder to fill
```

**Suggested Agent:**
```
TODO: Founder to fill
```

**Proposed Prompt:**
```
TODO: Founder to fill
```

**Expected Output:**
```
TODO: Founder to fill
```

---
## Founder Confirmation

- [ ] approve_create_work_order (确认创建 Work Order)
- [ ] edit_required (需要修改)
- [ ] dismiss (放弃此草稿)

---
## Notes

_{entry['notes'] or '(none)'}_

---
_draft_status: created_
"""


def _update_draft_index():
    """Scan work-order-drafts/ and regenerate INDEX.md."""
    if not DRAFTS_DIR.exists():
        return
    drafts = sorted(DRAFTS_DIR.glob("WO-DRAFT-*.md"))
    if not drafts:
        DRAFTS_INDEX_PATH.write_text("# Work Order Drafts Index\n\n_No drafts._\n", encoding="utf-8")
        return

    lines = [
        "# Work Order Drafts Index",
        "",
        "_Auto-generated._",
        f"_Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_",
        "",
        "| Draft | Source Brief | Decision | Title | Status |",
        "|-------|-------------|----------|-------|--------|",
    ]
    for d in drafts:
        text = d.read_text(encoding="utf-8")
        source = "unknown"
        m = re.search(r'\*\*Source Brief:\*\*\s*(.+)', text)
        if m: source = m.group(1).strip()
        decision = "unknown"
        m = re.search(r'\*\*Source Decision:\*\*\s*(.+)', text)
        if m: decision = m.group(1).strip()
        title = "—"
        m = re.search(r'^## Auto-filled Title\s*\n+(.+)$', text, re.MULTILINE)
        if m: title = m.group(1).strip()[:50]
        status = "created"
        m = re.search(r'_draft_status:\s*(.+)_', text)
        if m: status = m.group(1).strip()
        lines.append(f"| [{d.name}]({d.name}) | {source} | {decision} | {title} | {status} |")

    DRAFTS_INDEX_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


# ── Subcommand: create-work-order ────────────────────────────────────

def cmd_create_work_order(draft_path):
    """Validate a filled draft and print preview (NO API call in v0.19.x)."""
    if not os.path.exists(draft_path):
        print(f"  ❌ Draft file not found: {draft_path}")
        return

    with open(draft_path, "r", encoding="utf-8") as f:
        text = f.read()

    # Extract metadata
    draft_id = "unknown"
    m = re.search(r'\*\*Draft ID:\*\*\s*(.+)', text)
    if m: draft_id = m.group(1).strip()

    # Check status — reject if already processed
    status = "created"
    m = re.search(r'_draft_status:\s*(.+)_', text)
    if m: status = m.group(1).strip()
    if status != "created":
        print(f"  ❌ Draft {draft_id} already processed (status: {status})")
        return

    # Check approval
    approved = bool(re.search(r'-\s*\[x\]\s*approve_create_work_order', text, re.IGNORECASE))
    edit_req = bool(re.search(r'-\s*\[x\]\s*edit_required', text, re.IGNORECASE))
    dismissed = bool(re.search(r'-\s*\[x\]\s*dismiss', text, re.IGNORECASE))

    if dismissed:
        print(f"  ⏭️  Draft {draft_id} marked as dismissed — nothing to create")
        return

    if not approved:
        print(f"  ❌ Draft {draft_id} not approved. Please check [x] approve_create_work_order.")
        return

    if edit_req:
        print(f"  ℹ️  Draft {draft_id} marked 'edit_required' — please revise and re-submit.")
        return

    # Check required fields
    missing = []
    field_values = {}
    for field_name, field_label in [
        ("Suggested Task Type", "suggested_task_type"),
        ("Proposed Prompt", "proposed_prompt"),
        ("Expected Output", "expected_output"),
    ]:
        m = re.search(rf'\*\*{field_name}:\*\*\s*```\s*(.*?)\s*```', text, re.DOTALL)
        if m:
            value = m.group(1).strip()
            field_values[field_label] = value
            if not value or "TODO" in value:
                missing.append(field_label)
        else:
            field_values[field_label] = ""
            missing.append(field_label)

    if missing:
        print(f"  ❌ Draft {draft_id} is incomplete. Missing required fields:")
        for f in missing:
            print(f"     - {f}")
        print(f"  Please fill required fields before creating Work Order.")
        return

    # All checks passed — print preview (NO API call in v0.19.x)
    print(f"  ✅ Draft {draft_id} validated. Ready to create Work Order.")
    print(f"")
    print(f"  📋 Preview:")
    print(f"     Draft ID:       {draft_id}")
    print(f"     Risk Level:     medium")
    print(f"     Task Type:      {field_values.get('suggested_task_type', '—')[:40]}")
    print(f"     Prompt:         {field_values.get('proposed_prompt', '—')[:60]}...")
    print(f"     Expected:       {field_values.get('expected_output', '—')[:60]}...")
    print(f"")
    print(f"  ⚠️  API integration is not available in v0.19.x.")
    print(f"  To actually create this Work Order, use the API directly or wait for v0.20.")
    print(f"")

    # Update draft status to 'ready' (not 'created' — the API hasn't been called)
    new_status = "_draft_status: ready_\n"
    text = re.sub(r'_draft_status:.*', '', text)
    text += new_status
    with open(draft_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"  ✏️  Draft status updated to: ready")
    _update_draft_index()


# ── Subcommand: status ────────────────────────────────────────────────

def cmd_status():
    """Show overview of all Briefs and their review statuses."""
    briefs = scan_all_briefs()
    if not briefs:
        print("  ℹ️  No Briefs found")
        return

    print(f"  📊 CEO Brief Overview — {len(briefs)} Brief(s)")
    print()
    print(f"  {'Date':<14} {'Type':<35} {'WOs':<5} {'Status':<22} {'Review'}")
    print(f"  {'─'*14} {'─'*35} {'─'*5} {'─'*22} {'─'*30}")

    for b in briefs:
        wo_info = f"{b['completed_count']}/{b['work_orders_count']}" if b['work_orders_count'] else "0/0"
        icon = status_icon(b['review_status'])
        status_str = f"{icon} {b['review_status']}"
        review_path = b.get('review_path', '')
        print(f"  {b['date']:<14} {b['brief_type'][:33]:<35} {wo_info:<5} {status_str:<22} {review_path}")

    print()

    # Count by status
    from collections import Counter
    counts = Counter(b['review_status'] for b in briefs)
    status_labels = {
        "pending_review": "🟡 Pending Review",
        "review_generated": "🟢 Review Ready",
        "reviewed": "✅ Reviewed",
        "no_decision_items": "ℹ️ No Decisions Needed",
        "invalid_review": "🔴 Invalid Review",
    }
    for status, label in status_labels.items():
        if counts.get(status, 0) > 0:
            print(f"    {label}: {counts[status]}")

    # Pending actions for the user
    pending = [b for b in briefs if b['review_status'] == 'pending_review' and b['has_decision_items']]
    if pending:
        print()
        print(f"  ⚠️  {len(pending)} Brief(s) need review:")
        for b in pending:
            print(f"     → python3 scripts/review_brief.py review {b['brief_path']}")

    ready = [b for b in briefs if b['review_status'] == 'review_generated']
    if ready:
        print()
        print(f"  ✅ {len(ready)} Brief(s) have review templates generated, awaiting your decision:")
        for b in ready:
            print(f"     → Editor: python3 scripts/review_brief.py decide {b['review_path']}")

    invalid = [b for b in briefs if b['review_status'] == 'invalid_review']
    if invalid:
        print()
        print(f"  🔴 {len(invalid)} Brief(s) have invalid reviews (multiple decisions checked):")
        for b in invalid:
            print(f"     → open {b['review_path']} and fix conflicts, then re-run decide")


# ── Main ──────────────────────────────────────────────────────────────

def print_usage():
    print(__doc__)
    print("Usage:")
    print("  python3 scripts/review_brief.py index")
    print("  python3 scripts/review_brief.py review <brief-path>")
    print("  python3 scripts/review_brief.py decide <review-path>")
    print("  python3 scripts/review_brief.py create-work-order <draft-path>")
    print("  python3 scripts/review_brief.py status")
    print()
    print("Examples:")
    print("  python3 scripts/review_brief.py index")
    print('  python3 scripts/review_brief.py review reports/ceo-briefs/2026-05-30.md')
    print('  python3 scripts/review_brief.py decide reports/ceo-brief-reviews/2026-05-30-review.md')
    print('  python3 scripts/review_brief.py create-work-order reports/work-order-drafts/WO-DRAFT-20260530-001.md')
    print("  python3 scripts/review_brief.py status")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_usage()
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "index":
        cmd_index()
    elif cmd == "review":
        if len(sys.argv) < 3:
            print("  ❌ Usage: python3 scripts/review_brief.py review <brief-path>")
            sys.exit(1)
        cmd_review(sys.argv[2])
    elif cmd == "decide":
        if len(sys.argv) < 3:
            print("  ❌ Usage: python3 scripts/review_brief.py decide <review-path>")
            sys.exit(1)
        cmd_decide(sys.argv[2])
    elif cmd == "create-work-order":
        if len(sys.argv) < 3:
            print("  ❌ Usage: python3 scripts/review_brief.py create-work-order <draft-path>")
            sys.exit(1)
        cmd_create_work_order(sys.argv[2])
    elif cmd == "status":
        cmd_status()
    else:
        print(f"  ❌ Unknown command: {cmd}")
        print_usage()
        sys.exit(1)
