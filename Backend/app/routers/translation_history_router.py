from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel, Field, field_validator
from typing import List
from datetime import datetime

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import TranslationHistory
from app.utils.validation import reject_malicious
import uuid as _uuid

router = APIRouter(prefix="/api/v1/translations", tags=["Translation History & Logs"])

class TranslationRecord(BaseModel):
    user_id: str | int = Field(..., description="User performing the translation.")
    translated_text: str = Field(..., min_length=1, max_length=2000)
    confidence_level: float = Field(..., ge=0.0, le=1.0)

    @field_validator("translated_text")
    @classmethod
    def _reject_malicious_text(cls, value: str) -> str:
        return reject_malicious(value)


class TranslationResponse(BaseModel):
    id: str
    user_id: str
    translated_text: str
    confidence_level: float
    timestamp: datetime


# 1. Fetch Translation History for a User
@router.get("/history/{user_id}", response_model=List[TranslationResponse])
def get_translation_history(user_id: str, db: Session = Depends(get_db)):
    """
    Retrieves past sign language translation logs and recognized sentences for a specific user.
    """
    try:
        user_uuid = str(_uuid.UUID(user_id))
    except ValueError:
        user_uuid = user_id

    rows = (
        db.query(TranslationHistory)
        .filter(TranslationHistory.user_id == user_uuid)
        .order_by(TranslationHistory.created_at.desc())
        .all()
    )
    return [
        TranslationResponse(
            id=str(row.id),
            user_id=str(row.user_id),
            translated_text=row.translated_text,
            confidence_level=row.confidence_level,
            timestamp=row.created_at,
        )
        for row in rows
    ]


# 2. Save a New Translation Log Entry
@router.post("/log", response_model=TranslationResponse)
def log_new_translation(record: TranslationRecord, db: Session = Depends(get_db)):
    """
    Saves a newly processed real-time gesture translation string into the database log.
    """
    if record.confidence_level < 0.0 or record.confidence_level > 1.0:
        raise HTTPException(status_code=400, detail="Confidence level must be between 0.0 and 1.0.")

    try:
        user_uuid = str(_uuid.UUID(str(record.user_id)))
    except ValueError:
        user_uuid = str(_uuid.uuid5(_uuid.NAMESPACE_DNS, str(record.user_id)))

    row = TranslationHistory(
        user_id=user_uuid,
        translated_text=record.translated_text.strip(),
        confidence_level=record.confidence_level,
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    return TranslationResponse(
        id=str(row.id),
        user_id=str(row.user_id),
        translated_text=row.translated_text,
        confidence_level=row.confidence_level,
        timestamp=row.created_at,
    )