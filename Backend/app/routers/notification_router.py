"""
Milestone 3 - Day 2: Notification Service Router
-------------------------------------------------
Implements the database-backed notification APIs:
  - POST  /api/notifications                        -> create a notification
  - GET   /api/notifications/{user_id}              -> list a user's notifications, newest first
  - PATCH /api/notifications/{notification_id}/read -> mark a single notification as read

Checkpoints completed:
  [x] Notifications table created
  [x] 'Create notification' API working
  [x] 'Get my notifications' API working
  [x] 'Mark as read' API working
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import Notification
from app.schemas.notification import NotificationCreate, NotificationOut

router = APIRouter(prefix="/api/notifications", tags=["Notifications"])


@router.post(
    "",
    response_model=NotificationOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create Notification",
    description="Milestone 3 Day 2: Create and persist a new notification for a user (internal/service-to-service use).",
)
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new notification and save it to the notifications table.
    Returns the created notification record.
    """
    if not payload.user_id.strip():
        raise HTTPException(status_code=400, detail="user_id cannot be empty.")
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="title cannot be empty.")
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty.")

    new_notif = Notification(
        user_id=payload.user_id.strip(),
        title=payload.title.strip(),
        message=payload.message.strip(),
        event_type=(payload.event_type or "info").strip() or "info",
        is_read=False,
    )
    db.add(new_notif)
    db.commit()
    db.refresh(new_notif)

    return NotificationOut.model_validate(new_notif)


@router.get(
    "/{user_id}",
    response_model=list[NotificationOut],
    status_code=status.HTTP_200_OK,
    summary="Get My Notifications",
    description="Milestone 3 Day 2: List all notifications for a specific user, newest first.",
)
def get_user_notifications(
    user_id: str,
    db: Session = Depends(get_db),
):
    """
    Retrieve all notifications for a specific user from the database.
    Returns the newest notifications first.
    """
    notifications = (
        db.query(Notification)
        .filter(Notification.user_id == user_id)
        .order_by(Notification.created_at.desc())
        .all()
    )

    return [NotificationOut.model_validate(n) for n in notifications]


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationOut,
    status_code=status.HTTP_200_OK,
    summary="Mark Notification as Read",
    description="Milestone 3 Day 2: Mark a specific notification as read in the database.",
)
def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
):
    """
    Mark the specified notification as read in the database.
    Returns the updated notification record.
    """
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with id '{notification_id}' not found.",
        )

    if notif.is_read:
        return NotificationOut.model_validate(notif)

    notif.is_read = True
    db.commit()
    db.refresh(notif)

    return NotificationOut.model_validate(notif)
