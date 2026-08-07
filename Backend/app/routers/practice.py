from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from pydantic import BaseModel, Field
from app.db.database import get_db
from app.services import practice_service
from app.models import models
from app.schemas.practice import (
    PracticeSessionResponse,
    PracticeEndResponse,
    PracticeSubmitResponse,
)
import uuid

router = APIRouter(prefix="/api/practice", tags=["Practice Service"])


# Schema representing mock real-time image frame landmarks
class LandmarkPoint(BaseModel):
    x: float = Field(..., ge=-10.0, le=10.0)
    y: float = Field(..., ge=-10.0, le=10.0)
    z: float = Field(..., ge=-10.0, le=10.0)


class FrameSubmissionRequest(BaseModel):
    session_id: str = Field(..., min_length=1, max_length=80)
    landmarks: List[LandmarkPoint] = Field(..., min_length=1, max_length=500)


@router.post(
    "/start",
    response_model=PracticeSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Start a Practice Session",
    description=(
        "Starts a new practice session for a user/lesson pair via the practice "
        "service and returns the created session record with status 'in_progress'."
    ),
)
def start_practice(
    user_id: str,
    lesson_id: str,
    db: Session = Depends(get_db),
):
    """
    Starts a new practice session via the practice service.
    """
    session = practice_service.start_session(db, user_id, lesson_id)
    return session


@router.post(
    "/end",
    response_model=PracticeEndResponse,
    status_code=status.HTTP_200_OK,
    summary="End a Practice Session",
    description=(
        "Ends an existing practice session, recording end time and duration. "
        "Returns 404 if the session does not exist."
    ),
)
def end_practice(
    session_id: str,
    db: Session = Depends(get_db),
):
    """
    Ends an existing practice session via the practice service.
    """
    session = practice_service.end_session(db, session_id)

    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return session


@router.post(
    "/submit",
    response_model=PracticeSubmitResponse,
    status_code=status.HTTP_200_OK,
    summary="Submit a Practice Frame for AI Feedback",
    description=(
        "Submits a set of hand-landmark coordinates for a practice session and "
        "returns mock AI gesture-recognition metrics and feedback. Requires a valid "
        "UUID session_id; 400 if malformed, 404 if the session does not exist."
    ),
)
def submit_practice_frame(payload: FrameSubmissionRequest, db: Session = Depends(get_db)):
    # Convert session_id to UUID object for validation
    try:
        session_uuid = uuid.UUID(payload.session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="session_id must be a valid UUID format.")

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
