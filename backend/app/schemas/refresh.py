# @PRODUCT Schema — OS Core
from pydantic import BaseModel
from typing import Optional

class RefreshResponse(BaseModel):
    status: str = "ok"
    refreshed_at: str = ""
    results: dict = {}

class RefreshStatusResponse(BaseModel):
    last_refreshed_at: Optional[str] = None
    status: Optional[str] = None
    summary: Optional[str] = None
