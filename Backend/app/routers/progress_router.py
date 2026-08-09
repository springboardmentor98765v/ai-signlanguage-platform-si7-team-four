from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.models import models

router = APIRouter(prefix="/api/v1/progress", tags=["Progress & Analytics"])

class ProgressCreate(BaseModel):
    user_id: int
    course_id: int
    completed_lessons: int = Field(..., ge=0)
    total_lessons: int = Field(..., ge=1)
    accuracy_score: float = Field(..., ge=0.0, le=100.0)

class ProgressResponse(BaseModel):
    id: int
    user_id: int
    course_id: int
    completed_lessons: int
    total_lessons: int
    accuracy_score: float
    last_updated: str

    class Config:
        orm_mode = True

# 1. Fetch User Progress Statistics Endpoint
@router.get("/user/{user_id}", response_model=List[ProgressResponse])
def get_user_progress(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieves learning progress, course completion status, and accuracy metrics for a specific user.
    """
    sample_progress = [
        {
            "id": 1,
            "user_id": user_id,
            "course_id": 101,
            "completed_lessons": 8,
            "total_lessons": 10,
            "accuracy_score": 92.5,
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    return sample_progress

# 2. Record or Update User Progress Endpoint
@router.post("/update", response_model=ProgressResponse)
def update_user_progress(progress: ProgressCreate):
    """
    Records or updates user lesson completion and sign translation accuracy.
    """
    if progress.accuracy_score < 0 or progress.accuracy_score > 100:
        raise HTTPException(status_code=400, detail="Accuracy score must be between 0 and 100.")
        
    metrics = completion_metrics(progress)
    return {
        "id": 42,
        "user_id": progress.user_id,
        "course_id": progress.course_id,
        "completed_lessons": progress.completed_lessons,
        "total_lessons": metrics["total_lessons"],
        "accuracy_score": metrics["accuracy_score"],
        "last_updated": metrics["last_updated"]
    }

def completion_metrics(progress: ProgressCreate):
    return {
        "total_lessons": progress.total_lessons,
        "accuracy_score": progress.accuracy_score,
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }