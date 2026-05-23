# @PRODUCT Router — OS Core
from fastapi import APIRouter, HTTPException
from app.database import get_sync_session
from app.models.context_pack import ContextPack
from app.schemas.context_pack import ContextPackCreate, ContextPackResponse

router = APIRouter(tags=["Context Packs"])


@router.get("/api/v1/task-pool/{task_id}/context-pack", response_model=ContextPackResponse)
def get_context_pack(task_id: int):
    session = get_sync_session()
    try:
        cp = session.query(ContextPack).filter(ContextPack.task_id == task_id).first()
        if not cp:
            raise HTTPException(status_code=404, detail="Context pack not found for this task")
        return _cp_to_response(cp)
    finally:
        session.close()


@router.post("/api/v1/task-pool/{task_id}/context-pack", response_model=ContextPackResponse)
def upsert_context_pack(task_id: int, body: ContextPackCreate):
    session = get_sync_session()
    try:
        existing = session.query(ContextPack).filter(ContextPack.task_id == task_id).first()
        if existing:
            # Update existing
            update_data = body.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(existing, key, value)
            cp = existing
        else:
            # Create new
            cp = ContextPack(
                task_id=task_id,
                founder_intent=body.founder_intent,
                business_line_state=body.business_line_state,
                related_runs=body.related_runs,
                related_artifacts=body.related_artifacts,
                known_failures=body.known_failures,
                relevant_rules=body.relevant_rules,
                constraints=body.constraints,
                forbidden_actions=body.forbidden_actions,
                budget_limit=body.budget_limit,
                acceptance_criteria=body.acceptance_criteria,
                referenced_knowledge=body.referenced_knowledge,
                auto_generated=body.auto_generated,
            )
            session.add(cp)

        session.commit()
        session.refresh(cp)
        return _cp_to_response(cp)
    finally:
        session.close()


def _cp_to_response(cp: ContextPack) -> ContextPackResponse:
    return ContextPackResponse(
        id=cp.id,
        task_id=cp.task_id,
        founder_intent=cp.founder_intent,
        business_line_state=cp.business_line_state,
        related_runs=cp.related_runs,
        related_artifacts=cp.related_artifacts,
        known_failures=cp.known_failures,
        relevant_rules=cp.relevant_rules,
        constraints=cp.constraints,
        forbidden_actions=cp.forbidden_actions,
        budget_limit=cp.budget_limit,
        acceptance_criteria=cp.acceptance_criteria,
        referenced_knowledge=cp.referenced_knowledge,
        auto_generated=cp.auto_generated,
        created_at=cp.created_at.isoformat() if cp.created_at else None,
        updated_at=cp.updated_at.isoformat() if cp.updated_at else None,
    )
