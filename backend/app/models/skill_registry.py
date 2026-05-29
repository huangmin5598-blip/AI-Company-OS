# @PRODUCT Model — v0.10 Skill Registry
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, func
from app.models.base import Base


class SkillRegistry(Base):
    __tablename__ = "skill_registry"

    skill_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    capability_type = Column(String, nullable=False)  # research / copywriting / code_build / report_generation / deploy
    owner_agent = Column(String, nullable=False)
    owner_runtime = Column(String, nullable=False)
    risk_level = Column(String, default="low")           # low / medium / high
    execution_mode = Column(String, default="direct_delegate")
    # direct_delegate / code_bridge / local_script / openclaw_task_card / checklist_only / manual
    input_schema = Column(Text, default="")
    output_schema = Column(Text, default="")
    examples = Column(Text, default="")
    status = Column(String, default="active")             # active / disabled / experimental
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def to_dict(self):
        return {
            "skill_id": self.skill_id,
            "name": self.name,
            "description": self.description,
            "capability_type": self.capability_type,
            "owner_agent": self.owner_agent,
            "owner_runtime": self.owner_runtime,
            "risk_level": self.risk_level,
            "execution_mode": self.execution_mode,
            "input_schema": self.input_schema,
            "output_schema": self.output_schema,
            "examples": self.examples,
            "status": self.status,
            "created_at": str(self.created_at) if self.created_at else None,
            "updated_at": str(self.updated_at) if self.updated_at else None,
        }
