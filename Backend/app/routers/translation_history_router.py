from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import List
from datetime import datetime

router = APIRouter(prefix="/api/v1/translations", tags=["Translation History & Logs"])

class TranslationRecord(BaseModel):
    user_id: int
    translated_text: str
    confidence_level: float

class TranslationResponse(BaseModel):
    id: int
    user_id: int
    translated_text: str
    confidence_level: float
    timestamp: str

    class Config:
        from_attributes = True

# 1. Fetch Translation History for a User
@router.get("/history/{user_id}", response_model=List[TranslationResponse])
def get_translation_history(user_id: int):
    """
    Retrieves past sign language translation logs and recognized sentences for a specific user.
    """
    mock_history = [
        {
            "id": 101,
            "user_id": user_id,
            "translated_text": "Hello, welcome to sign language platform",
            "confidence_level": 0.96,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "id": 102,
            "user_id": user_id,
            "translated_text": "Thank you for your assistance",
            "confidence_level": 0.91,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    return mock_history

# 2. Save a New Translation Log Entry
@router.post("/log", response_model=TranslationResponse)
def log_new_translation(record: TranslationRecord):
    """
    Saves a newly processed real-time gesture translation string into the database log.
    """
    if record.confidence_level < 0.0 or record.confidence_level > 1.0:
        raise HTTPException(status_code=400, detail="Confidence level must be between 0.0 and 1.0.")
        
    return {
        "id": 505,
        "user_id": record.user_id,
        "translated_text": record.translated_text,
        "confidence_level": record.confidence_level,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }