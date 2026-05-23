# @PRODUCT Model — OS Core
from sqlalchemy import Column, Integer, String, Text, Float
from app.models.base import Base

class CommandLog(Base):
    __tablename__ = "command_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    endpoint = Column(String, nullable=False)
    command_type = Column(String, nullable=False)
    mode = Column(String, default="dry-run")       # dry-run / execute
    payload = Column(Text)
    risk_level = Column(String, default="low")      # low / medium / high
    requires_confirmation = Column(Integer, default=1)
    confirmed = Column(Integer, default=0)
    confirmed_by = Column(String)                    # founder
    status = Column(String, default="dry-run")       # dry-run / pending / executed / rejected / failed
    result_summary = Column(Text)
    error_message = Column(Text)
    created_at = Column(String)
