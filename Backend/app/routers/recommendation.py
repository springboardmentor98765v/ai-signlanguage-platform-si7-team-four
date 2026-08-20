from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.recommendation_service import generate_recommendations
from app.utils.validation import reject_malicious
from app.models.models import Recommendation as RecommendationModel, Lesson

router = APIRouter(prefix="/api/recommendation", tags=["Recommendation"])


@router.get("/{user_id}")
def list_recommendations(user_id: str, db: Session = Depends(get_db)):
    """
    Returns the active, persisted practice recommendations for a learner,
    joined with the lesson catalog so the UI can render useful titles.
    """
    rows = (
        db.query(RecommendationModel)
        .filter(RecommendationModel.user_id == user_id, RecommendationModel.is_active.is_(True))
        .all()
    )
    recommended_lessons = []
    for rec in rows:
        lesson = db.query(Lesson).filter(Lesson.id == rec.lesson_id).first()
        if lesson is None:
            continue
        recommended_lessons.append(
            {
                "lesson_id": str(lesson.id),
                "title": lesson.title,
                "reason": rec.reason,
                "expected_gesture": lesson.expected_gesture,
            }
        )
    return {"user_id": user_id, "recommended_lessons": recommended_lessons}


class AttemptRecord(BaseModel):
    sign: str = Field(..., min_length=1, max_length=5)
    score: float = Field(..., ge=0, le=100)

    @field_validator("sign")
    @classmethod
    def _reject_malicious_text(cls, value: str) -> str:
        return reject_malicious(value)


class LearnerHistoryRequest(BaseModel):
    learner_id: str
    attempts: List[AttemptRecord]


class Recommendation(BaseModel):
    sign: str
    message: str


class RecommendationResponse(BaseModel):
    learner_id: str
    recommendations: List[Recommendation]
    message: str


@router.post("/", response_model=RecommendationResponse)
def get_recommendations(request: LearnerHistoryRequest) -> RecommendationResponse:
    if not request.attempts:
        raise HTTPException(status_code=400, detail="Attempt history cannot be empty.")

    attempts = [attempt.model_dump() for attempt in request.attempts]
    recommendations = generate_recommendations(attempts)

    if not recommendations:
        return RecommendationResponse(
            learner_id=request.learner_id,
            recommendations=[],
            message="Great job! No extra practice needed at this time."
        )

    return RecommendationResponse(
        learner_id=request.learner_id,
        recommendations=recommendations,
        message="Extra practice recommended for some signs."
    )