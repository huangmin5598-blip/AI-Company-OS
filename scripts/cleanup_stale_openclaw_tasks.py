#!/usr/bin/env python3
"""v0.17.2 — Stale OpenClaw Task Cleanup.

Scans working/ for stale tasks (older than STALE_AGE_HOURS)
and optionally archives them to ~/.ai-company-os/openclaw/archive/stale/.

Usage:
    python3 scripts/cleanup_stale_openclaw_tasks.py --dry-run
    python3 scripts/cleanup_stale_openclaw_tasks.py --archive
    python3 scripts/cleanup_stale_openclaw_tasks.py --archive --max-age 24

Options:
    --dry-run       Show stale tasks without moving anything (default).
    --archive       Move stale tasks to archive directory.
    --max-age HOURS Mark tasks older than HOURS as stale (default: 1).
"""

import argparse
import os
import shutil
import sys
import time
from datetime import datetime

_WORKING_DIR = os.path.expanduser("~/.ai-company-os/openclaw/working")
_ARCHIVE_BASE = os.path.expanduser("~/.ai-company-os/openclaw/archive/stale")
_DEFAULT_MAX_AGE_HOURS = 1  # Tasks in working > 1 hour are stale


def find_stale_tasks(max_age_hours: float) -> list[tuple[str, str, float]]:
    """Find stale task files in working/.

    Returns:
        List of (filename, full_path, age_hours) tuples sorted by age (oldest first).
    """
    if not os.path.isdir(_WORKING_DIR):
        return []

    now = time.time()
    stale = []
    for f in sorted(os.listdir(_WORKING_DIR)):
        if not f.endswith(".task.json"):
            continue
        path = os.path.join(_WORKING_DIR, f)
        age_seconds = now - os.path.getmtime(path)
        age_hours = age_seconds / 3600
        if age_hours > max_age_hours:
            stale.append((f, path, age_hours))
    return stale


def dry_run(max_age_hours: float):
    """Show stale tasks without moving anything."""
    stale = find_stale_tasks(max_age_hours)
    if not stale:
        print("✅ No stale tasks found in working/.")
        return True

    print(f"Found {len(stale)} stale task(s) (>{max_age_hours}h old) in working/:\n")
    for filename, path, age_hours in stale:
        wo_id = filename.replace(".task.json", "")
        mtime = datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M")
        print(f"  {wo_id}")
        print(f"    File:     {filename}")
        print(f"    Age:      {age_hours:.1f}h (since {mtime})")
        print()

    summary_path = os.path.join(_ARCHIVE_BASE, "..", "..", "SUMMARY.txt")
    print(f"Would archive {len(stale)} file(s) to: {_ARCHIVE_BASE}/YYYY-MM-DD/")
    print(f"  (use --archive to execute)")
    return True


def archive(max_age_hours: float):
    """Move stale tasks to archive directory."""
    stale = find_stale_tasks(max_age_hours)
    if not stale:
        print("✅ No stale tasks to archive.")
        return True

    # Create archive dir with today's date
    date_str = datetime.now().strftime("%Y-%m-%d")
    archive_dir = os.path.join(_ARCHIVE_BASE, date_str)
    os.makedirs(archive_dir, exist_ok=True)

    moved = 0
    errors = 0
    for filename, path, age_hours in stale:
        dest = os.path.join(archive_dir, filename)
        try:
            shutil.move(path, dest)
            moved += 1
            print(f"  📦 {filename.replace('.task.json','')} → archive/{date_str}/")
        except Exception as e:
            print(f"  ❌ {filename}: {e}")
            errors += 1

    # Write summary log after archive
    log_path = os.path.join(archive_dir, "_CLEANUP_LOG.txt")
    with open(log_path, "w") as f:
        f.write(f"Cleanup Run: {datetime.now().isoformat()}\n")
        f.write(f"Max Age: {max_age_hours}h\n")
        f.write(f"Moved: {moved}\n")
        f.write(f"Errors: {errors}\n")
        f.write("---\n")
        for filename, path, age_hours in stale:
            dest_path = os.path.join(archive_dir, filename)
            if os.path.exists(dest_path):
                mtime = datetime.fromtimestamp(os.path.getmtime(dest_path)).strftime("%Y-%m-%d %H:%M")
            else:
                mtime = "unknown"
            f.write(f"{filename} | age={age_hours:.1f}h | archived_at={mtime}\n")

    print(f"\n✅ Archived {moved} task(s) to {archive_dir}/")
    if errors:
        print(f"⚠️  {errors} error(s)")
    return True


def parse_args():
    parser = argparse.ArgumentParser(
        description="v0.17.2 — Stale OpenClaw Task Cleanup",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Show stale tasks without moving (default).")
    parser.add_argument("--archive", action="store_true",
                        help="Move stale tasks to archive directory.")
    parser.add_argument("--max-age", type=float, default=_DEFAULT_MAX_AGE_HOURS,
                        help="Mark tasks older than HOURS as stale (default: 1).")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()

    if args.archive:
        ok = archive(args.max_age)
    else:
        ok = dry_run(args.max_age)

    sys.exit(0 if ok else 1)
