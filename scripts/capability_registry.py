#!/usr/bin/env python3
"""
v0.24 — Capability Registry CLI

Usage:
    python3 scripts/capability_registry.py list
    python3 scripts/capability_registry.py show <agent_id>
    python3 scripts/capability_registry.py find <keyword>
    python3 scripts/capability_registry.py find-capability <capability_name>

Examples:
    python3 scripts/capability_registry.py list
    python3 scripts/capability_registry.py show research-agent
    python3 scripts/capability_registry.py find finance
    python3 scripts/capability_registry.py find-capability status_query
"""
import argparse
import os
import sys
import yaml

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
_CONFIG_PATH = os.path.join(_PROJECT_ROOT, "config", "capability-registry.yaml")


def _load():
    if not os.path.exists(_CONFIG_PATH):
        print(f"  ❌ Capability Registry not found: {_CONFIG_PATH}")
        sys.exit(1)
    with open(_CONFIG_PATH, "r") as f:
        data = yaml.safe_load(f)
    return data.get("agents", [])


def cmd_list():
    agents = _load()
    if not agents:
        print("  ℹ️  No agents registered")
        return

    print(f"  📋 Capability Registry — {len(agents)} Agent(s)")
    print()
    print(f"  {'Agent ID':<30} {'Role':<40} {'Runtime':<15} {'Risk':<10}")
    print(f"  {'─'*30} {'─'*40} {'─'*15} {'─'*10}")
    for a in agents:
        print(f"  {a['agent_id']:<30} {a.get('role',''):<40} {a.get('runtime',''):<15} {a.get('risk_level',''):<10}")
    print()


def cmd_show(agent_id: str):
    agents = _load()
    agent = next((a for a in agents if a["agent_id"] == agent_id), None)
    if not agent:
        print(f"  ❌ Agent not found: {agent_id}")
        print(f"  Use 'list' to see all agents")
        return

    print(f"\n  📄 {agent['agent_id']}")
    print(f"  {'=' * 50}")
    print(f"    Display Name:  {agent.get('display_name', '—')}")
    print(f"    Role:          {agent.get('role', '—')}")
    print(f"    Runtime:       {agent.get('runtime', '—')}")
    print(f"    Risk Level:    {agent.get('risk_level', '—')}")
    print(f"    Cost Class:    {agent.get('cost_class', '—')}")
    print(f"    Quality Class: {agent.get('quality_class', '—')}")
    print()

    caps = agent.get("capabilities", [])
    # Determine related skills compact display
    skills = agent.get("related_skills", [])
    if caps:
        print(f"    Capabilities:")
        for c in caps:
            print(f"      ✓ {c}")
        print()
    if skills:
        print(f"    Skills Registry:")
        for s in skills:
            print(f"      → {s}")
        print()

    boundaries = agent.get("boundaries", [])
    if boundaries:
        print(f"    Boundaries:")
        for b in boundaries:
            print(f"      ❌ {b}")
        print()

    workflows = agent.get("supported_workflows", [])
    if workflows:
        print(f"    Supported Workflows:")
        for w in workflows:
            print(f"      • {w}")
        print()

    projects = agent.get("supported_projects", [])
    if projects:
        print(f"    Supported Projects:")
        for p in projects:
            print(f"      • {p}")
        print()

    approved = agent.get("approval_required_actions", [])
    if approved:
        print(f"    Approval Required For:")
        for a in approved:
            print(f"      ⚠️  {a}")
        print()

    contract = agent.get("default_output_contract", "")
    if contract:
        print(f"    Default Output Contract:")
        print(f"      {contract}")
        print()


def cmd_find(keyword: str):
    agents = _load()
    matches = []
    keyword_lower = keyword.lower()
    for a in agents:
        searchable = (
            a.get("agent_id", "").lower()
            + " " + a.get("display_name", "").lower()
            + " " + a.get("role", "").lower()
            + " " + " ".join(a.get("capabilities", [])).lower()
            + " " + " ".join(a.get("supported_projects", [])).lower()
        )
        if keyword_lower in searchable:
            matches.append(a)

    if not matches:
        print(f"  ℹ️  No matches for '{keyword}'")
        return

    print(f"  🔍 Found {len(matches)} agent(s) matching '{keyword}':\n")
    for m in matches:
        caps_preview = ", ".join(m.get("capabilities", [])[:3])
        if len(m.get("capabilities", [])) > 3:
            caps_preview += "..."
        print(f"  [{m['agent_id']}] {m.get('role', '—')}")
        print(f"    Capabilities: {caps_preview}")
        print()


def cmd_find_capability(cap_name: str):
    agents = _load()
    matches = []
    cap_lower = cap_name.lower()
    for a in agents:
        for c in a.get("capabilities", []):
            if cap_lower in c.lower():
                matches.append(a)
                break

    if not matches:
        print(f"  ℹ️  No agent has capability matching '{cap_name}'")
        return

    print(f"  🔍 Agents with '{cap_name}' capability:\n")
    for m in matches:
        print(f"  [{m['agent_id']}] — {m.get('display_name', '—')}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="v0.24 — Capability Registry CLI"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("list", help="List all agents")
    show_p = subparsers.add_parser("show", help="Show agent details")
    show_p.add_argument("agent_id", help="Agent ID (e.g. research-agent)")

    find_p = subparsers.add_parser("find", help="Search agents by keyword")
    find_p.add_argument("keyword", help="Search keyword")

    find_cap_p = subparsers.add_parser("find-capability", help="Find agents by capability name")
    find_cap_p.add_argument("capability", help="Capability name (e.g. status_query)")

    args = parser.parse_args()

    if args.command == "list":
        cmd_list()
    elif args.command == "show":
        cmd_show(args.agent_id)
    elif args.command == "find":
        cmd_find(args.keyword)
    elif args.command == "find-capability":
        cmd_find_capability(args.capability)


if __name__ == "__main__":
    main()
