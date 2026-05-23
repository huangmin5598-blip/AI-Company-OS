# @PRODUCT Monitor runner — OS Core
from datetime import datetime


async def run_monitor_scan(config: dict) -> dict:
    """Run a full monitor scan: collect → analyze → output.

    Each probe/analyzer is isolated — one failure doesn't block others.
    Final run.status is success / partial / failed.
    """
    from app.database import get_sync_session
    from app.models.monitor_run import MonitorRun

    # 1. Create run record
    session = get_sync_session()
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

    if config.get("probes", {}).get("execution_probe", {}).get("enabled", True):
        try:
            from app.monitor.probes.execution_probe import collect as collect_exec
            from app.monitor.analyzers.error_rate import analyze as analyze_error
            exec_data = await collect_exec(config)
            all_findings.extend(analyze_error(exec_data, config))
        except Exception as e:
            errors.append(f"execution_probe: {e}")

    if config.get("probes", {}).get("runtime_probe", {}).get("enabled", True):
        try:
            from app.monitor.probes.runtime_probe import collect as collect_rt
            rt_data = await collect_rt(config)
            if rt_data:
                for r in rt_data:
                    if not r.get("healthy", True):
                        all_findings.append({
                            "finding_type": "runtime_health",
                            "severity": "warning" if r.get("status") == "degraded" else "critical",
                            "title": f"Runtime {r.get('name', 'unknown')} is {r.get('status', 'unreachable')}",
                            "summary": f"Runtime '{r.get('name', 'unknown')}' ({r.get('type', '?')}) "
                                       f"reported status: {r.get('status', 'unknown')}.",
                            "evidence_json": r,
                            "source_id": f"runtime:{r.get('name', 'unknown')}",
                        })
        except Exception as e:
            errors.append(f"runtime_probe: {e}")

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

    session = get_sync_session()
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
