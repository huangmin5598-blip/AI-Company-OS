#!/usr/bin/env python3
"""
AI Company OS — Memory Runner v0.46

管理 Company Memory 生命周期：创建候选项、列出、查看、审批、拒绝。

用法：
  python3 tools/memory/memory-runner.py create-candidate --type <type> --title <title> --source-kind <kind> --source-ref <ref>
  python3 tools/memory/memory-runner.py list
  python3 tools/memory/memory-runner.py show <memory_id>
  python3 tools/memory/memory-runner.py approve <memory_id>
  python3 tools/memory/memory-runner.py reject <memory_id> --reason <reason>
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CANDIDATES_DIR = os.path.join(BASE_DIR, "private", "memory", "candidates")
APPROVED_DIR = os.path.join(BASE_DIR, "private", "memory", "approved")
REJECTED_DIR = os.path.join(BASE_DIR, "private", "memory", "rejected")
GENERATED_DIR = os.path.join(BASE_DIR, "private", "memory", "context-packs", "generated")

VALID_TYPES = {
    "system_architecture": "SA",
    "founder_decision": "FD",
    "governance_rule": "GR",
    "runtime_lifecycle": "RL",
    "product_line_learning": "PL",
    "workflow_pattern": "WP",
    "market_signal": "MS",
    "asset_evidence": "AE",
    "customer_feedback": "CF",
}

APPROVE_REQUIRED_FIELDS = [
    "memory_id", "memory_type", "title", "status",
    "source_kind", "source_ref", "source_date",
    "view_a_stage", "view_b_layer", "sensitivity", "summary",
]


def _ensure_dirs():
    os.makedirs(CANDIDATES_DIR, exist_ok=True)
    os.makedirs(APPROVED_DIR, exist_ok=True)
    os.makedirs(REJECTED_DIR, exist_ok=True)
    os.makedirs(GENERATED_DIR, exist_ok=True)


def _gen_memory_id(memory_type):
    """生成 MEM-YYYYMMDD-{TYPE}-NNN"""
    abbr = VALID_TYPES.get(memory_type, "XX")
    today = datetime.now().strftime("%Y%m%d")
    prefix = f"MEM-{today}-{abbr}-"

    max_num = 0
    for dir_path in [CANDIDATES_DIR, APPROVED_DIR, REJECTED_DIR]:
        if not os.path.isdir(dir_path):
            continue
        for fname in os.listdir(dir_path):
            if fname.startswith(prefix) and fname.endswith(".md"):
                try:
                    num = int(fname[len(prefix):-3])
                    if num > max_num:
                        max_num = num
                except (ValueError, IndexError):
                    pass

    return f"{prefix}{max_num + 1:03d}"


def _parse_front_matter(path):
    """解析 front matter (--- 之间)，支持简单 list 解析"""
    if not os.path.exists(path):
        return None, f"file not found: {path}"

    with open(path, "r") as f:
        content = f.read()

    m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
    if not m:
        return None, "no front matter found"

    raw = m.group(1)
    fields = {}
    current_list_key = None

    for line in raw.strip().split("\n"):
        # 检查是否是列表项 (line starts with "  - ")
        list_match = re.match(r'^\s*-\s+(.+)$', line)
        if list_match and current_list_key:
            val = list_match.group(1).strip().strip("\"'")
            if not isinstance(fields.get(current_list_key), list):
                fields[current_list_key] = []
            fields[current_list_key].append(val)
            continue

        # 检查是否是 key: value 行
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            val = val.strip().strip("\"'")
            if val == "":
                # 可能是列表的开始，记录当前 key
                current_list_key = key
                fields[key] = []
            else:
                current_list_key = None
                if val.lower() == "true":
                    val = True
                elif val.lower() == "false":
                    val = False
                fields[key] = val
        else:
            current_list_key = None

    return fields, content


def _validate_front_matter(fields, required_fields):
    """校验 front matter 必填字段。返回 (errors, warnings)。"""
    errors = []
    warnings = []

    for field in required_fields:
        val = fields.get(field)
        if val is None or val == "" or val == []:
            errors.append(f"Missing required field: {field}")

    # 特殊校验：memory_type 是否有效
    mt = fields.get("memory_type", "")
    if mt and mt not in VALID_TYPES:
        warnings.append(f"Unknown memory_type: {mt}")

    return errors, warnings


def cmd_create_candidate(args):
    """创建记忆候选项"""
    _ensure_dirs()

    memory_id = _gen_memory_id(args.type)
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")
    today = datetime.now().strftime("%Y-%m-%d")

    content = f"""---
memory_id: {memory_id}
memory_type: {args.type}
title: {args.title}
status: candidate
source_kind: {args.source_kind}
source_ref: {args.source_ref}
source_date: {today}
view_a_stage: []
view_b_layer: []
sensitivity: L1
summary: |
  <!-- TODO: 补充 1-3 行摘要 -->
created_at: {now}
---

# {memory_id} — {args.title}

<!-- 在此补充正文内容。至少包含 summary、view_a_stage、view_b_layer 才能 approve -->

## Context

<!-- 此记忆产生的背景 -->

## Content

<!-- 核心内容 -->

## Relevance

<!-- 什么情况下此记忆应被纳入 Context Pack -->
"""

    filepath = os.path.join(CANDIDATES_DIR, f"{memory_id}.md")
    with open(filepath, "w") as f:
        f.write(content)

    print(f"✅ Memory candidate created: {memory_id}")
    print(f"   File: {filepath}")
    print(f"   Type: {args.type}")
    print(f"   Title: {args.title}")
    print(f"   Next: 编辑文件补充内容 → approve")


def cmd_list(args):
    """列出所有候选项"""
    _ensure_dirs()

    candidates = []
    if os.path.isdir(CANDIDATES_DIR):
        for fname in sorted(os.listdir(CANDIDATES_DIR)):
            if fname.endswith(".md"):
                fpath = os.path.join(CANDIDATES_DIR, fname)
                fields, _ = _parse_front_matter(fpath)
                if fields:
                    candidates.append(fields)

    if not candidates:
        print("📭 No memory candidates.")
        return

    print(f"Memory Candidates ({len(candidates)})")
    print("─" * 80)
    for c in candidates:
        title = c.get("title", "?")[:50]
        st = c.get("status", "?")
        sens = c.get("sensitivity", "L1")
        print(f"{c['memory_id']:<34} {sens:<6} {st:<12} {title}")
    print("─" * 80)


def cmd_show(args):
    """查看候选项内容（递归搜索 candidates / approved 子目录 / rejected）"""
    _ensure_dirs()

    # Search candidates top-level
    fpath = os.path.join(CANDIDATES_DIR, f"{args.memory_id}.md")
    if os.path.exists(fpath):
        with open(fpath, "r") as f:
            content = f.read()
        print(f"📄 {args.memory_id} (candidate)")
        print("─" * 60)
        print(content)
        return

    # Search approved subdirectories (type-based)
    if os.path.isdir(APPROVED_DIR):
        for root, dirs, files in os.walk(APPROVED_DIR):
            if f"{args.memory_id}.md" in files:
                fpath = os.path.join(root, f"{args.memory_id}.md")
                with open(fpath, "r") as f:
                    content = f.read()
                print(f"📄 {args.memory_id} (approved)")
                print("─" * 60)
                print(content)
                return

    # Search rejected
    fpath = os.path.join(REJECTED_DIR, f"{args.memory_id}.md")
    if os.path.exists(fpath):
        with open(fpath, "r") as f:
            content = f.read()
        print(f"📄 {args.memory_id} (rejected)")
        print("─" * 60)
        print(content)
        return

    print(f"❌ Memory not found: {args.memory_id}")
    sys.exit(1)


def cmd_approve(args):
    """审核通过候选项"""
    _ensure_dirs()

    fpath = os.path.join(CANDIDATES_DIR, f"{args.memory_id}.md")
    if not os.path.exists(fpath):
        print(f"❌ Candidate not found: {args.memory_id}")
        sys.exit(1)

    fields, content = _parse_front_matter(fpath)
    if fields is None:
        print(f"❌ {content}")
        sys.exit(1)

    # 校验必填字段
    errors, warnings = _validate_front_matter(fields, APPROVE_REQUIRED_FIELDS)
    if errors:
        print(f"❌ Cannot approve — missing required fields:")
        for e in errors:
            print(f"   • {e}")
        sys.exit(1)
    if warnings:
        print("⚠️  Warnings:")
        for w in warnings:
            print(f"   • {w}")

    # 更新 front matter
    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")
    updated = content.replace("status: candidate", f"status: approved")
    updated = updated.replace("created_at:", "approved_at: " + now + "\ncreated_at:")
    # Only add approved_at line if we couldn't find/replace
    if "status: approved" not in updated:
        # Fallback: manual replacement
        updated = content

    # 写入 approved 目录
    memory_type = fields.get("memory_type", "unknown")
    type_dir = os.path.join(APPROVED_DIR, memory_type)
    os.makedirs(type_dir, exist_ok=True)
    dest = os.path.join(type_dir, f"{args.memory_id}.md")

    with open(dest, "w") as f:
        f.write(updated)

    # 删除候选
    os.remove(fpath)

    print(f"✅ {args.memory_id}: approved → {memory_type}/")
    print(f"   File: {dest}")
    print(f"   Next: 使用 context-pack-template 生成 Context Pack")


def cmd_reject(args):
    """审核拒绝候选项"""
    _ensure_dirs()

    fpath = os.path.join(CANDIDATES_DIR, f"{args.memory_id}.md")
    if not os.path.exists(fpath):
        print(f"❌ Candidate not found: {args.memory_id}")
        sys.exit(1)

    with open(fpath, "r") as f:
        content = f.read()

    now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+08:00")

    # 追加拒绝信息到 front matter
    reject_block = f"\nrejected_by: founder\nrejected_at: {now}\nreject_reason: {args.reason}\n"
    # Insert before the closing ---
    if "status: candidate" in content:
        content = content.replace("status: candidate", f"status: rejected{reject_block}", 1)

    dest = os.path.join(REJECTED_DIR, f"{args.memory_id}.md")
    with open(dest, "w") as f:
        f.write(content)

    os.remove(fpath)

    print(f"🗑️  {args.memory_id}: rejected")
    print(f"   Reason: {args.reason}")
    print(f"   File: {dest}")


# ── main ──

def main():
    parser = argparse.ArgumentParser(
        description="AI Company OS — Memory Runner v0.46"
    )
    sub = parser.add_subparsers(dest="command")

    # create-candidate
    p_create = sub.add_parser("create-candidate", help="Create a memory candidate")
    p_create.add_argument("--type", required=True, choices=list(VALID_TYPES.keys()),
                          help="Memory type")
    p_create.add_argument("--title", required=True, help="Memory title")
    p_create.add_argument("--source-kind", required=True,
                          choices=["runtime_task", "founder_discussion",
                                   "architecture_doc", "product_experiment",
                                   "customer_feedback"],
                          help="Source type")
    p_create.add_argument("--source-ref", required=True, help="Source reference (task_id / path / identifier)")

    # list
    sub.add_parser("list", help="List memory candidates")

    # show
    p_show = sub.add_parser("show", help="Show memory content")
    p_show.add_argument("memory_id")

    # approve
    p_approve = sub.add_parser("approve", help="Approve a memory candidate")
    p_approve.add_argument("memory_id")

    # reject
    p_reject = sub.add_parser("reject", help="Reject a memory candidate")
    p_reject.add_argument("memory_id")
    p_reject.add_argument("--reason", required=True, help="Rejection reason")

    args = parser.parse_args()

    if args.command == "create-candidate":
        cmd_create_candidate(args)
    elif args.command == "list":
        cmd_list(args)
    elif args.command == "show":
        cmd_show(args)
    elif args.command == "approve":
        cmd_approve(args)
    elif args.command == "reject":
        cmd_reject(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
