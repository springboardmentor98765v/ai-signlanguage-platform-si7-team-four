from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

from app.db.database import get_db
from app.models.models import AnalyticsSummary
from app.services.analytics_service import get_learner_dashboard

router = APIRouter(prefix="/api/v1/progress", tags=["Progress & Analytics"])

class ProgressCreate(BaseModel):
    user_id: str | int = Field(..., description="User whose progress is recorded.")
    course_id: str | int | None = None
    completed_lessons: int = Field(..., ge=0)
    total_lessons: int = Field(..., ge=1)
    accuracy_score: float = Field(..., ge=0.0, le=100.0)


class ProgressResponse(BaseModel):
    id: str
    user_id: str
    course_id: str | None
    completed_lessons: int
    total_lessons: int
    accuracy_score: float
    last_updated: datetime


# 1. Fetch User Progress Statistics Endpoint
@router.get("/user/{user_id}", response_model=List[ProgressResponse])
def get_user_progress(user_id: str, db: Session = Depends(get_db)):
    """
    Retrieves learning progress, course completion status, and accuracy metrics
    for a specific user, computed live from persisted practice/assessment records.
    """
    metrics = get_learner_dashboard(db, user_id)
    return [
        ProgressResponse(
            id=str(user_id),
            user_id=user_id,
            course_id=None,
            completed_lessons=metrics["lessons_completed"],
            total_lessons=max(metrics["lessons_completed"], 1),
            accuracy_score=float(metrics["overall_accuracy_percentage"] or 0.0),
            last_updated=datetime.utcnow(),
        )
    ]


# 2. Record or Update User Progress Endpoint
@router.post("/update", response_model=ProgressResponse)
def update_user_progress(progress: ProgressCreate, db: Session = Depends(get_db)):
    """
    Records or updates user lesson completion and sign translation accuracy.
    Upserts the learner's persisted AnalyticsSummary row.
    """
    if progress.accuracy_score < 0 or progress.accuracy_score > 100:
        raise HTTPException(status_code=400, detail="Accuracy score must be between 0 and 100.")

    user_id = str(progress.user_id)
    summary = db.query(AnalyticsSummary).filter(AnalyticsSummary.user_id == user_id).first()
    if summary is None:
        summary = AnalyticsSummary(user_id=user_id)
        summary.overall_accuracy_percentage = progress.accuracy_score
        summary.improvement_rate_percentage = 0.0
        summary.lessons_completed = progress.completed_lessons
        db.add(summary)
    else:
        summary.overall_accuracy_percentage = progress.accuracy_score
        summary.improvement_rate_percentage = summary.improvement_rate_percentage or 0.0
        summary.lessons_completed = progress.completed_lessons
    db.commit()
    db.refresh(summary)

    return ProgressResponse(
        id=str(summary.id),
        user_id=user_id,
        course_id=str(progress.course_id) if progress.course_id is not None else None,
        completed_lessons=progress.completed_lessons,
        total_lessons=progress.total_lessons,
        accuracy_score=progress.accuracy_score,
        last_updated=datetime.utcnow(),
    )