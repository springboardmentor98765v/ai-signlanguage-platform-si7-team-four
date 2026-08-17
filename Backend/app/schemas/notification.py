from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.utils.validation import ALLOWED_NOTIFICATION_TYPES, reject_malicious


class NotificationCreate(BaseModel):
    """Payload for creating a new notification (internal/service-to-service)."""

    user_id: str = Field(..., min_length=1, max_length=36)
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=2000)
    event_type: str = Field(
        default="info",
        max_length=50,
        description='Event type, e.g. "badge_earned", "certificate_ready", "recommendation".',
    )

    @field_validator("title", "message")
    @classmethod
    def _reject_malicious_text(cls, value: str) -> str:
        return reject_malicious(value)

    @field_validator("event_type")
    @classmethod
    def _validate_event_type(cls, value: str) -> str:
        reject_malicious(value)
        if value not in ALLOWED_NOTIFICATION_TYPES:
            raise ValueError(
                f"event_type must be one of: {sorted(ALLOWED_NOTIFICATION_TYPES)} "
                f"(got '{value}')."
            )
        return value


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
