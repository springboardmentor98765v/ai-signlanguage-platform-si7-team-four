
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.models import PracticeSession

def start_session(db: Session, user_id: str, lesson_id: str) -> dict:
    session = PracticeSession(
        user_id=user_id,
        lesson_id=lesson_id,
        status="in_progress",
        attempt_count=0,
        started_at=datetime.utcnow(),
        ended_at=None,
        duration_seconds=None,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "user_id": session.user_id,
        "lesson_id": session.lesson_id,
        "status": session.status,
        "attempt_count": session.attempt_count,
        "start_time": session.started_at,
        "end_time": session.ended_at,
        "duration_seconds": session.duration_seconds,
    }

def increment_attempt(db: Session, session_id: str) -> dict | None:
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id
    ).first()

    if session is None or session.status != "in_progress":
        return None

    session.attempt_count += 1

    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "attempt_count": session.attempt_count,
        "status": session.status,
    }

def end_session(db: Session, session_id: str) -> dict | None:
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id
    ).first()

    if session is None:
        return None

    if session.status == "completed":
        return {
            "session_id": session.id,
            "status": session.status,
            "attempt_count": session.attempt_count,
            "start_time": session.started_at,
            "end_time": session.ended_at,
            "duration_seconds": session.duration_seconds,
        }

    session.ended_at = datetime.utcnow()
    session.duration_seconds = (
        session.ended_at - session.started_at
    ).total_seconds()
    session.status = "completed"

    db.commit()
    db.refresh(session)

    return {
        "session_id": session.id,
        "status": session.status,
        "attempt_count": session.attempt_count,
        "start_time": session.started_at,
        "end_time": session.ended_at,
        "duration_seconds": session.duration_seconds,
    }

def get_session(db: Session, session_id: str) -> dict | None:
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id
    ).first()

    if session is None:
        return None

    return {
        "session_id": session.id,
        "user_id": session.user_id,
        "lesson_id": session.lesson_id,
        "status": session.status,
        "attempt_count": session.attempt_count,
        "start_time": session.started_at,
        "end_time": session.ended_at,
        "duration_seconds": session.duration_seconds,
    }

