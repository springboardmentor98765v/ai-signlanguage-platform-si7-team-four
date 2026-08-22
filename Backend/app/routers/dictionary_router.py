from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.db.database import get_db
from app.models.models import Lesson

router = APIRouter(prefix="/api/v1/dictionary", tags=["Sign Dictionary & Vocabulary"])

class DictionarySignResponse(BaseModel):
    id: str
    sign_name: str
    category: str
    difficulty_level: str
    description: str
    video_url: Optional[str] = None


# 1. Search / list the sign-language dictionary (backed by the real lesson catalog).
@router.get("/signs", response_model=List[DictionarySignResponse])
def list_dictionary_signs(
    search: Optional[str] = Query(None, max_length=200),
    db: Session = Depends(get_db),
):
    query = db.query(Lesson)
    if search and search.strip():
        like = f"%{search.strip()}%"
        query = query.filter(
            or_(Lesson.title.ilike(like), Lesson.expected_gesture.ilike(like))
        )
    rows = query.order_by(Lesson.title.asc()).all()
    return [
        DictionarySignResponse(
            id=str(lesson.id),
            sign_name=lesson.title,
            category=(lesson.category or "general").capitalize(),
            difficulty_level=(lesson.difficulty or "easy").capitalize(),
            description=lesson.description or "",
            video_url=None,
        )
        for lesson in rows
    ]


# 2. Fetch a single dictionary sign by its real catalog id.
@router.get("/signs/{sign_id}", response_model=DictionarySignResponse)
def get_dictionary_sign(sign_id: str, db: Session = Depends(get_db)):
    lesson = (
        db.query(Lesson)
        .filter(
            or_(Lesson.id == sign_id, Lesson.slug == sign_id)
        )
        .first()
    )
    if lesson is None:
        raise HTTPException(status_code=404, detail="Sign not found in the dictionary.")
    return DictionarySignResponse(
        id=str(lesson.id),
        sign_name=lesson.title,
        category=(lesson.category or "general").capitalize(),
        difficulty_level=(lesson.difficulty or "easy").capitalize(),
        description=lesson.description or "",
        video_url=None,
    )