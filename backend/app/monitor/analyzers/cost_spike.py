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
