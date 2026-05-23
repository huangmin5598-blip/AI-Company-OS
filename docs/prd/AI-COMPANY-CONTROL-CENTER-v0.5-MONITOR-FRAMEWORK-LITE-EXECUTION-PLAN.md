# v0.5 Monitor Framework Lite — 执行计划

> **基于 PRD** `AI-COMPANY-CONTROL-CENTER-v0.5-MONITOR-FRAMEWORK-LITE-PRD.md`
> **预估工时**: 8-10h（Sprint A ~5h + Sprint B ~4h）
> **执行策略**: 先做核心链路（task/cost），再做扩展链路（execution/runtime），最后 API + 验收

---

## 执行概览

```
Sprint A (~5h) — Core Pipeline
├── Step 1: Config — monitor-rules.example.yaml (0.5h)
├── Step 2: Models — monitor_runs + monitor_findings (1h)
├── Step 3: Probes — task_probe + cost_probe (1.5h)
├── Step 4: Analyzers — stuck_task + cost_spike (1h)
├── Step 5: Outputs — finding + alert (1h)
└── Step 6: 验收 — Stuck Task + Cost Spike (auto)

Sprint B (~4h) — Extension + API
├── Step 7: Probes — execution_probe + runtime_probe (1h)
├── Step 8: Analyzers — error_rate (0.5h)
├── Step 9: Outputs — task draft (approval_required) (0.5h)
├── Step 10: APIs — 5 endpoints (1.5h)
└── Step 11: 全链路验收 (0.5h)
```

---

## Sprint A: Core Pipeline

### Step 0: Schema Reality Check

**Before writing any code, confirm these database facts:**

```python
# TaskPool status machine (from task_pool.py)
# draft → ready → approval_required → approved → running → review → done
# Monitorable statuses with threshold hours:
MONITORABLE_STATUSES = {
    "running": 2,
    "approval_required": 4,
    "review": 4,
}

# CostSnapshot has: cost_usd (Float, per-day), date (String), input_tokens, output_tokens
# NOT "total_cost" — use SUM(cost_usd) over time windows

# ExecutionRecord has: result (String — "success"/"failed"/"timeout"), NOT "status"
# review_status is for approval tracking, NOT execution result

# RuntimeAdapter registry: backend/app/runtime/registry.py (new in v0.5)
# import: from app.runtime.registry import get_all_runtime_adapters
```

### Step 1: Config

**文件**: `config/monitor-rules.example.yaml`

```yaml
monitor:
  enabled: true
  schedule: manual  # v0.5 only manual trigger

probes:
  task_probe:
    enabled: true
  cost_probe:
    enabled: true
  execution_probe:
    enabled: true
  runtime_probe:
    enabled: true

analyzers:
  stuck_task:
    enabled: true
    threshold_hours: 2
  cost_spike:
    enabled: true
    lookback_hours: 24
    spike_multiplier: 2.0
  error_rate:
    enabled: true
    lookback_runs: 20
    error_threshold: 0.3

outputs:
  create_alerts: true
  create_task_drafts: true  # only for critical
  requires_approval: true   # task drafts created as approval_required
```

### Step 2: Models

**新文件**: `backend/app/models/monitor_run.py`
**新文件**: `backend/app/models/monitor_finding.py`
**修改**: `backend/app/models/__init__.py`

#### monitor_run.py

```python
# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Text, DateTime, func
from app.models.base import Base


class MonitorRun(Base):
    """A single monitor scan execution record."""

    __tablename__ = "monitor_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime, nullable=False, default=func.now())
    finished_at = Column(DateTime)
    status = Column(String, nullable=False, default="running")
    # success / failed / partial
    summary = Column(Text)
    findings_count = Column(Integer, default=0)
    alerts_created = Column(Integer, default=0)
    tasks_created = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
```

#### monitor_finding.py

```python
# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, func
from app.models.base import Base


class MonitorFinding(Base):
    """A single finding from a monitor scan."""

    __tablename__ = "monitor_findings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    monitor_run_id = Column(Integer, ForeignKey("monitor_runs.id"), nullable=False)
    finding_type = Column(String, nullable=False, index=True)
    # stuck_task / cost_spike / error_rate / runtime_health
    severity = Column(String, nullable=False, default="info")
    # info / warning / critical
    title = Column(String, nullable=False)
    summary = Column(Text)
    evidence_json = Column(Text)
    # structured JSON evidence
    status = Column(String, nullable=False, default="open")
    # open / acknowledged / dismissed / converted
    source_id = Column(String)
    # e.g. "task:42", "cost:snapshot:5"
    alert_id = Column(Integer)
    task_id = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
```

### Step 3: Probes

**新目录**: `backend/app/monitor/`
**新文件**:
- `backend/app/monitor/__init__.py`
- `backend/app/monitor/probes/__init__.py`
- `backend/app/monitor/probes/task_probe.py`
- `backend/app/monitor/probes/cost_probe.py`

#### task_probe.py

```python
# @PRODUCT Probe — OS Core
from datetime import datetime, timedelta
from sqlalchemy import select
from app.database import SessionLocal
from app.models.task_pool import TaskPool

# Real statuses from task_pool.py
# draft → ready → approval_required → approved → running → review → done
MONITORABLE_STATUSES = {
    "running": 2,
    "approval_required": 4,
    "review": 4,
}


async def collect(config: dict) -> list[dict]:
    """Find tasks stuck beyond threshold per status."""
    results = []
    session = SessionLocal()
    try:
        for status, threshold_hours in MONITORABLE_STATUSES.items():
            cutoff = datetime.utcnow() - timedelta(hours=threshold_hours)
            rows = session.execute(
                select(TaskPool).where(
                    TaskPool.status == status,
                    TaskPool.updated_at < cutoff
                )
            ).scalars().all()

            for task in rows:
                hours = (datetime.utcnow() - task.updated_at).total_seconds() / 3600
                results.append({
                    "task_id": task.id,
                    "title": task.title,
                    "status": task.status,
                    "threshold_hours": threshold_hours,
                    "hours_since_update": round(hours, 1),
                })
        return results
    finally:
        session.close()
```

#### cost_probe.py

```python
# @PRODUCT Probe — OS Core
from datetime import datetime, timedelta
from sqlalchemy import select, func as sa_func
from app.database import SessionLocal
from app.models.cost_snapshot import CostSnapshot


async def collect(config: dict) -> dict | None:
    """Compare recent cost vs historical average using SUM(cost_usd) delta."""
    lookback_hours = config.get("analyzers", {}).get("cost_spike", {}).get("lookback_hours", 24)

    now = datetime.utcnow()
    recent_start = now - timedelta(hours=lookback_hours)
    historical_start = now - timedelta(hours=lookback_hours * 2)

    session = SessionLocal()
    try:
        # SUM(cost_usd) per period — cost_snapshots has per-day cost_usd records
        recent = session.execute(
            select(sa_func.sum(CostSnapshot.cost_usd)).where(
                CostSnapshot.created_at >= recent_start
            )
        ).scalar() or 0.0

        historical = session.execute(
            select(sa_func.sum(CostSnapshot.cost_usd)).where(
                CostSnapshot.created_at >= historical_start,
                CostSnapshot.created_at < recent_start
            )
        ).scalar() or 0.0

        multiplier = float(recent) / float(historical) if historical > 0 else 1.0

        return {
            "recent_period_cost": float(recent),
            "historical_period_cost": float(historical),
            "lookback_hours": lookback_hours,
            "multiplier": round(multiplier, 2),
        }
    finally:
        session.close()
```

### Step 4: Analyzers

**新文件**:
- `backend/app/monitor/analyzers/__init__.py`
- `backend/app/monitor/analyzers/stuck_task.py`
- `backend/app/monitor/analyzers/cost_spike.py`

#### stuck_task.py

```python
# @PRODUCT Analyzer — OS Core


def analyze(task_data: list[dict], config: dict) -> list[dict]:
    """Classify stuck tasks by severity."""
    threshold_hours = config.get("analyzers", {}).get("stuck_task", {}).get("threshold_hours", 2)

    findings = []
    for task in task_data:
        factor = task["hours_since_update"] / threshold_hours
        if factor < 1:
            continue  # Not stuck yet
        elif factor < 2:
            severity = "info"
        elif factor < 4:
            severity = "warning"
        else:
            severity = "critical"

        findings.append({
            "finding_type": "stuck_task",
            "severity": severity,
            "title": f"Stuck task: {task['title']}",
            "summary": f"Task #{task['task_id']} has been '{task['status']}' for "
                       f"{task['hours_since_update']:.1f}h (threshold: {threshold_hours}h).",
            "evidence_json": task,
            "source_id": f"task:{task['task_id']}",
        })

    return findings
```

#### cost_spike.py

```python
# @PRODUCT Analyzer — OS Core


def analyze(cost_data: dict | None, config: dict) -> list[dict]:
    """Detect cost spikes."""
    if cost_data is None:
        return []

    multiplier = cost_data["multiplier"]
    spike_threshold = config.get("analyzers", {}).get("cost_spike", {}).get("spike_multiplier", 2.0)

    if multiplier < 1.5:
        return []
    elif multiplier < spike_threshold:
        severity = "info"
    elif multiplier < spike_threshold * 1.5:
        severity = "warning"
    else:
        severity = "critical"

    return [{
        "finding_type": "cost_spike",
        "severity": severity,
        "title": f"Cost spike detected ({multiplier:.1f}x normal)",
        "summary": f"Recent cost ({cost_data['recent_period_cost']:.2f}) is "
                   f"{multiplier:.1f}x the historical average ({cost_data['historical_period_cost']:.2f}).",
        "evidence_json": cost_data,
        "source_id": None,
    }]
```

### Step 5: Outputs

**新文件**:
- `backend/app/monitor/outputs/__init__.py`
- `backend/app/monitor/outputs/alert_output.py`

#### alert_output.py

```python
# @PRODUCT Output — OS Core
import json

from app.database import SessionLocal
from app.models.monitor_finding import MonitorFinding
from app.models.alert import Alert
from app.models.task_pool import TaskPool


def process_findings(findings: list[dict], run_id: int, config: dict) -> dict:
    """Write findings to DB and create alerts/tasks based on severity config."""
    session = SessionLocal()
    try:
        alerts_created = 0
        tasks_created = 0
        create_task_drafts = config.get("outputs", {}).get("create_task_drafts", False)

        for f_data in findings:
            # Dedup: skip if same finding_type + source_id already has open finding
            if f_data.get("source_id"):
                existing = session.query(MonitorFinding).filter_by(
                    finding_type=f_data["finding_type"],
                    source_id=f_data["source_id"],
                    status="open",
                ).first()
                if existing:
                    continue

            finding = MonitorFinding(
                monitor_run_id=run_id,
                finding_type=f_data["finding_type"],
                severity=f_data["severity"],
                title=f_data["title"],
                summary=f_data.get("summary", ""),
                evidence_json=json.dumps(f_data.get("evidence_json", {}), ensure_ascii=False),
                source_id=f_data.get("source_id"),
                status="open",
            )
            session.add(finding)
            session.flush()

            # Create alert for warning+
            if f_data["severity"] in ("warning", "critical"):
                alert = Alert(
                    severity=f_data["severity"],
                    title=f"[Monitor] {f_data['title']}",
                    description=f_data.get("summary", ""),
                    source="monitor",
                    source_id=f"monitor_finding:{finding.id}",
                )
                session.add(alert)
                session.flush()
                alerts_created += 1

                # Create task draft only if config allows and severity is critical
                if f_data["severity"] == "critical" and create_task_drafts:
                    task = TaskPool(
                        title=f"Investigate: {f_data['title']}",
                        description=f"Monitor detected: {f_data.get('summary', '')}",
                        status="approval_required",
                        source="monitor",
                        source_id=f"monitor_finding:{finding.id}",
                    )
                    session.add(task)
                    session.flush()
                    tasks_created += 1

        session.commit()
        return {
            "findings_created": len(findings),
            "alerts_created": alerts_created,
            "tasks_created": tasks_created,
        }
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

### Step 6: Monitor Runner

**新文件**: `backend/app/monitor/runner.py`

```python
import json
import traceback
from datetime import datetime


async def run_monitor_scan(config: dict) -> dict:
    """Run a full monitor scan: collect → analyze → output.
    
    Each probe/analyzer is isolated — one failure doesn't block others.
    Final run.status is success / partial / failed.
    """
    from app.database import SessionLocal
    from app.models.monitor_run import MonitorRun

    # 1. Create run record
    session = SessionLocal()
    try:
        run = MonitorRun(status="running", started_at=datetime.utcnow())
        session.add(run)
        session.commit()
        run_id = run.id
    finally:
        session.close()

    all_findings = []
    errors = []

    # 2. Run probes + analyzers (each wrapped in try/except)
    if config.get("probes", {}).get("task_probe", {}).get("enabled", True):
        try:
            from app.monitor.probes.task_probe import collect as collect_tasks
            from app.monitor.analyzers.stuck_task import analyze as analyze_stuck
            task_data = await collect_tasks(config)
            all_findings.extend(analyze_stuck(task_data, config))
        except Exception as e:
            errors.append(f"task_probe: {e}")

    if config.get("probes", {}).get("cost_probe", {}).get("enabled", True):
        try:
            from app.monitor.probes.cost_probe import collect as collect_cost
            from app.monitor.analyzers.cost_spike import analyze as analyze_cost
            cost_data = await collect_cost(config)
            all_findings.extend(analyze_cost(cost_data, config))
        except Exception as e:
            errors.append(f"cost_probe: {e}")

    # 3. Write outputs
    output_result = {"findings_created": 0, "alerts_created": 0, "tasks_created": 0}
    if all_findings:
        try:
            from app.monitor.outputs.alert_output import process_findings
            output_result = process_findings(all_findings, run_id, config)
        except Exception as e:
            errors.append(f"outputs: {e}")

    # 4. Update run record — never leave it in "running"
    run_status = "failed" if not all_findings and errors else \
                 "partial" if errors else "success"

    session = SessionLocal()
    try:
        run = session.query(MonitorRun).filter_by(id=run_id).first()
        run.status = run_status
        run.finished_at = datetime.utcnow()
        run.summary = f"Found {len(all_findings)} issues. " + \
                      (f"Errors: {'; '.join(errors)}" if errors else "")
        run.findings_count = len(all_findings)
        run.alerts_created = output_result.get("alerts_created", 0)
        run.tasks_created = output_result.get("tasks_created", 0)
        session.commit()
    finally:
        session.close()

    return {
        "run_id": run_id,
        "status": run_status,
        "findings_count": len(all_findings),
        "alerts_created": output_result.get("alerts_created", 0),
        "tasks_created": output_result.get("tasks_created", 0),
    }
```

---

## Sprint B: Extension + API

### Step 7: Probes — execution_probe + runtime_probe

#### execution_probe.py

```python
# @PRODUCT Probe — OS Core
from app.database import SessionLocal
from app.models.execution_record import ExecutionRecord


async def collect(config: dict) -> dict:
    """Check recent execution failure rate using result field."""
    lookback = config.get("analyzers", {}).get("error_rate", {}).get("lookback_runs", 20)

    session = SessionLocal()
    try:
        records = session.query(ExecutionRecord).order_by(
            ExecutionRecord.id.desc()
        ).limit(lookback).all()

        total = len(records)
        failed_results = ("failed", "timeout")
        failed = sum(1 for r in records if r.result in failed_results)
        failed_reasons = [r.result for r in records if r.result in failed_results][:5]

        return {
            "total_runs": total,
            "failed_count": failed,
            "failure_rate": round(failed / total, 3) if total else 0.0,
            "sample_failures": failed_reasons,
        }
    finally:
        session.close()
```

#### runtime_probe.py

```python
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
```

### Step 8: Analyzer — error_rate

```python
# @PRODUCT Analyzer — OS Core


def analyze(execution_data: dict | None, config: dict) -> list[dict]:
    """Detect high error rates in recent executions."""
    if execution_data is None or execution_data["total_runs"] == 0:
        return []

    rate = execution_data["failure_rate"]
    threshold = config.get("analyzers", {}).get("error_rate", {}).get("error_threshold", 0.3)

    if rate < 0.1:
        return []
    elif rate < threshold:
        severity = "info"
    elif rate < threshold * 1.5:
        severity = "warning"
    else:
        severity = "critical"

    return [{
        "finding_type": "error_rate",
        "severity": severity,
        "title": f"High error rate: {rate:.1%}",
        "summary": f"{execution_data['failed_count']} of {execution_data['total_runs']} recent "
                   f"executions failed (threshold: {threshold:.0%}).",
        "evidence_json": {
            "failure_rate": rate,
            "total_runs": execution_data["total_runs"],
            "failed_count": execution_data["failed_count"],
            "sample_failures": execution_data["sample_failures"],
        },
        "source_id": None,
    }]
```

### Step 10: Router — Monitor API

**新文件**: `backend/app/routers/monitor_runs.py`

```python
# @PRODUCT Router — OS Core
import json
from datetime import datetime

from fastapi import APIRouter, HTTPException
from app.database import SessionLocal
from app.models.monitor_run import MonitorRun
from app.models.monitor_finding import MonitorFinding

router = APIRouter(prefix="/api/v1/monitor", tags=["monitor"])


# ── Serializers ──────────────────────────────
# Avoid SQLAlchemy __dict__ (_sa_instance_state pollution)


def _serialize_run(r: MonitorRun) -> dict:
    return {
        "id": r.id,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        "status": r.status,
        "summary": r.summary,
        "findings_count": r.findings_count,
        "alerts_created": r.alerts_created,
        "tasks_created": r.tasks_created,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


def _serialize_finding(f: MonitorFinding) -> dict:
    return {
        "id": f.id,
        "monitor_run_id": f.monitor_run_id,
        "finding_type": f.finding_type,
        "severity": f.severity,
        "title": f.title,
        "summary": f.summary,
        "evidence_json": json.loads(f.evidence_json) if f.evidence_json else None,
        "status": f.status,
        "source_id": f.source_id,
        "alert_id": f.alert_id,
        "task_id": f.task_id,
        "created_at": f.created_at.isoformat() if f.created_at else None,
    }


# POST /api/v1/monitor/run
@router.post("/run")
async def trigger_monitor_scan():
    from app.monitor.runner import run_monitor_scan
    result = await run_monitor_scan({})
    return result


# GET /api/v1/monitor/runs
@router.get("/runs")
async def list_runs(limit: int = 10, offset: int = 0):
    session = SessionLocal()
    try:
        runs = session.query(MonitorRun).order_by(
            MonitorRun.id.desc()
        ).offset(offset).limit(limit).all()
        return {"runs": [_serialize_run(r) for r in runs]}
    finally:
        session.close()


# GET /api/v1/monitor/runs/{run_id}
@router.get("/runs/{run_id}")
async def get_run(run_id: int):
    session = SessionLocal()
    try:
        run = session.query(MonitorRun).filter_by(id=run_id).first()
        if not run:
            raise HTTPException(status_code=404, detail="Run not found")
        findings = session.query(MonitorFinding).filter_by(monitor_run_id=run_id).all()
        return {
            "run": _serialize_run(run),
            "findings": [_serialize_finding(f) for f in findings],
        }
    finally:
        session.close()


# GET /api/v1/monitor/findings
@router.get("/findings")
async def list_findings(
    status: str = None,
    severity: str = None,
    finding_type: str = None,
    limit: int = 20,
    offset: int = 0,
):
    session = SessionLocal()
    try:
        query = session.query(MonitorFinding)
        if status:
            query = query.filter_by(status=status)
        if severity:
            query = query.filter_by(severity=severity)
        if finding_type:
            query = query.filter_by(finding_type=finding_type)
        findings = query.order_by(MonitorFinding.id.desc()).offset(offset).limit(limit).all()
        return {"findings": [_serialize_finding(f) for f in findings], "total": query.count()}
    finally:
        session.close()


# GET /api/v1/monitor/findings/{finding_id}
@router.get("/findings/{finding_id}")
async def get_finding(finding_id: int):
    session = SessionLocal()
    try:
        finding = session.query(MonitorFinding).filter_by(id=finding_id).first()
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        return {"finding": _serialize_finding(finding)}
    finally:
        session.close()


# PATCH /api/v1/monitor/findings/{finding_id}/dismiss
@router.patch("/findings/{finding_id}/dismiss")
async def dismiss_finding(finding_id: int):
    session = SessionLocal()
    try:
        finding = session.query(MonitorFinding).filter_by(id=finding_id).first()
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        finding.status = "dismissed"
        session.commit()
        return {"status": "ok", "finding_id": finding_id}
    finally:
        session.close()


# POST /api/v1/monitor/findings/{finding_id}/create-task
@router.post("/findings/{finding_id}/create-task")
async def create_task_from_finding(finding_id: int):
    session = SessionLocal()
    try:
        finding = session.query(MonitorFinding).filter_by(id=finding_id).first()
        if not finding:
            raise HTTPException(status_code=404, detail="Finding not found")
        if finding.status == "dismissed":
            raise HTTPException(status_code=400, detail="Finding already dismissed")

        from app.models.task_pool import TaskPool
        task = TaskPool(
            title=f"Investigate: {finding.title}",
            description=f"Monitor finding #{finding_id}: {finding.summary}",
            status="approval_required",
            source="monitor",
            source_id=f"monitor_finding:{finding_id}",
        )
        session.add(task)
        session.flush()
        finding.task_id = task.id
        finding.status = "converted"
        session.commit()
        return {"status": "ok", "task_id": task.id}
    finally:
        session.close()
```

---

## 执行清单

### Sprint A

- [ ] Step 1: 创建 `config/monitor-rules.example.yaml`
- [ ] Step 2: 创建 `monitor_run.py` + `monitor_finding.py` 模型
- [ ] Step 2: 更新 `models/__init__.py` + 创建迁移
- [ ] Step 3: 创建 `monitor/` 包 + `probes/task_probe.py` + `probes/cost_probe.py`
- [ ] Step 4: 创建 `analyzers/stuck_task.py` + `analyzers/cost_spike.py`
- [ ] Step 5: 创建 `outputs/alert_output.py` + `runner.py`
- [ ] 验收: Stuck Task + Cost Spike

### Sprint B

- [ ] Step 7: 创建 `probes/execution_probe.py` + `probes/runtime_probe.py`
- [ ] Step 8: 创建 `analyzers/error_rate.py`
- [ ] Step 9: 更新 `outputs/alert_output.py`（支持 task draft）
- [ ] Step 10: 创建 `routers/monitor_runs.py` + 注册
- [ ] Step 11: 全链路验收

---

## 风险与回滚

| 风险 | 缓解 |
|:-----|:------|
| models 迁移脚本冲突 | SQLite — 直接执行 CREATE TABLE IF NOT EXISTS |
| probes 查询慢（大量数据） | 加 LIMIT + 走索引 |
| runtime_probe 调用失败 | catch Exception，标记为 unreachable，不影响其他 probe |
| 验收数据不足 | v0.5 验收使用手动构造数据（与 v0.2-v0.4 验收方式一致） |
