from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class PracticeImageSubmissionRequest(BaseModel):
    """Request body for submitting a base64-encoded raw image to the AI service.

    The backend does NOT do landmark extraction here. It decodes the raw image
    and forwards it to the Python AI service (`ai-service:8001/predict`), which
    runs MediaPipe to extract landmarks, builds features, and runs the model.
    `session_id` is optional: if omitted, the backend creates an in-progress
    session from `user_id`/`lesson_id`.
    """
    session_id: Optional[str] = Field(None, min_length=1, max_length=80)
    user_id: Optional[str] = Field(None, min_length=1, max_length=80)
    lesson_id: Optional[str] = Field(None, min_length=1, max_length=80)
    target_letter: Optional[str] = Field(None, min_length=1, max_length=5, description="Expected sign; forwarded to the AI service as target_sign for feedback")
    image_data: str = Field(..., description="Base64 data URL, e.g. 'data:image/jpeg;base64,...'")

    @field_validator("user_id", "lesson_id", "session_id", mode="before")
    @classmethod
    def _coerce_optional_ids(cls, v):
        # The frontend sends lesson_id as an integer (e.g. 1); normalize to string.
        return str(v) if isinstance(v, int) else v


"""
Practice Service response schemas (shown in Swagger /docs).
"""


class PracticeSessionResponse(BaseModel):
    """Full practice-session record returned by POST /api/practice/start."""

    session_id: str
    user_id: str
    lesson_id: str
    status: str
    attempt_count: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class PracticeEndResponse(BaseModel):
    """Record returned by POST /api/practice/end."""

    session_id: str
    status: str
    attempt_count: int
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class PracticeSubmitResponse(BaseModel):
    """Response body for POST /api/practice/submit.

    The prediction fields come straight from the AI service
    (`POST ai-service:8001/predict`), which extracted landmarks with MediaPipe
    and ran them through the trained model.
    """

    status: str
    session_id: str
    predicted_sign: Optional[str] = None
    confidence: float = 0.0
    hand_detected: bool = False
    correct: Optional[bool] = None
    possible_issue: Optional[str] = None
