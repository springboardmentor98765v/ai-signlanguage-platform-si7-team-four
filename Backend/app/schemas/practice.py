from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

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
