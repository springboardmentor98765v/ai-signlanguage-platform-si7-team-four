from fastapi import APIRouter, HTTPException, status, Query, Depends
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/notifications", tags=["Notification Service (Milestone 3)"])

# --- Pydantic Schemas ---
class NotificationCreate(BaseModel):
    user_id: str
    title: str
    message: str
    notification_type: Optional[str] = "info" # info, warning, alert, success

class NotificationResponse(BaseModel):
    notification_id: str
    user_id: str
    title: str
    message: str
    notification_type: str
    is_read: bool
    created_at: str

# --- In-Memory Mock Storage ---
MOCK_NOTIFICATIONS_DB = {}

def seed_sample_notifications():
    samples = [
        {
            "notification_id": "notif_001",
            "user_id": "user_demo_1",
            "title": "Welcome to AI Sign Language Platform!",
            "message": "Start your journey by exploring Module 101 Alphabet lessons.",
            "notification_type": "info",
            "is_read": False,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            "notification_id": "notif_002",
            "user_id": "user_demo_1",
            "title": "Lesson Completed!",
            "message": "You completed The Letter A lesson with 95% accuracy.",
            "notification_type": "success",
            "is_read": True,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    for n in samples:
        MOCK_NOTIFICATIONS_DB[n["notification_id"]] = n

seed_sample_notifications()

# --- Endpoints ---

@router.get("", response_model=List[NotificationResponse], status_code=status.HTTP_200_OK)
def get_user_notifications(
    user_id: Optional[str] = Query(None, description="Filter notifications by user ID"),
    unread_only: bool = Query(False, description="Filter only unread notifications"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100)
):
    """
    Milestone 3 Requirement: Fetch user notifications with unread filtering and pagination.
    """
    notifs = list(MOCK_NOTIFICATIONS_DB.values())
    
    if user_id:
        notifs = [n for n in notifs if n["user_id"] == user_id]
        
    if unread_only:
        notifs = [n for n in notifs if not n["is_read"]]
        
    # Sort newest first
    notifs.sort(key=lambda x: x["created_at"], reverse=True)
    
    paginated = notifs[skip : skip + limit]
    return [NotificationResponse(**n) for n in paginated]

@router.get("/unread-count", status_code=status.HTTP_200_OK)
def get_unread_count(user_id: str = Query(..., description="User ID to get unread count for")):
    """
    Milestone 3 Requirement: Get total count of unread notifications for badge counters.
    """
    count = sum(1 for n in MOCK_NOTIFICATIONS_DB.values() if n["user_id"] == user_id and not n["is_read"])
    return {"user_id": user_id, "unread_count": count}

@router.post("", response_model=NotificationResponse, status_code=status.HTTP_201_CREATED)
def create_notification(payload: NotificationCreate):
    """
    Milestone 3 Requirement: Create and dispatch a new notification to a specific user.
    """
    new_id = f"notif_{uuid.uuid4().hex[:8]}"
    notif_data = {
        "notification_id": new_id,
        "user_id": payload.user_id,
        "title": payload.title,
        "message": payload.message,
        "notification_type": payload.notification_type or "info",
        "is_read": False,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    MOCK_NOTIFICATIONS_DB[new_id] = notif_data
    return NotificationResponse(**notif_data)

@router.patch("/{notification_id}/read", status_code=status.HTTP_200_OK)
def mark_notification_as_read(notification_id: str):
    """
    Milestone 3 Requirement: Mark a specific notification as read.
    """
    if notification_id not in MOCK_NOTIFICATIONS_DB:
        raise HTTPException(status_code=404, detail="Notification not found.")
        
    MOCK_NOTIFICATIONS_DB[notification_id]["is_read"] = True
    return {"message": "Notification marked as read.", "notification_id": notification_id}

@router.delete("/{notification_id}", status_code=status.HTTP_200_OK)
def delete_notification(notification_id: str):
    """
    Milestone 3 Requirement: Delete a notification.
    """
    if notification_id not in MOCK_NOTIFICATIONS_DB:
        raise HTTPException(status_code=404, detail="Notification not found.")
        
    del MOCK_NOTIFICATIONS_DB[notification_id]
    return {"message": f"Notification {notification_id} deleted successfully."}
