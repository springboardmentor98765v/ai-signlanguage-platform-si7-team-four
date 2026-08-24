from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import List, Optional

from app.utils.validation import ALLOWED_ROLES, reject_malicious

# Schema used when a user registers a new account
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: Optional[str] = Field(default="Learner", max_length=30)  # Default role is Learner

    @field_validator("username", "password")
    @classmethod
    def _reject_malicious_text(cls, value: str) -> str:
        return reject_malicious(value)

    @field_validator("role")
    @classmethod
    def _validate_role(cls, value: str) -> str:
        reject_malicious(value)
        if value not in ALLOWED_ROLES:
            raise ValueError(
                f"role must be one of: {sorted(ALLOWED_ROLES)} (got '{value}')."
            )
        return value


# Schema used when a user logs in
class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)

    @field_validator("password")
    @classmethod
    def _reject_malicious_password(cls, value: str) -> str:
        return reject_malicious(value)


# --- Response schemas (shown in Swagger /docs) ---

class UserSummary(BaseModel):
    """Identity fields embedded in auth responses."""

    user_id: str
    username: str
    role: str


class RegisterResponse(BaseModel):
    """Response body for POST /api/auth/register."""

    message: str
    user_id: str
    role: str


class LoginResponse(BaseModel):
    """Response body for POST /api/auth/login."""

    message: str
    access_token: str
    refresh_token: str
    token_type: str
    user: UserSummary


class RefreshTokenResponse(BaseModel):
    """Response body for POST /api/auth/refresh-token."""

    access_token: str
    token_type: str
    message: str


class RecentActivity(BaseModel):
    """One recent practice attempt rendered on the learner dashboard."""

    id: str
    sign: str
    score: float
    date: str


class LearnerDashboardResponse(BaseModel):
    """Response body for GET /api/auth/dashboard/learner.

    All values are computed live from the learner's persisted
    practice/assessment records — there are no stub metrics.
    """

    message: str
    learner_name: str = ""
    accuracy_average: float = 0.0
    completed_lessons: int = 0
    # Legacy aliases kept for older clients/tests; mirror the values above.
    accuracy_metric: float = 0.0
    lessons_completed: int = 0
    current_streak_days: int = 0
    target_sign: str = "A"
    recent_activities: List[RecentActivity] = []


class InstructorDashboardResponse(BaseModel):
    """Response body for GET /api/auth/dashboard/instructor."""

    message: str
    class_performance_average: float
