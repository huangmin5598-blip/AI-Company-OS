#!/usr/bin/env python3
"""
docs-frontmatter-add.py
OS 白名单脚本：为 markdown 文件添加 YAML frontmatter

Usage: python3 docs-frontmatter-add.py <target_file> <version> <status> <last_updated> [--dry-run]

Args:
  target_file: path to .md file
  version: e.g. v0.46.5
  status: e.g. Active
  last_updated: e.g. 2026-06-05
  --dry-run: simulate without writing
"""
import os
import sys
import re
import hashlib
import json

WORKSPACE = os.path.expanduser("~/projects/ai-company-os")

def sha256_file(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def add_frontmatter(file_path, version, status, last_updated, dry_run=False):
    """Add or update frontmatter in a markdown file."""
    
    # Security: only allow docs/ paths
    abs_path = os.path.abspath(file_path)
    rel_path = os.path.relpath(abs_path, WORKSPACE)
    
    # Check path safety
    allowed_prefixes = ["docs/architecture/", "docs/governance/"]
    is_allowed = any(rel_path.startswith(p) for p in allowed_prefixes)
    
    if not is_allowed:
        print(f"[docs-frontmatter-add] REJECTED: {rel_path} not in allowed paths", flush=True)
        return {"error": "path_not_allowed", "file": rel_path}
    
    # Check for path traversal
    if ".." in rel_path:
        print(f"[docs-frontmatter-add] REJECTED: path traversal detected", flush=True)
        return {"error": "path_traversal", "file": rel_path}
    
    # Read file
    try:
        with open(abs_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        print(f"[docs-frontmatter-add] ERROR: file not found: {rel_path}", flush=True)
        return {"error": "file_not_found", "file": rel_path}
    
    before_sha256 = sha256_file(abs_path)
    
    # Check existing frontmatter
    frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
    has_existing = frontmatter_match is not None
    
    new_frontmatter = f"""---
version: {version}
status: {status}
last_updated: {last_updated}
---"""
    
    # Check idempotency: if frontmatter already exists with same values
    if has_existing:
        fm_text = frontmatter_match.group(1)
        fm = {}
        for line in fm_text.split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                fm[key.strip()] = val.strip()
        
        if fm.get('version') == version and fm.get('status') == status and fm.get('last_updated') == last_updated:
            print(f"[docs-frontmatter-add] SKIP (idempotent): {rel_path} already has correct frontmatter", flush=True)
            return {
                "file": rel_path,
                "action": "skipped_idempotent",
                "current_has_frontmatter": True,
                "before_sha256": before_sha256,
                "proposed_after_sha256": before_sha256,
                "lines_would_change": 0,
                "frontmatter_to_add": {"version": version, "status": status, "last_updated": last_updated}
            }
        
        # Update existing frontmatter
        body = content[frontmatter_match.end():]
        new_content = new_frontmatter + body
        action = "would_update"
    else:
        # Add new frontmatter
        new_content = new_frontmatter + "\n" + content
        action = "would_add"
    
    # Calculate proposed after sha256
    proposed_after_sha256 = hashlib.sha256(new_content.encode()).hexdigest()
    
    result = {
        "file": rel_path,
        "action": action,
        "current_has_frontmatter": has_existing,
        "before_sha256": before_sha256,
        "proposed_after_sha256": proposed_after_sha256,
        "lines_would_change": len(new_content.split('\n')) - len(content.split('\n')),
        "frontmatter_to_add": {
            "version": version,
            "status": status,
            "last_updated": last_updated
        }
    }
    
    print(f"[docs-frontmatter-add] {action}: {rel_path}", flush=True)
    print(f"  before_sha256: {before_sha256[:16]}...", flush=True)
    print(f"  proposed_after_sha256: {proposed_after_sha256[:16]}...", flush=True)
    
    # Dry-run: don't write
    if dry_run:
        print(f"[docs-frontmatter-add] DRY-RUN: not writing file", flush=True)
        result["dry_run"] = True
        result["files_written"] = False
        return result
    
    # Actually write
    try:
        with open(abs_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        after_sha256 = sha256_file(abs_path)
        result["files_written"] = True
        result["after_sha256"] = after_sha256
        print(f"[docs-frontmatter-add] WRITTEN: {rel_path}", flush=True)
        return result
    except Exception as e:
        result["error"] = str(e)
        result["files_written"] = False
        return result

def main():
    # Parse args: target_file version status last_updated [--dry-run]
    if len(sys.argv) < 5:
        print("Usage: docs-frontmatter-add.py <target_file> <version> <status> <last_updated> [--dry-run]", flush=True)
        sys.exit(1)
    
    dry_run = "--dry-run" in sys.argv
    
    # Get target files from task args
    # In dry-run mode, we process all 5 files
    target_files = []
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg.startswith("docs/") and not arg.startswith("--"):
            target_files.append(arg)
        i += 1
    
    if not target_files:
        # Default 5 files
        target_files = [
            "docs/architecture/runtime-adapter-contract.md",
            "docs/architecture/agent-role-architecture.md",
            "docs/architecture/os-skill-dispatch-contract.md",
            "docs/governance/os-design-quality-gate.md",
            "docs/governance/prd-quality-gate.md"
        ]
    
    version = sys.argv[1] if not sys.argv[1].startswith("docs/") else "v0.46.5"
    status = "Active"
    last_updated = "2026-06-05"
    
    # Extract from args if provided differently
    for i, arg in enumerate(sys.argv):
        if arg in ["v0.46.5", "v0.47", "v0.48"]:
            version = arg
        elif arg in ["Active", "Draft", "Deprecated"]:
            status = arg
    
    results = []
    errors = []
    
    for target_file in target_files:
        # Make absolute path
        if not target_file.startswith('/'):
            abs_path = os.path.join(WORKSPACE, target_file)
        else:
            abs_path = target_file
        
        result = add_frontmatter(abs_path, version, status, last_updated, dry_run=dry_run)
        results.append(result)
        
        if "error" in result:
            errors.append(result)
    
    # Write outbox result
    outbox_path = os.path.join(WORKSPACE, "private/work-queue/outbox/WQ-B1-1A-001-dry-run-result.json")
    output = {
        "dry_run": dry_run,
        "files_written": False,
        "target_files_written": False,
        "outbox_result_written": True,
        "results": results,
        "summary": {
            "total": len(results),
            "would_add": sum(1 for r in results if r.get("action") == "would_add"),
            "would_update": sum(1 for r in results if r.get("action") == "would_update"),
            "skipped_idempotent": sum(1 for r in results if r.get("action") == "skipped_idempotent"),
            "errors": len(errors)
        }
    }
    
    with open(outbox_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"[docs-frontmatter-add] Dry-run result written to: {outbox_path}", flush=True)
    
    # Exit with error if any errors
    sys.exit(1 if errors else 0)

if __name__ == "__main__":
    main()
