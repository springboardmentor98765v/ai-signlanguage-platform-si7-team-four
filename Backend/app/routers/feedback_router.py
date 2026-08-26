from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, field_validator
from typing import List
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import Feedback
from app.utils.validation import reject_malicious
import uuid as _uuid

router = APIRouter(prefix="/api/v1/feedback", tags=["Community Feedback & Support"])

class FeedbackCreate(BaseModel):
    user_id: str | int = Field(..., description="User submitting the feedback.")
    category: str = Field(..., max_length=50, description="E.g., Gesture Recognition, Dictionary, General")
    rating: int = Field(..., ge=1, le=5, description="Rating scale from 1 to 5")
    comments: str = Field(..., min_length=1, max_length=2000)

    @field_validator("category", "comments")
    @classmethod
    def _reject_malicious_text(cls, value: str) -> str:
        return reject_malicious(value)


class FeedbackResponse(BaseModel):
    id: str
    user_id: str
    category: str
    rating: int
    comments: str
    submitted_at: datetime


# 1. Submit User Feedback Endpoint
@router.post("/submit", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(feedback: FeedbackCreate, db: Session = Depends(get_db)):
    """
    Allows users to submit performance feedback, bug reports, or feature ratings.
    """
    try:
        user_uuid = str(_uuid.UUID(str(feedback.user_id)))
    except ValueError:
        user_uuid = str(_uuid.uuid5(_uuid.NAMESPACE_DNS, str(feedback.user_id)))

    row = Feedback(
        user_id=user_uuid,
        category=feedback.category.strip(),
        rating=feedback.rating,
        comments=feedback.comments.strip(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return FeedbackResponse(
        id=str(row.id),
        user_id=str(row.user_id),
        category=row.category,
        rating=row.rating,
        comments=row.comments,
        submitted_at=row.submitted_at,
    )


# 2. Retrieve All Feedback Logs Endpoint
@router.get("/all", response_model=List[FeedbackResponse])
def get_all_feedback(db: Session = Depends(get_db)):
    """
    Retrieves all submitted feedback and user ratings logs (admin view).
    """
    rows = (
        db.query(Feedback)
        .order_by(Feedback.submitted_at.desc())
        .all()
    )
    return [
        FeedbackResponse(
            id=str(row.id),
            user_id=str(row.user_id),
            category=row.category,
            rating=row.rating,
            comments=row.comments,
            submitted_at=row.submitted_at,
        )
        for row in rows
    ]