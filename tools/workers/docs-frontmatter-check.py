#!/usr/bin/env python3
"""
docs-frontmatter-check.py
OS 白名单脚本：检查 docs/ 目录 markdown 文件的 frontmatter 一致性

Usage: python3 docs-frontmatter-check.py [target_paths...]
Default: docs/architecture/ docs/governance/
"""
import os
import sys
import re
import json
import hashlib

WORKSPACE = os.path.expanduser("~/projects/ai-company-os")

def check_frontmatter(file_path):
    """检查单个文件的 frontmatter"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        frontmatter_match = re.match(r'^---\n(.*?)\n---', content, re.DOTALL)
        if not frontmatter_match:
            return {"file": file_path, "status": "NO_FRONTMATTER", "missing": ["version", "status", "last_updated"]}
        
        fm_text = frontmatter_match.group(1)
        fm = {}
        for line in fm_text.split('\n'):
            if ':' in line:
                key, val = line.split(':', 1)
                fm[key.strip()] = val.strip()
        
        required = ["version", "status", "last_updated"]
        missing = [f for f in required if f not in fm]
        
        return {
            "file": file_path,
            "status": "PASS" if not missing else "WARNING",
            "missing": missing,
            "frontmatter": fm
        }
    except Exception as e:
        return {"file": file_path, "status": "ERROR", "error": str(e)}

def main():
    # Get target paths from args (relative to WORKSPACE)
    if len(sys.argv) > 1:
        target_paths = []
        for p in sys.argv[1:]:
            # If absolute, use as-is; if relative, join with WORKSPACE
            if p.startswith('/'):
                target_paths.append(p)
            else:
                target_paths.append(os.path.join(WORKSPACE, p))
    else:
        target_paths = [
            os.path.join(WORKSPACE, "docs/architecture/"),
            os.path.join(WORKSPACE, "docs/governance/")
        ]
    
    results = []
    all_files = []
    
    for target in target_paths:
        if not os.path.exists(target):
            print(f"[docs-frontmatter-check] WARNING: {target} not found, skipping", flush=True)
            continue
        
        if os.path.isfile(target):
            all_files.append(target)
        else:
            for root, dirs, files in os.walk(target):
                for file in files:
                    if file.endswith('.md'):
                        all_files.append(os.path.join(root, file))
    
    for file_path in all_files:
        result = check_frontmatter(file_path)
        results.append(result)
    
    pass_count = sum(1 for r in results if r["status"] == "PASS")
    warning_count = sum(1 for r in results if r["status"] == "WARNING")
    error_count = sum(1 for r in results if r["status"] == "ERROR")
    
    print(f"[docs-frontmatter-check] Scanned {len(all_files)} files", flush=True)
    print(f"[docs-frontmatter-check] Results: {pass_count} PASS, {warning_count} WARNING, {error_count} ERROR", flush=True)
    
    for r in results:
        if r["status"] != "PASS":
            print(f"[docs-frontmatter-check] {r['status']}: {r['file']}", flush=True)
            if "missing" in r:
                print(f"  Missing: {r['missing']}", flush=True)
    
    # Generate report
    report = {
        "summary": {
            "total": len(all_files),
            "pass": pass_count,
            "warning": warning_count,
            "error": error_count
        },
        "files": results
    }
    
    # Write to outbox
    outbox_path = os.path.join(WORKSPACE, "private/work-queue/outbox/WQ-B1-0-001-result.json")
    with open(outbox_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"[docs-frontmatter-check] Report written to: {outbox_path}", flush=True)
    return 0 if error_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main())
