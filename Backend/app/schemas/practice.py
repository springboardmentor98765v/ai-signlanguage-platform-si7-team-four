from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PracticeImageSubmissionRequest(BaseModel):
    """Request body for submitting a base64‑encoded image to the AI service."""
    session_id: str = Field(..., min_length=1, max_length=80)
    image_data: str = Field(..., description="Base64 data URL, e.g. 'data:image/jpeg;base64,...'")


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


class FrameMetrics(BaseModel):
    """Mock AI metrics for a submitted practice frame."""

    predicted_sign: str
    confidence_percentage: float
    overall_accuracy_score: float
    hand_shape_match: bool


class PracticeSubmitResponse(BaseModel):
    """Response body for POST /api/practice/submit."""

    status: str
    session_id: str
    metrics: FrameMetrics
    feedback: str
