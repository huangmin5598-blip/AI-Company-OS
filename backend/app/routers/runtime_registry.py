# @PRODUCT Router — OS Core
import json
from fastapi import APIRouter, HTTPException
from app.database import get_sync_session
from app.models.runtime_registry import RuntimeRegistry
from app.models.runtime_heartbeat import RuntimeHeartbeat
from app.runtime.registry import get_instantiated_adapters, get_all_runtime_adapters

router = APIRouter(prefix="/api/v1/runtimes", tags=["runtimes"])


def _serialize_reg(r):
    return {
        "runtime_id": r.runtime_id,
        "runtime_type": r.runtime_type,
        "display_name": r.display_name,
        "adapter_module": r.adapter_module,
        "endpoint": r.endpoint,
        "enabled": bool(r.enabled),
        "created_at": str(r.created_at),
        "updated_at": str(r.updated_at),
    }


@router.get("")
async def list_runtimes():
    """List all registered runtimes with latest heartbeat."""
    session = get_sync_session()
    try:
        runtimes = session.query(RuntimeRegistry).all()
        result = []
        for r in runtimes:
            reg = _serialize_reg(r)
            # Attach latest heartbeat
            hb = session.query(RuntimeHeartbeat).filter_by(
                runtime_id=r.runtime_id
            ).order_by(RuntimeHeartbeat.checked_at.desc()).first()
            if hb:
                reg["latest_heartbeat"] = {
                    "status": hb.status,
                    "checked_at": str(hb.checked_at),
                    "latency_ms": hb.latency_ms,
                }
            else:
                reg["latest_heartbeat"] = None
            result.append(reg)
        return {"runtimes": result}
    finally:
        session.close()


@router.post("/refresh")
async def refresh_all():
    """Force health check on all registered runtimes.
    Calls runtime_probe.collect directly (方案 B, per GPT review).
    """
    from app.monitor.probes.runtime_probe import collect
    results = await collect({})
    return {"runtimes": results}


@router.get("/{runtime_id}")
async def get_runtime(runtime_id: str):
    session = get_sync_session()
    try:
        r = session.query(RuntimeRegistry).filter_by(runtime_id=runtime_id).first()
        if not r:
            raise HTTPException(status_code=404, detail=f"Runtime '{runtime_id}' not found")
        return _serialize_reg(r)
    finally:
        session.close()


@router.get("/{runtime_id}/heartbeats")
async def get_heartbeats(runtime_id: str, limit: int = 20):
    session = get_sync_session()
    try:
        hbs = session.query(RuntimeHeartbeat).filter_by(
            runtime_id=runtime_id
        ).order_by(RuntimeHeartbeat.checked_at.desc()).limit(limit).all()
        return {"heartbeats": [
            {"status": h.status, "message": h.message,
             "latency_ms": h.latency_ms, "checked_at": str(h.checked_at)}
            for h in hbs
        ]}
    finally:
        session.close()


@router.get("/{runtime_id}/capabilities")
async def get_capabilities(runtime_id: str):
    adapters = get_instantiated_adapters()
    for a in adapters:
        if a.runtime_id == runtime_id:
            caps = await a.get_capabilities()
            return {"runtime_id": runtime_id, "capabilities": caps}
    raise HTTPException(status_code=404, detail=f"Runtime '{runtime_id}' not found or not instantiable")
