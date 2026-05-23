# @PRODUCT Schema — OS Core
from pydantic import BaseModel
from typing import Optional

class AlertResponse(BaseModel):
    id: int
    severity: Optional[str] = None
    title: str
    description: Optional[str] = None
    source: Optional[str] = None
    resolved: bool = False
    created_at: Optional[str] = None
