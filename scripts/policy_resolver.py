#!/usr/bin/env python3
"""
v0.29 — Policy Resolver

Merge-reads 4 manifest/config files to produce a single policy decision:
  - config/capability-boundary.yaml   — action classification
  - config/capability-manifest.yaml   — actor capabilities (optional)
  - config/runtime-manifest.yaml      — runtime declarations (optional)
  - config/safe-output-policy.yaml    — output format & redaction rules (optional)

Usage (CLI):
    python3 scripts/policy_resolver.py resolve --actor hermes-main --action create_work_order
    python3 scripts/policy_resolver.py resolve --actor hermes-main --action expose_sensitive_data --mode enforce
    python3 scripts/policy_resolver.py resolve --actor ceo-cmd-interface --action status_query --output-type markdown_report

Import (library):
    from scripts.policy_resolver import resolve, load_all_configs

    decision = resolve(actor_id="hermes-main", action="create_work_order")
    # => {allowed, boundary_class, requires_founder_approval, safe_output_required, reason, sources}
"""

import argparse
import json
import os
import sys

# ── Paths ─────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))

_CONFIG_PATHS = {
    "capability_boundary": os.path.join(_PROJECT_ROOT, "config", "capability-boundary.yaml"),
    "capability_manifest": os.path.join(_PROJECT_ROOT, "config", "capability-manifest.yaml"),
    "runtime_manifest": os.path.join(_PROJECT_ROOT, "config", "runtime-manifest.yaml"),
    "safe_output_policy": os.path.join(_PROJECT_ROOT, "config", "safe-output-policy.yaml"),
}

# Allow optional backend path for Run Ledger
_BACKEND_DIR = os.path.join(_PROJECT_ROOT, "backend")
if os.path.isdir(_BACKEND_DIR):
    sys.path.insert(0, _BACKEND_DIR)


# ── Loaders ───────────────────────────────────────────────────

def _try_load_yaml(path: str) -> dict:
    """Load YAML or return empty dict if file missing."""
    import yaml
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        data = yaml.safe_load(f)
    return data if data else {}


def load_all_configs(cfg_paths: dict = None) -> dict:
    """Load all config files. Missing files return empty dicts."""
    if cfg_paths is None:
        cfg_paths = _CONFIG_PATHS
    return {key: _try_load_yaml(path) for key, path in cfg_paths.items()}


# ── Action Classification (from capability-boundary.yaml) ─────

_CLASS_LABELS = {
    "read_only_actions": "read_only",
    "safe_output_actions": "safe_output",
    "approval_required_actions": "approval_required",
    "elevated_write_actions": "elevated_write",
    "forbidden_actions": "forbidden",
}


def _build_action_map(boundary: dict) -> dict:
    """Build action_name -> class_label mapping."""
    action_map = {}
    classes = boundary.get("action_classes", {})
    for yaml_key, label in _CLASS_LABELS.items():
        for action in classes.get(yaml_key, []):
            action_map[action] = label
    return action_map


def _get_actor_boundary(boundary: dict, actor_id: str) -> dict:
    """Get an actor's boundary config, or empty dict if unknown."""
    actors = boundary.get("actors", {})
    return actors.get(actor_id, {})


def _get_safe_output_requirements(policy: dict, output_type: str) -> dict:
    """Get safe output requirements for a given output type."""
    for ot in policy.get("allowed_output_types", []):
        if ot.get("type") == output_type:
            return ot
    return {}


# ── Resolver ──────────────────────────────────────────────────

def resolve(
    actor_id: str,
    action: str,
    output_type: str = "",
    runtime_id: str = "",
    mode: str = "advisory",
    configs: dict = None,
) -> dict:
    """Resolve a policy decision for a given actor + action.

    Args:
        actor_id: The actor attempting the action
        action: The action name being attempted
        output_type: Optional — if provided, checks safe output policy
        runtime_id: Optional — if provided, checks runtime manifest
        mode: 'advisory' (warn only) or 'enforce' (block forbidden)
        configs: Optional pre-loaded configs dict (from load_all_configs)

    Returns:
        dict with keys:
            allowed, boundary_class, requires_founder_approval,
            safe_output_required, reason, verdict, sources
    """
    if configs is None:
        configs = load_all_configs()

    boundary = configs.get("capability_boundary", {})
    cap_manifest = configs.get("capability_manifest", {})
    safe_policy = configs.get("safe_output_policy", {})

    # 1. Build action map
    action_map = _build_action_map(boundary)
    action_class = action_map.get(action, "unknown")

    # 2. Get actor boundary config
    actor_cfg = _get_actor_boundary(boundary, actor_id)
    allowed_classes = actor_cfg.get("allowed_classes", [])

    # 3. Optional: get actor manifest entry for enrichment
    manifest_actor = None
    for actor in cap_manifest.get("actors", []):
        if actor.get("actor_id") == actor_id:
            manifest_actor = actor
            break

    # 4. Determine if allowed
    is_forbidden = action_class == "forbidden"
    in_allowed_class = action_class in allowed_classes

    # 5. Build result
    result = {
        "actor": actor_id,
        "action": action,
        "action_class": action_class,
        "mode": mode,
        "allowed": bool(in_allowed_class and not is_forbidden),
        "requires_founder_approval": False,
        "safe_output_required": False,
        "reason": "",
        "verdict": "",
        "sources": {},
    }

    # 6. Safe output requirements (if output_type provided)
    if output_type:
        safe_req = _get_safe_output_requirements(safe_policy, output_type)
        if safe_req:
            result["safe_output_required"] = safe_req.get("redact", False)
            result["sources"]["safe_output_policy"] = safe_req

    # 7. Manifest enrichment
    if manifest_actor:
        result["sources"]["capability_manifest"] = {
            "actor_type": manifest_actor.get("actor_type", ""),
            "boundary_profile": manifest_actor.get("boundary_profile", ""),
            "runtime_ref": manifest_actor.get("runtime_ref", ""),
            "capabilities": manifest_actor.get("capabilities", []),
            "approval_required_actions": manifest_actor.get("approval_required_actions", []),
        }
        # Check if this action is in the actor's approval_required_actions list
        if action in manifest_actor.get("approval_required_actions", []):
            result["requires_founder_approval"] = True

    # 8. founder_approval for approval_required and elevated_write classes
    if action_class in ("approval_required", "elevated_write") and not is_forbidden:
        result["requires_founder_approval"] = True

    # 9. Verdict
    if is_forbidden:
        result["allowed"] = False
        result["requires_founder_approval"] = False
        if mode == "enforce":
            result["verdict"] = "BLOCKED"
            result["reason"] = f"Action '{action}' is classified as forbidden"
        else:
            result["verdict"] = "WARNING (advisory)"
            result["reason"] = f"Action '{action}' is classified as forbidden — advisory mode"
    elif in_allowed_class:
        result["verdict"] = "ALLOWED"
        result["reason"] = f"Actor '{actor_id}' is authorized for '{action_class}' actions"
    else:
        result["verdict"] = "DENIED"
        result["reason"] = (
            f"Actor '{actor_id}' is not authorized for '{action_class}' actions. "
            f"Allowed classes: {allowed_classes}"
        )

    # 10. Sources reference
    result["sources"]["capability_boundary"] = {
        "action_class": action_class,
        "allowed_classes": allowed_classes,
    }

    return result


# ── Check + Record (for integration into entry points) ────────

def check_and_record(
    actor_id: str,
    action: str,
    output_type: str = "",
    runtime_id: str = "",
    mode: str = "advisory",
    source_id: str = "",
    summary: str = "",
    configs: dict = None,
    record: bool = True,
) -> dict:
    """Resolve a policy decision and optionally record it in Run Ledger.

    Returns the decision dict. Caller should check decision['verdict']
    and respect 'BLOCKED' / 'DENIED' outcomes.
    """
    decision = resolve(
        actor_id=actor_id,
        action=action,
        output_type=output_type,
        runtime_id=runtime_id,
        mode=mode,
        configs=configs,
    )
    if not record:
        return decision

    # Determine event type based on verdict
    if decision["verdict"] == "ALLOWED":
        event_type = "policy_allowed"
    elif decision["verdict"] == "BLOCKED":
        event_type = "policy_blocked"
    elif decision["verdict"] == "WARNING (advisory)":
        event_type = "policy_blocked"  # forbidden in advisory also gets blocked record
    else:
        event_type = "policy_checked"

    try:
        from app.services.run_ledger_service import record_event
        record_event(
            event_type=event_type,
            source_type="policy",
            source_id=source_id or f"{actor_id}:{action}",
            actor=actor_id,
            summary=summary or decision.get("reason", ""),
            metadata={
                "action": action,
                "action_class": decision["action_class"],
                "verdict": decision["verdict"],
                "mode": mode,
                "requires_founder_approval": decision["requires_founder_approval"],
                "safe_output_required": decision["safe_output_required"],
            },
            skip_dupe=True,
        )
    except Exception:
        pass  # Don't fail the main operation if Run Ledger is unavailable

    return decision


# ── Safe Output Check ────────────────────────────────────────

_SENSITIVE_PATTERNS = [
    ("local_path", r"/Users/[^/]+/"),
    ("api_key", r"(?i)(api[_-]?key|token|secret)[\s]*[:=][\s]*['\"][^'\"]+['\"]"),
    ("env_var", r"(?i)^[A-Z_]+=.*"),
]


def safe_output_scan(text: str) -> dict:
    """Scan text for potential sensitive content.

    Returns:
        {
            "safe": bool,
            "violations": [{"pattern": str, "match": str, ...}],
            "suggestion": str
        }
    """
    import re
    violations = []
    for name, pattern in _SENSITIVE_PATTERNS:
        matches = re.findall(pattern, text)
        if matches:
            for m in matches[:3]:  # limit to 3 examples per pattern
                truncated = m[:60] + "..." if len(m) > 60 else m
                violations.append({"pattern": name, "match": truncated})

    return {
        "safe": len(violations) == 0,
        "violations": violations,
        "suggestion": "Text contains potential sensitive data. Consider redacting before use." if violations else "",
    }


def _print_result(r: dict) -> None:
    """Pretty-print a policy decision."""
    icon = {
        "ALLOWED": "✅",
        "WARNING (advisory)": "⚠️",
        "DENIED": "⛔",
        "BLOCKED": "🚫",
    }.get(r["verdict"], "•")
    print(f"\n{icon}  Policy Decision — {r['verdict']}")
    print(f"  {'='*50}")
    print(f"  Actor:   {r['actor']}")
    print(f"  Action:  {r['action']}")
    print(f"  Class:   {r['action_class']}")
    print(f"  Mode:    {r['mode']}")
    print(f"  {r['reason']}")
    if r["requires_founder_approval"]:
        print(f"  Requires Founder approval: YES")
    if r["safe_output_required"]:
        print(f"  Safe output required: YES")
    print()


# ── CLI ───────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Policy Resolver — v0.29",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    check_p = sub.add_parser("check", help="Check and record a policy decision in Run Ledger")
    check_p.add_argument("--actor", required=True, help="Actor ID")
    check_p.add_argument("--action", required=True, help="Action name")
    check_p.add_argument("--output-type", default="", help="Output type (for safe output check)")
    check_p.add_argument("--runtime", default="", help="Runtime ID (optional)")
    check_p.add_argument(
        "--mode", default="advisory", choices=["advisory", "enforce"],
        help="advisory = warn only, enforce = hard block on forbidden",
    )
    check_p.add_argument("--source-id", default="", help="Source reference ID (optional)")
    check_p.add_argument("--summary", default="", help="Human-readable summary (optional)")
    check_p.add_argument("--json", action="store_true", help="Output as JSON")
    check_p.add_argument("--skip-ledger", action="store_true", help="Skip Run Ledger recording")

    resolve_p = sub.add_parser("resolve", help="Resolve a policy decision (no Run Ledger)")
    resolve_p.add_argument("--actor", required=True, help="Actor ID")
    resolve_p.add_argument("--action", required=True, help="Action name")
    resolve_p.add_argument("--output-type", default="", help="Output type (for safe output check)")
    resolve_p.add_argument("--runtime", default="", help="Runtime ID (optional)")
    resolve_p.add_argument(
        "--mode", default="advisory", choices=["advisory", "enforce"],
        help="advisory = warn only, enforce = hard block on forbidden",
    )
    resolve_p.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.command == "resolve":
        configs = load_all_configs()
        decision = resolve(
            actor_id=args.actor,
            action=args.action,
            output_type=args.output_type,
            runtime_id=args.runtime,
            mode=args.mode,
            configs=configs,
        )
        if args.json:
            print(json.dumps(decision, indent=2, ensure_ascii=False))
        else:
            _print_result(decision)

        # Determine exit code
        if decision["verdict"] == "BLOCKED":
            sys.exit(1)
        sys.exit(0)

    elif args.command == "check":
        configs = load_all_configs()
        decision = check_and_record(
            actor_id=args.actor,
            action=args.action,
            output_type=args.output_type,
            runtime_id=args.runtime,
            mode=args.mode,
            source_id=args.source_id,
            summary=args.summary,
            configs=configs,
            record=not args.skip_ledger,
        )
        if args.json:
            print(json.dumps(decision, indent=2, ensure_ascii=False))
        else:
            _print_result(decision)

        # Determine exit code
        if decision["verdict"] == "BLOCKED":
            sys.exit(1)
        sys.exit(0)


if __name__ == "__main__":
    main()
