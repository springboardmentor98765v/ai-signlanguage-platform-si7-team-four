import os
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.db.database import get_db
from app.models.models import User
from app.utils.validation import reject_malicious
from app.utils.ratelimit import (
    limiter,
    PASSWORD_RESET_LIMIT,
    PASSWORD_RESET_ERROR_MESSAGE,
)
from app.utils.security import verify_token_and_role
from app.utils.email import send_reset_password_email

router = APIRouter(prefix="/api", tags=["Day 2 Milestone 2 APIs"])

RESET_TOKEN_TTL_MINUTES = 30

class ProfileUpdate(BaseModel):
    username: str | None = Field(default=None, min_length=3, max_length=80)
    email: EmailStr | None = None

    @field_validator("username")
    @classmethod
    def _reject_malicious_username(cls, value):
        if value is None:
            return value
        return reject_malicious(value)

class PasswordChange(BaseModel):
    current_password: str = Field(..., min_length=8, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("current_password", "new_password")
    @classmethod
    def _reject_malicious_password(cls, value: str) -> str:
        return reject_malicious(value)

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str = Field(..., min_length=16, max_length=256)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("token", "new_password")
    @classmethod
    def _reject_malicious_reset(cls, value: str) -> str:
        return reject_malicious(value)

# Dependency: resolve the authenticated user from the Bearer token's user_id.
def get_current_user(
    token_payload: dict = Depends(verify_token_and_role(["Learner", "Instructor", "Accessibility Trainer", "Admin"])),
    db: Session = Depends(get_db),
) -> User:
    user = db.query(User).filter(User.id == token_payload["user_id"]).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# 1. Update Profile API
@router.patch("/users/me")
def update_profile(
    payload: ProfileUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if payload.username:
        user.username = payload.username
    if payload.email:
        user.email = payload.email

    db.commit()
    db.refresh(user)
    return {"message": "Profile updated successfully", "username": user.username, "email": user.email}


# 2. Change Password API
@router.post("/users/change-password")
def change_password(
    payload: PasswordChange,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not bcrypt.checkpw(
        payload.current_password.encode("utf-8"),
        (user.password_hash or "").encode("utf-8"),
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    hashed = bcrypt.hashpw(payload.new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user.password_hash = hashed
    db.commit()
    return {"message": "Password changed successfully"}


# 3. Forgot Password Flow (real DB-backed reset token + email delivery)
@router.post("/auth/forgot-password")
@limiter.limit(PASSWORD_RESET_LIMIT, error_message=PASSWORD_RESET_ERROR_MESSAGE)
def forgot_password(
    request: Request,
    response: Response,
    payload: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")

    reset_token = secrets.token_urlsafe(32)
    user.reset_token_hash = hashlib.sha256(reset_token.encode("utf-8")).hexdigest()
    user.reset_token_expires_at = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_TTL_MINUTES)
    db.commit()

    frontend_url = (os.getenv("FRONTEND_URL") or os.getenv("PUBLIC_BASE_URL") or "http://localhost:5173").rstrip("/")
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"

    delivery = send_reset_password_email(payload.email, reset_link)

    return {
        "message": (
            "If that email is registered, a password reset link has been sent."
            if delivery["method"] == "smtp"
            else "Password reset link generated and printed to the server terminal (SMTP not configured)."
        ),
        "method": delivery["method"],
    }


# 4. Reset Password (consumes the emailed token)
@router.post("/auth/reset-password")
@limiter.limit(PASSWORD_RESET_LIMIT, error_message=PASSWORD_RESET_ERROR_MESSAGE)
def reset_password(
    request: Request,
    response: Response,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
):
    token_hash = hashlib.sha256(payload.token.encode("utf-8")).hexdigest()
    user = db.query(User).filter(User.reset_token_hash == token_hash).first()
    if user is None:
        raise HTTPException(status_code=400, detail="Invalid or already used reset token.")

    expires_at = user.reset_token_expires_at
    if expires_at is None or expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This reset link has expired. Please request a new one.")

    user.password_hash = bcrypt.hashpw(payload.new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    user.reset_token_hash = None
    user.reset_token_expires_at = None
    db.commit()
    return {"message": "Password reset successfully. You can now sign in with your new password."}