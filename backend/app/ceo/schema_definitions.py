"""
CEO Agent Skill Schema Definitions
These are Python constants used by the Hermes CEO Skill and for backend validation.
"""

GOAL_DECOMPOSITION_SCHEMA_VERSION = "v0.3.0"

GOAL_TYPES = ["repair", "growth", "research", "build", "review", "ops"]

TASK_TYPES = ["diagnosis", "fix", "investigate", "optimize", "build", "review", "monitor"]

# Approval thresholds
APPROVAL_CONFIDENCE_THRESHOLD = 0.85
APPROVAL_MATCHED_TARGETS_MAX = 1

# Goal Intake Schema — used for Hermes prompt and backend validation
GOAL_INTAKE_SCHEMA_DESCRIPTION = """
{
  "goal_summary": "string — 目标摘要",
  "goal_type": "repair|growth|research|build|review|ops",
  "business_line": "string, optional",
  "risk_level": "low|medium|high",
  "priority": "low|medium|high|critical",
  "confidence": "float 0.0-1.0",
  "tasks": [
    {
      "title": "string",
      "why": "string",
      "task_type": "diagnosis|fix|investigate|optimize|build|review|monitor",
      "assigned_agent": "string, optional",
      "risk_level": "low|medium|high",
      "priority": "low|medium|high|critical",
      "acceptance_criteria": "string, optional",
      "context_pack": {
        "founder_intent": "string, optional",
        "related_sources": ["array of strings, optional"],
        "known_failures": ["array of strings, optional"],
        "constraints": "string, optional"
      }
    }
  ]
}
"""

# Approval Action Schema
APPROVAL_ACTION_SCHEMA_DESCRIPTION = """
{
  "intent_type": "approval_action",
  "decision": "approved|rejected|revised|deferred",
  "target_type": "approval",
  "target_id": "integer — the approval ID",
  "matched_targets_count": "integer",
  "confidence": "float 0.0-1.0",
  "requires_confirmation": "boolean",
  "founder_phrase": "string — what the founder said"
}
"""
