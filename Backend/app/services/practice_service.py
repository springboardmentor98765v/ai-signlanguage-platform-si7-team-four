
from datetime import datetime
import uuid as uuid_lib

from sqlalchemy.orm import Session

from app.models.models import PracticeSession


def _as_uuid(value):
    """Coerce a value into a canonical hyphenated UUID string.

    Guards against numeric-looking ids (e.g. the frontend sending lesson_id=1).
    SQLite's NUMERIC column affinity stores such values as INTEGER, which then
    breaks the UUID result processor on read (uuid.UUID(int) fails). Mapping
    them to a deterministic UUID keeps every UUID column stored as TEXT.
    """
    if value is None:
        return None
    try:
        return str(uuid_lib.UUID(str(value)))
    except (ValueError, AttributeError, TypeError):
        return str(uuid_lib.uuid5(uuid_lib.NAMESPACE_DNS, str(value)))


def start_session(db: Session, user_id: str, lesson_id: str) -> dict:
    session = PracticeSession(
        user_id=_as_uuid(user_id),
        lesson_id=_as_uuid(lesson_id),
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

