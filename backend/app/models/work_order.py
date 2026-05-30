# @PRODUCT Model — v0.10 Work Order
from datetime import datetime
from sqlalchemy import Column, String, Text, Integer, Boolean, DateTime, func
from app.models.base import Base


class WorkOrder(Base):
    __tablename__ = "work_orders"

    work_order_id = Column(String, primary_key=True)   # UUID
    goal_session_id = Column(String, default="")
    product_line_id = Column(String, default="")
    skill_id = Column(String, nullable=False)
    task_type = Column(String, default="")
    route_reason = Column(Text, default="")
    risk_level = Column(String, default="low")          # low / medium / high
    execution_mode = Column(String, default="direct_delegate")
    assigned_agent = Column(String, default="")
    runtime_id = Column(String, default="")
    input_context = Column(Text, default="")
    expected_output = Column(Text, default="")
    status = Column(String, default="created")
    # created → routed → assigned → blocked / requires_approval → in_progress → completed / failed / cancelled
    approval_required = Column(Boolean, default=False)
    approval_id = Column(String, default="")
    attempt_count = Column(Integer, default=0)
    output_path = Column(Text, default="")
    evidence_path = Column(Text, default="")
    error = Column(Text, default="")
    result_summary = Column(Text, default="")
    artifacts_json = Column(Text, default="")            # JSON list of artifact paths
    routing_log_json = Column(Text, default="")          # JSON routing trace
    execution_log_json = Column(Text, default="")        # JSON execution trace
    created_at = Column(DateTime, default=func.now())
    assigned_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # v0.13 — OpenClaw tracking
    openclaw_dispatched_at = Column(DateTime, nullable=True)
    openclaw_claimed_at = Column(DateTime, nullable=True)
    openclaw_timeout_at = Column(DateTime, nullable=True)

    # v0.21 — Founder approval timestamp (set by approve-dispatch command)
    approved_for_dispatch_at = Column(DateTime, nullable=True)

    def to_dict(self) -> dict:
        return {
            "work_order_id": self.work_order_id,
            "goal_session_id": self.goal_session_id,
            "product_line_id": self.product_line_id,
            "skill_id": self.skill_id,
            "task_type": self.task_type,
            "route_reason": self.route_reason,
            "risk_level": self.risk_level,
            "execution_mode": self.execution_mode,
            "assigned_agent": self.assigned_agent,
            "runtime_id": self.runtime_id,
            "input_context": self.input_context,
            "expected_output": self.expected_output,
            "status": self.status,
            "approval_required": bool(self.approval_required),
            "approval_id": self.approval_id,
            "attempt_count": self.attempt_count,
            "output_path": self.output_path,
            "evidence_path": self.evidence_path,
            "error": self.error,
            "result_summary": self.result_summary,
            "artifacts_json": self.artifacts_json,
            "routing_log_json": self.routing_log_json,
            "execution_log_json": self.execution_log_json,
            "created_at": str(self.created_at) if self.created_at else None,
            "assigned_at": str(self.assigned_at) if self.assigned_at else None,
            "completed_at": str(self.completed_at) if self.completed_at else None,
            # v0.13 — OpenClaw tracking
            "openclaw_dispatched_at": str(self.openclaw_dispatched_at) if self.openclaw_dispatched_at else None,
            "openclaw_claimed_at": str(self.openclaw_claimed_at) if self.openclaw_claimed_at else None,
            "openclaw_timeout_at": str(self.openclaw_timeout_at) if self.openclaw_timeout_at else None,
            # v0.21 — Founder approval
            "approved_for_dispatch_at": str(self.approved_for_dispatch_at) if self.approved_for_dispatch_at else None,
        }
