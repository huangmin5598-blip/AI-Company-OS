# @PRODUCT Runtime registry — OS Core
"""Runtime registry — reads registered runtimes from DB and instantiates adapters."""

from app.database import get_sync_session
from app.models.runtime_registry import RuntimeRegistry


def get_all_runtime_adapters() -> list[dict]:
    """Return all enabled runtime registrations from DB."""
    session = get_sync_session()
    try:
        rows = session.query(RuntimeRegistry).filter_by(enabled=1).all()
        return [
            {
                "runtime_id": r.runtime_id,
                "runtime_type": r.runtime_type,
                "display_name": r.display_name,
                "adapter_module": r.adapter_module,
                "endpoint": r.endpoint,
                "enabled": bool(r.enabled),
            }
            for r in rows
        ]
    finally:
        session.close()


def instantiate_adapter(reg: dict):
    """Dynamically import and instantiate an adapter from its module path."""
    import importlib
    mod_path = reg["adapter_module"]
    mod = importlib.import_module(mod_path)
    return mod.create_adapter(reg)


def get_instantiated_adapters() -> list:
    """Return instantiated adapter objects for all enabled runtimes."""
    registrations = get_all_runtime_adapters()
    adapters = []
    for r in registrations:
        try:
            adapters.append(instantiate_adapter(r))
        except Exception as e:
            print(f"[registry] Failed to instantiate adapter for {r.get('runtime_id', '?')}: {e}")
    return adapters
