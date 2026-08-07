from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field, field_validator
import uuid

from app.db.database import get_db
from app.models import models
from app.utils.validation import reject_malicious

router = APIRouter(prefix="/api", tags=["Day 2 Milestone 2 APIs"])

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

# 1. Update Profile API
@router.patch("/users/me")
def update_profile(payload: ProfileUpdate, db: Session = Depends(get_db)):
    user = db.query(models.User).first() 
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if payload.username:
        user.username = payload.username
    if payload.email:
        user.email = payload.email
        
    db.commit()
    db.refresh(user)
    return {"message": "Profile updated successfully", "username": user.username, "email": user.email}

# 2. Change Password API
@router.post("/users/change-password")
def change_password(payload: PasswordChange, db: Session = Depends(get_db)):
    user = db.query(models.User).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.password_hash = payload.new_password 
    db.commit()
    return {"message": "Password changed successfully"}

# 3. Forgot Password Flow (Console Print Method)
@router.post("/auth/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Email not registered")
    
    reset_token = str(uuid.uuid4())
    reset_link = f"http://127.0.0.1:8000/api/auth/reset-password?token={reset_token}"
    
    # Print reset link to terminal console
    print("\n==============================================")
    print(f" [PASSWORD RESET] Reset link for {payload.email}:")
    print(f" {reset_link}")
    print("==============================================\n")
    
    return {"message": "Password reset link generated and printed to server terminal."}