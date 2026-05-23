#!/usr/bin/env python3
"""Cold start script for AI Company OS v0.2 — Alert→Task auto-pooling.

Runnable via: python scripts/cold_start_v0_2.py

Ensures tables exist, then runs the alert-to-task pooling logic.
"""
import sys
import os

# Ensure the backend root is on sys.path so imports resolve
backend_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

from app.database import init_db
from app.models import Alert, TaskPool, ContextPack, Approval
from app.routers.alert_to_task import _pool_unresolved_alerts


def main():
    print("=== Cold Start v0.2 ===")
    print("[1/2] Initializing database tables...")
    init_db()
    print("     Tables ready.")

    print("[2/2] Running Alert→Task pooling...")
    result = _pool_unresolved_alerts()

    pooled = result.get("pooled", 0)
    skipped = result.get("skipped", 0)
    errors = result.get("errors", [])

    print()
    print(f"  Tasks created:     {pooled}")
    print(f"  Context packs created (1:1 with tasks): {pooled}")
    print(f"  Approvals created  (1:1 with tasks):    {pooled}")
    print(f"  Alerts updated to resolved=2: {pooled}")
    print(f"  Skipped (already exist / resolved): {skipped}")

    if errors:
        print()
        print("  Errors encountered:")
        for err in errors:
            print(f"    - Alert {err.get('alert_id')}: {err.get('reason')}")

    print()
    print("=== Cold Start v0.2 Complete ===")
    print("=== Next: Start the frontend or manually trigger POST /api/v1/alert-to-task ===")


if __name__ == "__main__":
    main()
