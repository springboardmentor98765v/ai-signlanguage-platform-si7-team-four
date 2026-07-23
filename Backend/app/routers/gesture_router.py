from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List
import shutil
import os

from app.db.database import get_db
from app.models import models

router = APIRouter(prefix="/api/v1/day3", tags=["Day 3 Core Features"])

# Directory to store uploaded sample frames/videos for sign processing simulation
UPLOAD_DIR = "app/static/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class SignSubmission(BaseModel):
    sign_text: str
    user_id: int

class EvaluationResponse(BaseModel):
    success: bool
    confidence_score: float
    matched_sign: str
    message: str

# 1. Sign Recognition / Validation Simulation Endpoint
@router.post("/evaluate-sign", response_model=EvaluationResponse)
def evaluate_sign_submission(submission: SignSubmission):
    """
    Simulates AI sign language gesture evaluation matching input text 
    against baseline platform dictionary terms.
    """
    if not submission.sign_text.strip():
        raise HTTPException(status_code=400, detail="Sign text cannot be empty.")
    
    # Mocking confidence scoring logic for milestone testing
    mock_confidence = 0.94
    return {
        "success": True,
        "confidence_score": mock_confidence,
        "matched_sign": submission.sign_text.lower(),
        "message": "Sign gesture evaluated successfully with high confidence."
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
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")
        
    return {
        "filename": file.filename,
        "status": "Uploaded and queued for MediaPipe landmark processing",
        "saved_path": file_path
    }