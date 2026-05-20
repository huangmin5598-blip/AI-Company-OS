from pydantic import BaseModel
from typing import Optional

class ArtifactResponse(BaseModel):
    id: str
    run_id: Optional[str] = None
    business_line: str
    date: str
    artifact_path: str
    word_count: int = 0
    file_size_bytes: int = 0
    file_type: Optional[str] = None
    artifact_status: str = "created"
    cost_usd: float = 0.0
