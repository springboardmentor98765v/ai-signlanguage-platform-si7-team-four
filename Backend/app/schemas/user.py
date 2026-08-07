from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional

from app.utils.validation import ALLOWED_ROLES, reject_malicious

# Schema used when a user registers a new account
class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=80)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    role: Optional[str] = Field(default="Learner", max_length=20)  # Default role is Learner

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
