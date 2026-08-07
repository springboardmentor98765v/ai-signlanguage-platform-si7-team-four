from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class NotificationCreate(BaseModel):
    """Payload for creating a new notification (internal/service-to-service)."""

    user_id: str = Field(..., description="Target user's UUID.")
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1)
    event_type: str = Field(
        default="info",
        description='Event type, e.g. "badge_earned", "certificate_ready", "recommendation".',
    )


class NotificationOut(BaseModel):
    """Serialized notification returned to clients."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    title: str
    message: str
    event_type: str
    is_read: bool
    created_at: Optional[datetime] = None
