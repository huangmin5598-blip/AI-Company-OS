# @PRODUCT Adapter — OS Core
"""Adapter: sync cost data from gateway-lite JSON files."""
import json
import glob
from datetime import datetime
from pathlib import Path
from app.database import get_sync_session
from app.models.cost_snapshot import CostSnapshot
from app.config import settings
from app.adapters.ledger_adapter import get_batch_id

def now():
    return datetime.utcnow().isoformat() + "Z"

def sync_costs() -> dict:
    """Sync cost snapshots from gateway-lite JSON files."""
    session = get_sync_session()
    records = 0
    errors = []
    
    try:
        # 1. Sync from daily files
        daily_dir = Path(settings.GATEWAY_DAILY_DIR).expanduser().resolve()
        if daily_dir.exists():
            for fpath in sorted(glob.glob(str(daily_dir / "*.json"))):
                try:
                    with open(fpath) as f:
                        data = json.load(f)
                    date = data.get("date", Path(fpath).stem)
                    entries = data.get("entries", [])
                    for e in entries:
                        session.add(CostSnapshot(
                            date=date,
                            agent_id=e.get("agent_id", ""),
                            model=e.get("model", ""),
                            provider=e.get("provider", ""),
                            input_tokens=e.get("input_tokens", 0),
                            output_tokens=e.get("output_tokens", 0),
                            cost_usd=e.get("estimated_cost_usd", 0),
                            fallback_count=1 if e.get("fallback_triggered") else 0,
                            result_status=e.get("result_status", "unknown"),
                            task_hint=e.get("task_hint", ""),
                            created_at=now(),
                            data_source='real',
                            source_name='gateway_lite_daily',
                            source_path=str(fpath),
                            sync_batch_id=get_batch_id(),
                            last_synced_at=now(),
                        ))
                        records += 1
                except Exception as e:
                    errors.append(f"daily/{Path(fpath).name}: {e}")
        
        # 2. Sync from cost-view files (aggregate level)
        cost_dir = Path(settings.GATEWAY_COST_DIR).expanduser().resolve()
        if cost_dir.exists():
            cost_types = {
                "by-agent.json": "agent_id",
                "by-model.json": "model",
                "by-project.json": "project",
            }
            for fname, key_field in cost_types.items():
                fpath = cost_dir / fname
                if not fpath.exists():
                    continue
                try:
                    with open(fpath) as f:
                        data = json.load(f)
                    for entity_name, info in data.items():
                        if isinstance(info, dict):
                            session.add(CostSnapshot(
                                date="aggregate",
                                agent_id=entity_name if key_field == "agent_id" else info.get("agents", [None])[0] if isinstance(info.get("agents"), list) and info["agents"] else "",
                                model=entity_name if key_field == "model" else "",
                                provider="",
                                input_tokens=info.get("input_tokens", 0),
                                output_tokens=info.get("output_tokens", 0),
                                cost_usd=info.get("total_cost_usd", info.get("avg_cost_per_call", 0)),
                                fallback_count=info.get("fallback_count", 0),
                                result_status="aggregated",
                                task_hint=f"from {fname}",
                                created_at=now(),
                                data_source='real',
                                source_name=f'gateway_lite_{fname.removesuffix(".json")}',
                                source_path=str(fpath),
                                sync_batch_id=get_batch_id(),
                                last_synced_at=now(),
                            ))
                            records += 1
                except Exception as e:
                    errors.append(f"{fname}: {e}")
        
        session.commit()
        return {"status": "ok", "records": records, "errors": errors[:3]}
    except Exception as e:
        session.rollback()
        return {"status": "error", "error": str(e), "records": records}
    finally:
        session.close()
