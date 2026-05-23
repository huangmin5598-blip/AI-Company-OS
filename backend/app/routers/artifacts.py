# @PRODUCT Router — OS Core
from fastapi import APIRouter, Query
from typing import Optional
from app.database import get_sync_session
from app.models.artifact import Artifact
from app.schemas.artifact import ArtifactResponse

router = APIRouter(tags=["Artifacts"])

@router.get("/api/v1/artifacts", response_model=list[ArtifactResponse])
def list_artifacts(
    business_line: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
):
    session = get_sync_session()
    try:
        query = session.query(Artifact).filter(Artifact.data_source != 'mock')
        if business_line:
            query = query.filter(Artifact.business_line == business_line)
        if date:
            query = query.filter(Artifact.date == date)
        artifacts = query.order_by(Artifact.date.desc()).limit(limit).all()
        return [
            ArtifactResponse(
                id=a.id, run_id=a.run_id, business_line=a.business_line,
                date=a.date, artifact_path=a.artifact_path,
                word_count=a.word_count or 0, file_size_bytes=a.file_size_bytes or 0,
                file_type=a.file_type, artifact_status=a.artifact_status or "created",
                cost_usd=round(a.cost_usd or 0, 6),
            ) for a in artifacts
        ]
    finally:
        session.close()
