"""VS-001 local pilot package with a fail-closed import boundary."""

from __future__ import annotations

import sys


FORBIDDEN_STARTUP_MODULES = frozenset(
    {
        "app.main",
        "app.database",
        "app.runtime.seed_runtimes",
    }
)

loaded = FORBIDDEN_STARTUP_MODULES.intersection(sys.modules)
if loaded:
    raise RuntimeError(
        "pilot_forbidden_startup_module_loaded:" + ",".join(sorted(loaded))
    )


__all__ = ["FORBIDDEN_STARTUP_MODULES"]
