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
