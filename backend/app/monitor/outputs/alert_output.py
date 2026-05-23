# @PRODUCT Output — OS Core
import json

from app.database import get_sync_session
from app.models.monitor_finding import MonitorFinding
from app.models.alert import Alert
from app.models.task_pool import TaskPool


def process_findings(findings: list[dict], run_id: int, config: dict) -> dict:
    """Write findings to DB and create alerts/tasks based on severity config."""
    session = get_sync_session()
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
