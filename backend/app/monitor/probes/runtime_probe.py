# @PRODUCT Probe — OS Core
from app.runtime.registry import get_instantiated_adapters
from app.database import get_sync_session
from app.models.runtime_heartbeat import RuntimeHeartbeat
from datetime import datetime


async def collect(config: dict) -> list[dict]:
    """Check all registered runtimes via their adapters. Records heartbeats.

    Each adapter is isolated — one failure doesn't block others.
    Placeholder adapters (enabled=0) are skipped by get_instantiated_adapters().
    """
    adapters = get_instantiated_adapters()
    results = []
    session = get_sync_session()
    try:
        for adapter in adapters:
            try:
                status = await adapter.health_check()
                caps = await adapter.get_capabilities()
                latency = getattr(adapter, "latency_ms", 0)

                # Record heartbeat
                hb = RuntimeHeartbeat(
                    runtime_id=adapter.runtime_id,
                    status=status.value,
                    latency_ms=latency,
                    capabilities_count=len(caps),
                    checked_at=datetime.utcnow(),
                )
                session.add(hb)
                session.commit()

                results.append({
                    "runtime_id": adapter.runtime_id,
                    "name": adapter.name,
                    "type": adapter.runtime_type,
                    "status": status.value,
                    "latency_ms": latency,
                    "capabilities": caps,
                })
            except Exception as e:
                # Record heartbeat with error
                hb = RuntimeHeartbeat(
                    runtime_id=adapter.runtime_id,
                    status="unknown",
                    message=str(e),
                    checked_at=datetime.utcnow(),
                )
                session.add(hb)
                session.commit()
                results.append({
                    "runtime_id": getattr(adapter, "runtime_id", "unknown"),
                    "name": getattr(adapter, "name", "unknown"),
                    "type": getattr(adapter, "runtime_type", "unknown"),
                    "status": "unknown",
                    "error": str(e),
                })
        return results
    finally:
        session.close()
