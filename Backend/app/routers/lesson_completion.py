"""Lesson completion tracking endpoints.

Allows marking lessons as completed and querying completion status
per user. Completion is automatically triggered by the practice submit
flow when a score >= 80% is achieved, but can also be set manually.
"""
from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func as sqlf
from typing import List
import uuid

from app.db.database import get_db
from app.models.models import LessonCompletion, Lesson, User
from app.utils.security import verify_token_and_role

router = APIRouter(prefix="/api/lesson-completions", tags=["Lesson Completion"])


class MarkCompleteRequest(BaseModel):
    lesson_id: str
    score: float = 0.0


class LessonCompletionOut(BaseModel):
    lesson_id: str
    best_score: float
    completed_at: str


@router.post("/mark", status_code=status.HTTP_200_OK)
def mark_lesson_complete(
    data: MarkCompleteRequest,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token_and_role(["Learner", "Instructor", "Admin"])),
):
    user_id = token_payload["user_id"]

    # Validate lesson exists.
    try:
        lesson_uuid = str(uuid.UUID(data.lesson_id))
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid lesson_id format.")
    lesson = db.query(Lesson).filter(Lesson.id == lesson_uuid).first()
    if not lesson:
        raise HTTPException(status_code=404, detail="Lesson not found.")

    existing = (
        db.query(LessonCompletion)
        .filter(
            LessonCompletion.user_id == user_id,
            LessonCompletion.lesson_id == lesson_uuid,
        )
        .first()
    )

    if existing:
        if data.score > existing.best_score:
            existing.best_score = data.score
    else:
        existing = LessonCompletion(
            user_id=user_id,
            lesson_id=lesson_uuid,
            best_score=data.score,
        )
        db.add(existing)

    db.commit()
    db.refresh(existing)
    return {"message": "Lesson marked as completed.", "lesson_id": lesson_uuid, "best_score": existing.best_score}


@router.get("/user/{user_id}", status_code=status.HTTP_200_OK)
def get_user_completions(
    user_id: str,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token_and_role(["Learner", "Instructor", "Admin", "Accessibility Trainer"])),
):
    completions = (
        db.query(LessonCompletion)
        .filter(LessonCompletion.user_id == user_id)
        .all()
    )
    return {
        "user_id": user_id,
        "total_completed": len(completions),
        "completions": [
            {
                "lesson_id": str(c.lesson_id),
                "best_score": c.best_score,
                "completed_at": c.completed_at.isoformat() if c.completed_at else None,
            }
            for c in completions
        ],
    }


@router.get("/summary/{user_id}", status_code=status.HTTP_200_OK)
def get_completion_summary(
    user_id: str,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token_and_role(["Learner", "Instructor", "Admin", "Accessibility Trainer"])),
):
    total_lessons = db.query(sqlf.count(Lesson.id)).scalar() or 0
    completed_count = (
        db.query(sqlf.count(LessonCompletion.id))
        .filter(LessonCompletion.user_id == user_id)
        .scalar()
        or 0
    )
    return {
        "user_id": user_id,
        "total_lessons": total_lessons,
        "completed": completed_count,
        "percentage": round(completed_count / total_lessons * 100, 1) if total_lessons > 0 else 0.0,
    }
