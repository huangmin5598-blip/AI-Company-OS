# @PRODUCT Schema — OS Core
from pydantic import BaseModel
from typing import Optional

class ExecutionRecordResponse(BaseModel):
    id: str
    date: str
    business_line: str
    task_id: Optional[str] = None
    title: Optional[str] = None
    word_count: int = 0
    result: Optional[str] = None
    result_detail: Optional[str] = None
    cost_usd: float = 0.0
    model: Optional[str] = None
    artifact_path: Optional[str] = None
