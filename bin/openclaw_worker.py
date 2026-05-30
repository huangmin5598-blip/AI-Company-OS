#!/usr/bin/env python3
"""
OpenClaw Worker — Standalone CLI

Processes pending tasks in the OpenClaw inbox.

Usage:
    # Process one task (default)
    python3 bin/openclaw_worker.py

    # Process all pending tasks
    python3 bin/openclaw_worker.py --all

    # Process and call the backend callback API
    python3 bin/openclaw_worker.py --call-backend

    # Keep watching for new tasks (poll every 30s)
    python3 bin/openclaw_worker.py --watch

    # Custom backend URL
    python3 bin/openclaw_worker.py --call-backend --backend-url http://localhost:8001

    # Show help
    python3 bin/openclaw_worker.py --help
"""
import argparse
import os
import sys
import time

# Add backend to path
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.abspath(os.path.join(_SCRIPT_DIR, ".."))
_BACKEND_DIR = os.path.join(_PROJECT_ROOT, "backend")
sys.path.insert(0, _BACKEND_DIR)


def parse_args():
    parser = argparse.ArgumentParser(
        description="OpenClaw Worker — Process inbox tasks and write results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process ALL pending tasks (default: process one)",
    )
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Keep watching for new tasks (poll every N seconds)",
    )
    parser.add_argument(
        "--poll-interval",
        type=int,
        default=30,
        help="Poll interval in seconds (default: 30, used with --watch)",
    )
    parser.add_argument(
        "--call-backend",
        action="store_true",
        help="Call the backend callback API after execution",
    )
    parser.add_argument(
        "--backend-url",
        default="http://localhost:8001",
        help="Backend base URL (default: http://localhost:8001)",
    )
    return parser.parse_args()


def process_all(call_backend: bool, backend_url: str):
    """Process all pending tasks."""
    from app.services.openclaw_worker.worker import process_all_pending

    results = process_all_pending(call_backend=call_backend, backend_url=backend_url)

    completed = sum(1 for r in results if r["status"] == "completed")
    failed = sum(1 for r in results if r["status"] == "failed")

    print(f"\nWorker Summary: {len(results)} processed ({completed} completed, {failed} failed)")
    return results


def watch_loop(interval: int, call_backend: bool, backend_url: str):
    """Watch for new tasks in a loop."""
    from app.services.openclaw_worker.worker import process_all_pending

    print(f"Worker: Watching inbox every {interval}s... (Ctrl+C to stop)")
    try:
        while True:
            results = process_all_pending(call_backend=call_backend, backend_url=backend_url)
            if results:
                completed = sum(1 for r in results if r["status"] == "completed")
                failed = sum(1 for r in results if r["status"] == "failed")
                print(f"  → {len(results)} processed ({completed} ok, {failed} fail)")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\nWorker: Stopped")


def main():
    args = parse_args()

    print("=" * 50)
    print(" OpenClaw Worker v0.14")
    print("=" * 50)

    if args.watch:
        watch_loop(args.poll_interval, args.call_backend, args.backend_url)
    elif args.all:
        process_all(args.call_backend, args.backend_url)
    else:
        # Default: process one task
        from app.services.openclaw_worker.worker import find_pending_tasks, process_task

        pending = find_pending_tasks()
        if not pending:
            print("No pending tasks in inbox.")
            return

        print(f"Processing 1 task (of {len(pending)} pending)...")
        result = process_task(pending[0], call_backend=args.call_backend, backend_url=args.backend_url)
        print(f"Status: {result['status']}")


if __name__ == "__main__":
    main()
