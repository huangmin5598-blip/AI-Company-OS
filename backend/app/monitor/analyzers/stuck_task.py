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
                       f"{task['hours_since_update']:.1f}h (threshold: {task['threshold_hours']}h).",
            "evidence_json": task,
            "source_id": f"task:{task['task_id']}",
        })

    return findings
