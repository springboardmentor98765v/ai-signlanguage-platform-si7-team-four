import uuid
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# TEMPORARY IN-MEMORY STORE
# This dict is a PLACEHOLDER only. It stands in for the real database layer
# that Intern 5 will implement (e.g. SQLAlchemy models + a DB session).
# Do not build on this as permanent storage — it resets on every server restart
# and is not safe for concurrent/production use.
# ---------------------------------------------------------------------------
_sessions: dict[str, dict] = {}


def _persist_session(session: dict) -> None:
    """
    Placeholder for Intern 5's database persistence logic.

    Currently a no-op. When the database module is ready, this function
    should be replaced with actual DB writes (e.g. insert/update via
    SQLAlchemy model), and _sessions above can be removed in favor of
    querying the database directly.
    """
    pass


def start_session() -> dict:
    """
    Starts a new practice session.
    - Generates a unique session_id
    - Initializes attempt_count to 0
    - Records start_time
    - Sets status to 'in_progress'
    """
    session_id = str(uuid.uuid4())
    session = {
        "session_id": session_id,
        "status": "in_progress",
        "attempt_count": 0,
        "start_time": datetime.now(timezone.utc),
        "end_time": None,
        "duration_seconds": None,
    }

    _sessions[session_id] = session
    _persist_session(session)

    return session


def increment_attempt(session_id: str) -> dict | None:
    """
    Increments the attempt count for an active session.
    Returns the updated session, or None if the session doesn't exist
    or is already completed.

    Note: No route calls this yet (attempt-triggering logic belongs to a
    later day per the SRS). This function is provided now so session
    tracking is complete, and can be wired into a router later.
    """
    session = _sessions.get(session_id)
    if session is None or session["status"] != "in_progress":
        return None

    session["attempt_count"] += 1
    _persist_session(session)
    return session


def end_session(session_id: str) -> dict | None:
    """
    Ends an active practice session.
    - Records end_time
    - Calculates duration in seconds
    - Sets status to 'completed'
    Returns the updated session, or None if session_id is unknown.
    """
    session = _sessions.get(session_id)
    if session is None:
        return None

    if session["status"] == "completed":
        # Already ended — return as-is rather than overwriting timing data.
        return session

    session["end_time"] = datetime.now(timezone.utc)
    session["duration_seconds"] = (
        session["end_time"] - session["start_time"]
    ).total_seconds()
    session["status"] = "completed"

    _persist_session(session)
    return session


def get_session(session_id: str) -> dict | None:
    """
    Retrieves current session data (status, attempt count, timing).
    Placeholder-store lookup only — will be replaced by a DB query later.
    """
    return _sessions.get(session_id)