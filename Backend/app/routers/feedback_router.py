from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import List
from datetime import datetime

router = APIRouter(prefix="/api/v1/feedback", tags=["Community Feedback & Support"])

class FeedbackCreate(BaseModel):
    user_id: int
    category: str = Field(..., description="E.g., Gesture Recognition, Dictionary, General")
    rating: int = Field(..., ge=1, le=5, description="Rating scale from 1 to 5")
    comments: str

class FeedbackResponse(BaseModel):
    id: int
    user_id: int
    category: str
    rating: int
    comments: str
    submitted_at: str

    class Config:
        from_attributes = True

# In-memory mock storage for feedback items
FEEDBACK_DB = [
    {
        "id": 1,
        "user_id": 101,
        "category": "Gesture Recognition",
        "rating": 5,
        "comments": "The real-time translation accuracy has improved significantly!",
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
]

# 1. Submit User Feedback Endpoint
@router.post("/submit", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(feedback: FeedbackCreate):
    """
    Allows users to submit performance feedback, bug reports, or feature ratings.
    """
    new_record = {
        "id": len(FEEDBACK_DB) + 1,
        "user_id": feedback.user_id,
        "category": feedback.category,
        "rating": feedback.rating,
        "comments": feedback.comments,
        "submitted_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    FEEDBACK_DB.append(new_record)
    return new_record

# 2. Retrieve All Feedback Logs Endpoint
@router.get("/all", response_model=List[FeedbackResponse])
def get_all_feedback():
    """
    Retrieves all submitted feedback and user ratings logs (admin view).
    """
    return FEEDBACK_DB