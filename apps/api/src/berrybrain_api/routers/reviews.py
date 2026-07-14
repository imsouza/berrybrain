from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select

from berrybrain_api.database import SessionLocal
from berrybrain_api.jobs import CREATE_REVIEW_FROM_INSIGHT, create_job
from berrybrain_api.models import ReviewItemRecord
from berrybrain_api.review_service import (
    create_review_item,
    grade_review_item,
    serialize_review,
    set_review_status,
)


router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])


class CreateReviewRequest(BaseModel):
    source_insight_id: int
    review_type: str
    prompt: str = Field(min_length=1, max_length=2000)
    expected_points: list[str] = Field(min_length=1, max_length=12)
    evidence: list = Field(default_factory=list, max_length=12)


class GradeReviewRequest(BaseModel):
    rating: str
    perceived_difficulty: int | None = None


@router.get("")
def list_reviews(due: bool = False, limit: int = 50) -> dict:
    with SessionLocal() as session:
        query = select(ReviewItemRecord).where(ReviewItemRecord.status == "active")
        if due:
            query = query.where(ReviewItemRecord.due_at <= datetime.now(UTC))
        items = list(
            session.execute(
                query.order_by(ReviewItemRecord.due_at.asc()).limit(min(limit, 100))
            ).scalars()
        )
        return {"reviews": [serialize_review(item) for item in items]}


@router.post("/from-insight", status_code=201)
def create_review(payload: CreateReviewRequest) -> dict:
    with SessionLocal() as session:
        item = create_review_item(
            session,
            source_insight_id=payload.source_insight_id,
            review_type=payload.review_type,
            prompt=payload.prompt,
            expected_points=payload.expected_points,
            evidence=payload.evidence,
        )
        return {"review": serialize_review(item)}


@router.post("/{review_id}/grade")
def grade_review(review_id: int, payload: GradeReviewRequest) -> dict:
    with SessionLocal() as session:
        item = grade_review_item(
            session,
            review_id,
            payload.rating,
            payload.perceived_difficulty,
        )
        return {"review": serialize_review(item)}


@router.post("/{review_id}/pause")
def pause_review(review_id: int) -> dict:
    with SessionLocal() as session:
        return {
            "review": serialize_review(set_review_status(session, review_id, "paused"))
        }


@router.post("/{review_id}/resume")
def resume_review(review_id: int) -> dict:
    with SessionLocal() as session:
        return {
            "review": serialize_review(set_review_status(session, review_id, "active"))
        }


@router.delete("/{review_id}")
def delete_review(review_id: int) -> dict:
    with SessionLocal() as session:
        return {
            "review": serialize_review(set_review_status(session, review_id, "deleted"))
        }


@router.post("/{review_id}/regenerate")
def regenerate_review(review_id: int) -> dict:
    with SessionLocal() as session:
        item = session.get(ReviewItemRecord, review_id)
        if item is None:
            return {"status": "review_not_found"}
        item.status = "stale"
        job = create_job(
            session,
            CREATE_REVIEW_FROM_INSIGHT,
            {"insight_id": item.source_insight_id, "review_id": item.id},
            max_attempts=2,
        )
        return {"status": "queued", "jobId": job.id}
