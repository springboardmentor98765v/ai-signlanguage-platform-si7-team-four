
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services import practice_service

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models import models
from pydantic import BaseModel
from typing import List
import uuid

router = APIRouter(tags=["Practice Service"])


# Schema for creating a practice session
class PracticeStartRequest(BaseModel):
    user_id: str
    lesson_id: str

# Schema representing mock real-time image frame landmarks
class LandmarkPoint(BaseModel):
    x: float
    y: float
    z: float


@router.post("/start")
def start_practice(
    user_id: str,
    lesson_id: str,
    db: Session = Depends(get_db)
):
    """
    Starts a new practice session via the practice service.
    """
    session = practice_service.start_session(db, user_id, lesson_id)
    return session

class FrameSubmissionRequest(BaseModel):
    session_id: str
    landmarks: List[LandmarkPoint]


@router.post("/start", status_code=status.HTTP_201_CREATED)
def start_practice_session(payload: PracticeStartRequest, db: Session = Depends(get_db)):
    # 1. Validate user_id as a string (keep your UUID validation)
    try:
        user_uuid = uuid.UUID(payload.user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format.")


@router.post("/end")
def end_practice(
    session_id: str,
    db: Session = Depends(get_db)
):
    """
    Ends an existing practice session via the practice service.
    """
    session = practice_service.end_session(db, session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Query user and lesson
    user = db.query(models.User).filter(models.User.id == str(user_uuid)).first()
    
    # We query the lesson directly by the slug string
    lesson = db.query(models.Lesson).filter(models.Lesson.slug == payload.lesson_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # If lesson is None, it means that exact string slug doesn't exist in the DB
    if not lesson:
        raise HTTPException(status_code=404, detail=f"Lesson '{payload.lesson_id}' not found in database.")
        
    # 3. Create Session
    new_session = models.PracticeSession(
        user_id=str(user_uuid),
        lesson_id=lesson.id, # We use the lesson's internal ID
        status="active"
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    
    return {"status": "success", "session_id": str(new_session.id)}

@router.post("/submit", status_code=status.HTTP_200_OK)
def submit_practice_frame(payload: FrameSubmissionRequest, db: Session = Depends(get_db)):
    # Convert session_id to UUID object for validation
    try:
        session_uuid = uuid.UUID(payload.session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="session_id must be a valid UUID format.")

    # Cast to str() here as well to prevent the same AttributeError
    session = db.query(models.PracticeSession).filter(models.PracticeSession.id == str(session_uuid)).first()
    if not session:
        raise HTTPException(status_code=404, detail="Active practice session context missing")
        
    # Mock analysis
    mock_confidence = 96.4
    mock_score = 90.0
    
    session.status = "completed"
    db.commit()
    
    return {
        "status": "success",
        "session_id": str(session.id),
        "metrics": {
            "predicted_sign": "A",
            "confidence_percentage": mock_confidence,
            "overall_accuracy_score": mock_score,
            "hand_shape_match": True
        },
        "feedback": "Keep your thumb closer to the palm for structural clarity."
    }