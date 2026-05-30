#!/usr/bin/env python3
"""
v0.27 — Capability Boundary Check Tool

Check whether an agent is allowed to perform a given action,
based on config/capability-boundary.yaml.

Usage:
    python3 scripts/capability_boundary.py list
    python3 scripts/capability_boundary.py list --class forbidden
    python3 scripts/capability_boundary.py check --agent hermes-main --action status_query
    python3 scripts/capability_boundary.py check --agent ceo-cmd-interface --action create_work_order
    python3 scripts/capability_boundary.py check --agent hermes-main --action expose_sensitive_data --mode enforce
    python3 scripts/capability_boundary.py check --agent daily-operating-loop --action write_to_repo --mode enforce -q

Exit codes:
    0 — Allowed or advisory warning
    1 — Enforce mode: forbidden action
    2 — Configuration error (unknown agent, unknown action)
"""

import argparse
import os
import sys
import yaml


# ── Path setup ─────────────────────────────────────────────────────
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config", "capability-boundary.yaml")


# ── Config loader ──────────────────────────────────────────────────

def load_config(path: str = _CONFIG_PATH) -> dict:
    """Load capability-boundary.yaml."""
    if not os.path.exists(path):
        print(f"  ❌ Config not found: {path}", file=sys.stderr)
        sys.exit(2)
    with open(path, "r") as f:
        config = yaml.safe_load(f)
    if not config:
        print(f"  ❌ Empty config: {path}", file=sys.stderr)
        sys.exit(2)
    return config


def build_action_map(config: dict) -> dict:
    """Build inverse mapping: action_name -> class_label.
    
    class_label values: read_only, safe_output, approval_required,
                        elevated_write, forbidden
    """
    action_map = {}
    class_labels = {
        "read_only_actions": "read_only",
        "safe_output_actions": "safe_output",
        "approval_required_actions": "approval_required",
        "elevated_write_actions": "elevated_write",
        "forbidden_actions": "forbidden",
    }
    classes = config.get("action_classes", {})
    for yaml_key, label in class_labels.items():
        for action in classes.get(yaml_key, []):
            action_map[action] = label
    return action_map


# ── Check logic ────────────────────────────────────────────────────

def classify(action: str, action_map: dict) -> str:
    """Return the class label for an action, or 'unknown'."""
    return action_map.get(action, "unknown")


def is_action_allowed_for_agent(action_class: str, agent_config: dict) -> bool:
    """Check if this action class is in the agent's allowed_classes."""
    allowed = agent_config.get("allowed_classes", [])
    return action_class in allowed


def perform_check(
    agent_id: str,
    action: str,
    config: dict,
    action_map: dict,
    mode: str = "advisory",
    quiet: bool = False,
) -> int:
    """Run the boundary check. Returns exit code."""
    # ── Validate agent ──
    actors = config.get("actors", {})
    if agent_id not in actors:
        if not quiet:
            print(f"  ❌ Unknown agent: {agent_id}")
            print(f"  📋 Known agents: {', '.join(sorted(actors.keys()))}")
        return 2

    agent_cfg = actors[agent_id]

    # ── Classify action ──
    action_class = classify(action, action_map)

    if action_class == "unknown":
        if not quiet:
            print(f"  ⚠️  Unknown action: {action}")
            print(f"     Action not defined in capability-boundary.yaml")
        # Unknown actions are denied (fail safe)
        action_class = "unsafe_unknown"

    # ── Determine if allowed ──
    is_forbidden = action_class == "forbidden"
    is_allowed = is_action_allowed_for_agent(action_class, agent_cfg)

    # ── Results ──
    class_label_display = {
        "read_only": "read_only",
        "safe_output": "safe_output",
        "approval_required": "approval_required",
        "elevated_write": "elevated_write",
        "forbidden": "forbidden",
        "unsafe_unknown": "unknown",
    }.get(action_class, action_class)

    requires_approval = action_class in ("approval_required", "elevated_write")

    result = {
        "agent": agent_id,
        "action": action,
        "action_class": class_label_display,
        "allowed": is_allowed and not is_forbidden,
        "requires_founder_approval": requires_approval and not is_forbidden,
        "mode": mode,
    }

    if is_forbidden:
        result["allowed"] = False
        result["requires_founder_approval"] = False
        result["reason"] = "Action is classified as forbidden"

        if mode == "enforce":
            if not quiet:
                _print_result(result, verdict="🚫 BLOCKED")
            return 1  # Hard block
        else:
            if not quiet:
                _print_result(result, verdict="⚠️  WARNING (advisory)")
            return 0  # Warn only

    if is_allowed:
        result["reason"] = f"Agent is authorized for '{class_label_display}' actions"
        if not quiet:
            _print_result(result, verdict="✅ ALLOWED")
        return 0

    # Denied (not in agent's allowed_classes)
    result["reason"] = (
        f"Action '{action}' is '{class_label_display}', "
        f"but agent '{agent_id}' is not authorized for '{class_label_display}' actions"
    )
    result["allowed"] = False
    if not quiet:
        _print_result(result, verdict="⛔ DENIED")
    return 0  # Denied but not hard-blocked (only forbidden gets enforce block)


def _print_result(result: dict, verdict: str) -> None:
    """Print human-readable check result."""
    print(f"  Agent:  {result['agent']}")
    print(f"  Action: {result['action']}")
    print(f"  Class:  {result['action_class']}")
    print(f"  Mode:   {result['mode']}")
    print(f"  {verdict}")
    if result.get("reason"):
        print(f"  Reason: {result['reason']}")
    if result["requires_founder_approval"]:
        print(f"  ⚠️  Requires Founder approval")
    print()


# ── List command ───────────────────────────────────────────────────

def cmd_list(config: dict, action_map: dict, class_filter: str = "") -> None:
    """List all actions by class."""
    classes = config.get("action_classes", {})

    # Build reverse map: class_display_name -> actions
    class_order = [
        ("read_only_actions", "read_only"),
        ("safe_output_actions", "safe_output"),
        ("approval_required_actions", "approval_required"),
        ("elevated_write_actions", "elevated_write"),
        ("forbidden_actions", "forbidden"),
    ]

    print(f"{'='*60}")
    print(f"  Capability Boundary — Action Registry")
    print(f"  Mode: {config.get('mode', 'advisory')}")
    print(f"{'='*60}\n")

    total_actions = 0
    for yaml_key, display_name in class_order:
        actions = classes.get(yaml_key, [])
        if class_filter and class_filter != display_name:
            continue
        if not actions:
            continue
        icon = {
            "read_only": "📖",
            "safe_output": "📝",
            "approval_required": "🔒",
            "elevated_write": "🔑",
            "forbidden": "🚫",
        }.get(display_name, "•")
        print(f"  {icon} {display_name} ({len(actions)} actions)")
        for a in sorted(actions):
            print(f"    • {a}")
        print()
        total_actions += len(actions)

    print(f"  Total: {total_actions} actions in {len(class_order)} classes\n")

    # Actors
    print(f"{'='*60}")
    print(f"  Registered Actors ({len(config.get('actors', {}))})")
    print(f"{'='*60}\n")
    for agent_id, actor in sorted(config.get("actors", {}).items()):
        allowed = ", ".join(actor.get("allowed_classes", []))
        print(f"  {agent_id}: [{allowed}]")
        print(f"    {actor.get('description', '—')}")
        if actor.get("notes"):
            print(f"    Note: {actor['notes']}")
        print()


# ── Main ───────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Capability Boundary Check — v0.27",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # list
    list_p = sub.add_parser("list", help="List all actions by class")
    list_p.add_argument(
        "--class", dest="class_filter", default="",
        choices=["read_only", "safe_output", "approval_required",
                 "elevated_write", "forbidden"],
        help="Filter by action class",
    )

    # check
    check_p = sub.add_parser("check", help="Check if an action is allowed for an agent")
    check_p.add_argument("--agent", required=True, help="Agent ID")
    check_p.add_argument("--action", required=True, help="Action name")
    check_p.add_argument(
        "--mode", default="advisory", choices=["advisory", "enforce"],
        help="advisory = warn only (default), enforce = hard block on forbidden",
    )
    check_p.add_argument(
        "-q", "--quiet", action="store_true",
        help="Quiet mode — exit code only, no output",
    )

    args = parser.parse_args()

    # Load config
    config = load_config()
    action_map = build_action_map(config)

    if args.command == "list":
        cmd_list(config, action_map, class_filter=args.class_filter)
        sys.exit(0)
    elif args.command == "check":
        exit_code = perform_check(
            agent_id=args.agent,
            action=args.action,
            config=config,
            action_map=action_map,
            mode=args.mode,
            quiet=args.quiet,
        )
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
