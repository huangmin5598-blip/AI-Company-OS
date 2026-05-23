# @PRODUCT Router — OS Core
from fastapi import APIRouter, HTTPException
from app.database import get_sync_session
from app.models.review import Review
from app.schemas.review import ReviewCreate, ReviewResponse

router = APIRouter(tags=["Reviews"])


@router.get("/api/v1/reviews/{review_id}", response_model=ReviewResponse)
def get_review(review_id: int):
    session = get_sync_session()
    try:
        review = session.query(Review).filter(Review.id == review_id).first()
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        return _review_to_response(review)
    finally:
        session.close()


@router.post("/api/v1/reviews", response_model=ReviewResponse, status_code=201)
def create_review(body: ReviewCreate):
    session = get_sync_session()
    try:
        review = Review(
            task_id=body.task_id,
            result=body.result,
            artifact_id=body.artifact_id,
            review_notes=body.review_notes,
            next_action=body.next_action,
            reviewed_by=body.reviewed_by,
        )
        session.add(review)
        session.commit()
        session.refresh(review)
        return _review_to_response(review)
    finally:
        session.close()


def _review_to_response(r: Review) -> ReviewResponse:
    return ReviewResponse(
        id=r.id,
        task_id=r.task_id,
        result=r.result,
        artifact_id=r.artifact_id,
        review_notes=r.review_notes,
        next_action=r.next_action,
        reviewed_by=r.reviewed_by,
        created_at=r.created_at.isoformat() if r.created_at else None,
    )
