#!/usr/bin/env python3
"""
v0.30 — Workflow Helpers: shared utilities for workflow_runner.py.

Provides template loading, ID generation, Run Ledger access, Asset Registry access.
"""

import json
import os
import sys
import yaml
from datetime import datetime
from typing import Optional

# ── Paths ─────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
_TEMPLATES_DIR = os.path.join(_SCRIPT_DIR, "templates")

# Backend path for DB access
_BACKEND_DIR = os.path.join(_PROJECT_ROOT, "backend")
if os.path.isdir(_BACKEND_DIR):
    sys.path.insert(0, _BACKEND_DIR)


# ── Template Loading ──────────────────────────────────────────

def load_template(template_name: str) -> dict:
    """Load a workflow template YAML file.

    Returns:
        dict with keys: workflow, steps

    Raises:
        FileNotFoundError: template not found
        yaml.YAMLError: invalid YAML
    """
    path = os.path.join(_TEMPLATES_DIR, f"{template_name}.yaml")
    if not os.path.exists(path):
        raise FileNotFoundError(f"Template not found: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)


def list_templates() -> list[str]:
    """List available template names (without .yaml extension)."""
    if not os.path.isdir(_TEMPLATES_DIR):
        return []
    return sorted(
        f.replace(".yaml", "")
        for f in os.listdir(_TEMPLATES_DIR)
        if f.endswith(".yaml")
    )


# ── ID Generation ─────────────────────────────────────────────

_WORKFLOW_COUNTER_FILE = os.path.join(
    _PROJECT_ROOT, "reports", "workflow-counter.json"
)


def generate_workflow_id() -> str:
    """Generate a unique workflow ID: WF-YYYYMMDD-NNN."""
    date_part = datetime.now().strftime("%Y%m%d")
    counter = 1
    if os.path.exists(_WORKFLOW_COUNTER_FILE):
        try:
            with open(_WORKFLOW_COUNTER_FILE, "r") as f:
                data = json.load(f)
            today_data = data.get(date_part, 0)
            counter = today_data + 1
        except (json.JSONDecodeError, KeyError):
            counter = 1

    os.makedirs(os.path.dirname(_WORKFLOW_COUNTER_FILE), exist_ok=True)
    with open(_WORKFLOW_COUNTER_FILE, "w") as f:
        json.dump({date_part: counter}, f)

    return f"WF-{date_part}-{counter:03d}"


def generate_draft_id() -> str:
    """Generate a Draft ID: WO-DRAFT-YYYYMMDD-NNN."""
    date_part = datetime.now().strftime("%Y%m%d")
    drafts_dir = os.path.join(_PROJECT_ROOT, "reports", "work-order-drafts")
    existing = []
    if os.path.isdir(drafts_dir):
        existing = [
            f for f in os.listdir(drafts_dir)
            if f.startswith("WO-DRAFT-") and f.endswith(".md")
        ]
    next_idx = len(existing) + 1
    return f"WO-DRAFT-{date_part}-{next_idx:03d}"


# ── Run Ledger ────────────────────────────────────────────────

def _get_run_ledger_service():
    """Lazy-import the Run Ledger service."""
    from app.services.run_ledger_service import record_event
    return record_event


def record_ledger_event(
    event_type: str,
    source_type: str = "workflow_cli",
    source_id: str = "",
    summary: str = "",
    metadata: Optional[dict] = None,
) -> Optional[dict]:
    """Record an event in Run Ledger.

    Returns the event dict on success, None if DB unavailable.
    """
    try:
        record_event = _get_run_ledger_service()
        result = record_event(
            event_type=event_type,
            source_type=source_type,
            source_id=source_id,
            summary=summary,
            metadata=metadata or {},
        )
        return result
    except Exception as e:
        print(f"  ⚠️  Run Ledger unavailable: {e}")
        return None


def record_and_register_asset(
    event_type: str,
    source_type: str = "workflow_cli",
    source_id: str = "",
    summary: str = "",
    asset_type: Optional[str] = None,
    path: Optional[str] = None,
    metadata: Optional[dict] = None,
) -> Optional[dict]:
    """Record event + register asset in one call."""
    try:
        from app.services.run_ledger_service import record_and_register
        result = record_and_register(
            event_type=event_type,
            asset_type=asset_type or "",
            source_type=source_type,
            source_id=source_id,
            path=path or source_id,
            summary=summary,
            metadata=metadata or {},
        )
        return result
    except Exception as e:
        print(f"  ⚠️  Run Ledger/Asset Registry unavailable: {e}")
        return None


# ── Asset Registry ────────────────────────────────────────────

def query_asset_by_source(source_work_order: str, asset_type: str) -> Optional[dict]:
    """Query Asset Registry by source work order and asset type.

    Returns first matching asset dict, or None.
    """
    try:
        from app.database import get_sync_session
        from app.models.asset_record import AssetRecord

        session = get_sync_session()
        asset = (
            session.query(AssetRecord)
            .filter(
                AssetRecord.source_work_order == source_work_order,
                AssetRecord.asset_type == asset_type,
            )
            .first()
        )
        if asset:
            return {
                "asset_id": asset.asset_id,
                "asset_type": asset.asset_type,
                "summary": asset.summary,
                "path": asset.path,
            }
        return None
    except Exception:
        return None


# ── Draft Generation ──────────────────────────────────────────

_DRAFTS_DIR = os.path.join(_PROJECT_ROOT, "reports", "work-order-drafts")


def write_draft_with_front_matter(
    draft_id: str,
    workflow_id: str,
    step_id: str,
    template_name: str,
    step_index: int,
    total_steps: int,
    depends_on: list,
    outputs: list,
    body: str,
) -> str:
    """Write a Draft file with YAML front matter for workflow tracking.

    Args:
        draft_id: Draft file name (without extension)
        workflow_id: Parent workflow ID
        step_id: Step ID this draft belongs to
        template_name: Template name
        step_index: 0-based step index
        total_steps: Total steps in workflow
        depends_on: List of dependency step IDs
        outputs: List of output asset declarations
        body: Markdown body content

    Returns:
        Absolute path to the written draft file
    """
    os.makedirs(_DRAFTS_DIR, exist_ok=True)

    # Build front matter
    depends_yaml = yaml.dump(depends_on, default_flow_style=False).strip() if depends_on else "[]"
    outputs_yaml = yaml.dump(outputs, default_flow_style=False).strip()

    front_matter = f"""---
workflow_id: {workflow_id}
workflow_step_id: {step_id}
workflow_template: {template_name}
step_index: {step_index}
total_steps: {total_steps}
depends_on:
{depends_yaml}
outputs:
{outputs_yaml}
---

"""

    draft_content = front_matter + body
    draft_path = os.path.join(_DRAFTS_DIR, f"{draft_id}.md")
    with open(draft_path, "w", encoding="utf-8") as f:
        f.write(draft_content)

    return draft_path


def read_draft_metadata(draft_path: str) -> Optional[dict]:
    """Read workflow metadata from a Draft file's front matter.

    Returns dict with workflow_id, step_id, etc., or None if not parseable.
    """
    try:
        with open(draft_path, "r") as f:
            content = f.read()
        if not content.startswith("---"):
            return None
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None
        return yaml.safe_load(parts[1])
    except Exception:
        return None
