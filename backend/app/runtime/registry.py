# @PRODUCT Runtime registry — OS Core
"""
Runtime registry for RuntimeAdapter Protocol.

Holds all registered runtime adapters. v0.5 starts empty;
v0.6+ adds multi-runtime registration via config/company-instance.yaml.
"""

from app.runtime.protocol import RuntimeAdapter

_adapters: list[RuntimeAdapter] = []


def register_runtime_adapter(adapter: RuntimeAdapter) -> None:
    """Register a runtime adapter for health checks and execution."""
    _adapters.append(adapter)


def get_all_runtime_adapters() -> list[RuntimeAdapter]:
    """Return all registered runtime adapters. May be empty."""
    return list(_adapters)
