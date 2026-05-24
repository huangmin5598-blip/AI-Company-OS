# @PRODUCT Model — OS Core
from sqlalchemy import Column, String, Integer, Text, DateTime, func
from app.models.base import Base


class RuntimeRegistry(Base):
    """Registered runtime instances."""

    __tablename__ = "runtime_registry"

    id = Column(Integer, primary_key=True, autoincrement=True)
    runtime_id = Column(String, nullable=False, unique=True, index=True)
    runtime_type = Column(String, nullable=False)
    # hermes / openclaw / codex / claude_code / cloud
    display_name = Column(String, nullable=False)
    adapter_module = Column(String, nullable=False)
    # Python module path: "app.runtime.adapters.hermes_adapter"
    endpoint = Column(String)
    # CLI path or HTTP URL
    config_json = Column(Text)
    # Optional adapter-specific config
    enabled = Column(Integer, default=1)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
