from fastapi import APIRouter, HTTPException

from app.services import practice_service

router = APIRouter(
    prefix="/practice",
    tags=["practice"]
)


@router.post("/start")
def start_practice():
    """
    Starts a new practice session via the practice service.
    Session tracking (id, status, attempt count, start time) is handled
    in app/services/practice_service.py.
    """
    session = practice_service.start_session()
    return session


@router.post("/end")
def end_practice(session_id: str):
    """
    Ends an existing practice session via the practice service.
    Requires the session_id returned by /practice/start.
    """
    session = practice_service.end_session(session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Session not found")

    return session