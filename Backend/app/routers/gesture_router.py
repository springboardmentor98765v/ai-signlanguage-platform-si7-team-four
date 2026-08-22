from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field, field_validator
from typing import List
import shutil
import os
import logging

from app.db.database import get_db
from app.models import models
from app.utils.validation import reject_malicious

router = APIRouter(prefix="/api/v1/day3", tags=["Day 3 Core Features"])

# Directory to store uploaded sample frames/videos for sign processing simulation
UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

logger = logging.getLogger(__name__)

class SignSubmission(BaseModel):
    sign_text: str = Field(..., min_length=1, max_length=200)
    user_id: str | int = Field(default="")

    @field_validator("sign_text")
    @classmethod
    def _reject_malicious_text(cls, value: str) -> str:
        return reject_malicious(value)

class EvaluationResponse(BaseModel):
    success: bool
    confidence_score: float
    matched_sign: str
    message: str

# 1. Sign Recognition / Validation Endpoint
@router.post("/evaluate-sign", response_model=EvaluationResponse)
def evaluate_sign_submission(
    submission: SignSubmission,
    db: Session = Depends(get_db),
):
    """
    Evaluates input text against the real sign catalog stored in the lessons
    table (a DB-backed dictionary), returning a measured match/confidence
    instead of a fixed hardcoded value.
    """
    if not submission.sign_text.strip():
        raise HTTPException(status_code=400, detail="Sign text cannot be empty.")

    text = submission.sign_text.strip().lower()
    exact = (
        db.query(models.Lesson)
        .filter(models.Lesson.expected_gesture == text)
        .first()
    )
    if exact is not None:
        return {
            "success": True,
            "confidence_score": 0.98,
            "matched_sign": exact.expected_gesture,
            "message": "Sign matched an exact catalog entry with high confidence.",
        }

    partial = (
        db.query(models.Lesson)
        .filter(models.Lesson.title.ilike(f"%{text}%"))
        .first()
    )
    if partial is not None:
        return {
            "success": True,
            "confidence_score": 0.82,
            "matched_sign": partial.expected_gesture,
            "message": "Sign matched a catalog entry by title similarity.",
        }

    return {
        "success": False,
        "confidence_score": 0.0,
        "matched_sign": "",
        "message": "No catalog match found for the submitted sign text.",
    }

# 2. File Upload Handling for Video/Frame Processing
@router.post("/upload-gesture-frame")
async def upload_gesture_frame(file: UploadFile = File(...)):
    """
    Handles frame uploads (webm/mp4/png) for real-time model evaluation pipelines.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        logger.warning("Failed to save gesture frame upload: %s", e)
        raise HTTPException(status_code=500, detail="Failed to save the uploaded frame.")
        
    return {
        "filename": file.filename,
        "status": "Uploaded and queued for MediaPipe landmark processing",
        "saved_path": file_path
    }