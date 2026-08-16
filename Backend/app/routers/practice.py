from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services import practice_service
from app.models import models
from app.schemas.practice import (
    PracticeSessionResponse,
    PracticeEndResponse,
    PracticeSubmitResponse,
    PracticeImageSubmissionRequest,
)
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/practice", tags=["Practice Service"])


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
        "Accepts a raw base64-encoded image from the frontend, decodes it, and "
        "forwards it as multipart/form-data to the Python AI service "
        "(`ai-service:8001/predict`). The AI service extracts hand landmarks with "
        "MediaPipe, generates features, and runs the trained model; the resulting "
        "prediction is relayed back to the client. Requires a valid UUID "
        "session_id (or user_id + lesson_id to auto-start one); 400 if the image "
        "data is malformed, 404 if the session does not exist."
    ),
)

def submit_practice_frame(
    payload: PracticeImageSubmissionRequest,
    db: Session = Depends(get_db)
) -> PracticeSubmitResponse:
    """
    Relay a raw hand image to the AI service for prediction.

    Flow enforced here (landmark extraction happens ONLY in the AI service):
        Browser -> raw image (base64) -> /submit -> decode -> multipart ->
        ai-service:8001/predict -> MediaPipe landmarks -> features -> model ->
        prediction -> relayed back.
    """
    session_id = payload.session_id

    if session_id:
        # Validate the provided session belongs to a real practice record.
        try:
            session_uuid = uuid.UUID(session_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="session_id must be a valid UUID format.")
        session = db.query(models.PracticeSession).filter(models.PracticeSession.id == str(session_uuid)).first()
        if not session:
            raise HTTPException(status_code=404, detail="Active practice session context missing")
    else:
        # The frontend may omit session_id; auto-start an in-progress session.
        if not payload.user_id or not payload.lesson_id:
            raise HTTPException(
                status_code=400,
                detail="Either session_id or both user_id and lesson_id are required.",
            )
        session_id = practice_service.start_session(db, payload.user_id, payload.lesson_id)["session_id"]

    # Decode base64 image data (expects a data URL prefix)
    import base64, re
    match = re.match(r"data:image/.+;base64,(.*)", payload.image_data)
    if not match:
        raise HTTPException(status_code=400, detail="Invalid image_data format; must be base64 data URL.")
    try:
        image_bytes = base64.b64decode(match.group(1))
    except Exception:
        raise HTTPException(status_code=400, detail="Failed to decode base64 image.")

    # Forward the RAW image to the AI service (landmark extraction is done there).
    import httpx, os
    ai_url = os.getenv("AI_SERVICE_URL", "http://ai-service:8001").rstrip("/")
    files = {"file": ("image.jpg", image_bytes, "image/jpeg")}
    data = {}
    if payload.target_letter:
        data["target_sign"] = payload.target_letter
    try:
        ai_resp = httpx.post(f"{ai_url}/predict", files=files, data=data, timeout=10.0)
    except Exception as exc:
        logger.warning("AI service request failed: %s", exc)
        raise HTTPException(status_code=502, detail="AI service is unreachable. Please try again shortly.")
    if ai_resp.status_code != 200:
        raise HTTPException(status_code=502, detail="AI service returned an unexpected error.")

    ai = ai_resp.json()
    return PracticeSubmitResponse(
        status="success",
        session_id=session_id,
        predicted_sign=ai.get("predicted_sign"),
        confidence=float(ai.get("confidence") or 0.0),
        hand_detected=bool(ai.get("hand_detected", False)),
        correct=ai.get("correct"),
        possible_issue=ai.get("possible_issue"),
    )
