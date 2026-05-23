# @PRODUCT Probe — OS Core
from app.runtime.registry import get_all_runtime_adapters


async def collect(config: dict) -> list[dict]:
    """Check runtime health via RuntimeAdapter Protocol.

    v0.5: Uses runtime registry. If no adapters registered, returns empty list.
    Full multi-runtime support comes in v0.6+.
    """
    adapters = get_all_runtime_adapters()
    results = []
    for adapter in adapters:
        try:
            status = await adapter.health_check()
            results.append({
                "name": adapter.name,
                "type": adapter.runtime_type,
                "status": status.value if hasattr(status, 'value') else str(status),
                "healthy": status.value == "online" if hasattr(status, 'value') else False,
            })
        except Exception as e:
            results.append({
                "name": getattr(adapter, 'name', 'unknown'),
                "type": getattr(adapter, 'runtime_type', 'unknown'),
                "status": "unreachable",
                "healthy": False,
                "error": str(e),
            })
    return results
