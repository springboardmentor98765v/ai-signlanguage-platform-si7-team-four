from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services import practice_service

router = APIRouter(
    prefix="/practice",
    tags=["practice"]
)


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

    return session