"""
Milestone 3 - Day 3: Server-side Notification Hook Service
-----------------------------------------------------------
Reusable helper that inserts a Notification row directly into the database.

This is the internal contract other services (certificate, assessment, practice,
recommendation, and later Intern 4's business-logic code) use to raise platform
events without an HTTP round trip.

Agreed event types (see Backend/milestone3_api_plan.md):
  - "badge_earned"
  - "certificate_ready"
  - "new_recommendation"
"""

from sqlalchemy.orm import Session

from app.models.models import Notification


def create_notification(
    db: Session,
    user_id: str,
    title: str,
    message: str,
    event_type: str = "info",
) -> Notification:
    """
    Insert a new Notification row for the given user and return it.

    Args:
        db: Active SQLAlchemy session.
        user_id: Target user's UUID (string).
        title: Short notification title.
        message: Full notification body.
        event_type: Contract event type, e.g. "badge_earned",
            "certificate_ready", "new_recommendation", or "info".

    Returns:
        The persisted Notification object.
    """
    new_notif = Notification(
        user_id=user_id,
        title=title,
        message=message,
        event_type=event_type,
        is_read=False,
    )
    db.add(new_notif)
    db.commit()
    db.refresh(new_notif)
    return new_notif
