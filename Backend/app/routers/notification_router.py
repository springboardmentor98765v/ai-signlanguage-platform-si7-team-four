"""
Milestone 3 - Day 2: Notification Service Router
-------------------------------------------------
Implements fully database-backed notification APIs:
  - POST   /api/notifications        -> Create a notification
  - GET    /api/notifications/me     -> Get my notifications (by user_id)
  - PATCH  /api/notifications/{id}/read -> Mark a notification as read
  - GET    /api/notifications/unread-count -> Unread badge count
  - DELETE /api/notifications/{id}   -> Delete a notification

Checkpoints completed:
  [x] Notifications table created (with Intern 5)
  [x] 'Create notification' API working
  [x] 'Get my notifications' API working
  [x] 'Mark as read' API working
"""

from fastapi import APIRouter, HTTPException, status, Query, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from app.db.database import get_db
from app.models.models import Notification

router = APIRouter(prefix="/api/notifications", tags=["Notification Service (Milestone 3 - Day 2)"])


# ─────────────────────────────────────────
# Pydantic Schemas
# ─────────────────────────────────────────

class NotificationCreate(BaseModel):
    """Schema for creating a new notification."""
    user_id: str
    title: str
    message: str
    notification_type: Optional[str] = "info"   # info | success | warning | alert


class NotificationResponse(BaseModel):
    """Schema for returning a notification to the client."""
    id: str
    user_id: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: str

    class Config:
        from_attributes = True

    @classmethod
    def from_orm_obj(cls, obj: Notification) -> "NotificationResponse":
        return cls(
            id=obj.id,
            user_id=obj.user_id,
            title=obj.title,
            message=obj.message,
            notification_type=obj.notification_type,
            is_read=obj.is_read,
            created_at=obj.created_at.strftime("%Y-%m-%d %H:%M:%S") if obj.created_at else "",
        )


# ─────────────────────────────────────────
# Checkpoint 2: 'Create notification' API
# ─────────────────────────────────────────

@router.post(
    "",
    response_model=NotificationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Notification",
    description="Milestone 3 Day 2 - Checkpoint 2: Create and persist a new notification for a user.",
)
def create_notification(
    payload: NotificationCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new notification and save it to the notifications database table.
    Returns the created notification record.
    """
    if not payload.user_id.strip():
        raise HTTPException(status_code=400, detail="user_id cannot be empty.")
    if not payload.title.strip():
        raise HTTPException(status_code=400, detail="title cannot be empty.")
    if not payload.message.strip():
        raise HTTPException(status_code=400, detail="message cannot be empty.")

    allowed_types = {"info", "success", "warning", "alert"}
    notif_type = (payload.notification_type or "info").lower()
    if notif_type not in allowed_types:
        notif_type = "info"

    new_notif = Notification(
        user_id=payload.user_id.strip(),
        title=payload.title.strip(),
        message=payload.message.strip(),
        notification_type=notif_type,
        is_read=False,
        created_at=datetime.utcnow(),
    )
    db.add(new_notif)
    db.commit()
    db.refresh(new_notif)

    return NotificationResponse.from_orm_obj(new_notif)


# ─────────────────────────────────────────
# Checkpoint 3: 'Get my notifications' API
# ─────────────────────────────────────────

@router.get(
    "/me",
    response_model=List[NotificationResponse],
    status_code=status.HTTP_200_OK,
    summary="Get My Notifications",
    description="Milestone 3 Day 2 - Checkpoint 3: List all notifications for a specific user, with optional unread filter.",
)
def get_my_notifications(
    user_id: str = Query(..., description="The user ID whose notifications to fetch"),
    unread_only: bool = Query(False, description="If true, return only unread notifications"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Max notifications to return"),
    db: Session = Depends(get_db),
):
    """
    Retrieve all notifications for a specific user from the database.
    Supports unread-only filtering and pagination.
    Returns newest notifications first.
    """
    query = db.query(Notification).filter(Notification.user_id == user_id)

    if unread_only:
        query = query.filter(Notification.is_read == False)  # noqa: E712

    notifications = (
        query.order_by(Notification.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [NotificationResponse.from_orm_obj(n) for n in notifications]


# ─────────────────────────────────────────
# Checkpoint 4: 'Mark as read' API
# ─────────────────────────────────────────

@router.patch(
    "/{notification_id}/read",
    status_code=status.HTTP_200_OK,
    summary="Mark Notification as Read",
    description="Milestone 3 Day 2 - Checkpoint 4: Mark a specific notification as read in the database.",
)
def mark_notification_as_read(
    notification_id: str,
    db: Session = Depends(get_db),
):
    """
    Mark the specified notification as read in the database.
    Returns confirmation with the updated notification ID.
    """
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with id '{notification_id}' not found.",
        )

    if notif.is_read:
        return {
            "message": "Notification was already marked as read.",
            "notification_id": notification_id,
            "is_read": True,
        }

    notif.is_read = True
    db.commit()
    db.refresh(notif)

    return {
        "message": "Notification successfully marked as read.",
        "notification_id": notification_id,
        "is_read": notif.is_read,
    }


# ─────────────────────────────────────────
# Supporting endpoints
# ─────────────────────────────────────────

@router.get(
    "/unread-count",
    status_code=status.HTTP_200_OK,
    summary="Get Unread Notification Count",
    description="Returns total count of unread notifications for a user (for badge counters).",
)
def get_unread_count(
    user_id: str = Query(..., description="User ID to get unread count for"),
    db: Session = Depends(get_db),
):
    count = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)  # noqa: E712
        .count()
    )
    return {"user_id": user_id, "unread_count": count}


@router.delete(
    "/{notification_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Notification",
    description="Permanently delete a notification by ID from the database.",
)
def delete_notification(
    notification_id: str,
    db: Session = Depends(get_db),
):
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notif:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with id '{notification_id}' not found.",
        )

    db.delete(notif)
    db.commit()
    return {"message": f"Notification '{notification_id}' deleted successfully."}
