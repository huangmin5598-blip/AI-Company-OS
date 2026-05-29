# @PRODUCT Model — v0.12 Product Line Registry (Agent Boundaries)
from datetime import datetime
from sqlalchemy import Column, String, Text, DateTime, func
from app.models.base import Base


class ProductLineRegistry(Base):
    __tablename__ = "product_line_registry"

    product_line_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    owner_agent = Column(String, default="")
    status = Column(String, default="active")               # active / paused / incubating
    related_skills = Column(Text, default="")                # comma-separated skill_ids
    scope = Column(Text, default="")                         # v0.12: agent responsibility boundary
    current_goal = Column(Text, default="")                  # v0.12: active objective
    active_projects = Column(Text, default="")               # v0.12: JSON list of active project names
    weekly_status = Column(Text, default="")                 # v0.12: brief weekly status note
    created_at = Column(DateTime, default=func.now())

    def to_dict(self):
        return {
            "product_line_id": self.product_line_id,
            "name": self.name,
            "description": self.description,
            "owner_agent": self.owner_agent,
            "status": self.status,
            "related_skills": self.related_skills,
            "scope": self.scope,
            "current_goal": self.current_goal,
            "active_projects": self.active_projects,
            "weekly_status": self.weekly_status,
            "created_at": str(self.created_at) if self.created_at else None,
        }
