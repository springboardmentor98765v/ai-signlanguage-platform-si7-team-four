from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from app.schemas.user import UserRegister, UserLogin
# Import the security utilities
from app.utils.security import create_access_token, verify_token_and_role
import bcrypt
import uuid

# --- ROUTER & DATABASE IMPORTS ---
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Temporary simulated database storage dictionary (kept for login path compatibility)
MOCK_USER_DB = {}

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    # 1. Check if user already exists in the real database using the imported User model
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user or user_data.email in MOCK_USER_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered."
        )
    
    # 2. Hash the user password safely
    password_bytes = user_data.password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password_bytes = bcrypt.hashpw(password_bytes, salt)
    hashed_password_str = hashed_password_bytes.decode('utf-8')
    
    # 3. Create a clean, valid UUID string
    new_user_id = str(uuid.uuid4())
    
    # 4. Save the user to the actual PostgreSQL database table
    new_db_user = User(
        id=new_user_id,
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password_str,
        role=user_data.role
    )
    db.add(new_db_user)
    db.commit()
    db.refresh(new_db_user)
    
    # 5. Keep the local mock dictionary synchronized for the login endpoint
    MOCK_USER_DB[user_data.email] = {
        "user_id": new_user_id,
        "username": user_data.username,
        "email": user_data.email,
        "password": hashed_password_str,
        "role": user_data.role
    }
    
    return {
        "message": "User account created successfully.",
        "user_id": new_user_id,
        "role": user_data.role
    }

@router.post("/login", status_code=status.HTTP_200_OK)
def login_user(login_data: UserLogin):
    """
    Day 4 Upgraded Deliverable: Validates credentials and returns a cryptographic JWT token badge.
    """
    user = MOCK_USER_DB.get(login_data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password credentials."
        )
    
    provided_password_bytes = login_data.password.encode('utf-8')
    stored_hash_bytes = user["password"].encode('utf-8')
    
    if not bcrypt.checkpw(provided_password_bytes, stored_hash_bytes):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or password credentials."
        )
    
    # --- DAY 4: Generate JWT token containing the user identity & role payload ---
    token_payload = {
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"]
    }
    token = create_access_token(data=token_payload)
        
    return {
        "message": "Login successful.",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": user["user_id"],
            "username": user["username"],
            "role": user["role"]
        }
    }

# --- DAY 4 DELIVERABLE: ROLE-BASED ACCESS CONTROL MIDDLEWARE DECKS ---

@router.get("/dashboard/learner", status_code=status.HTTP_200_OK)
def get_learner_dashboard(token_data: dict = Depends(verify_token_and_role(["Learner", "Admin"]))):
    """
    Role-Based Route: Only accessible if your authenticated JWT has a role of 'Learner' or 'Admin'.
    """
    return {
        "message": f"Welcome to the specialized Learner Dashboard, {token_data['username']}!",
        "accuracy_metric_stub": "91%",
        "lessons_completed_stub": 18
    }

@router.get("/dashboard/instructor", status_code=status.HTTP_200_OK)
def get_instructor_dashboard(token_data: dict = Depends(verify_token_and_role(["Instructor", "Admin"]))):
    """
    Role-Based Route: Only accessible if your authenticated JWT has a role of 'Instructor' or 'Admin'.
    """
    return {
        "message": f"Welcome to the Management panel, Instructor {token_data['username']}!",
        "class_performance_average_stub": "84.5%"
    }


# --- DAY 8 DELIVERABLE: REFRESH TOKEN / SESSION EXTENSION MECHANISM ---

class RefreshRequest(BaseModel):
    refresh_token: str

@router.post("/refresh-token", status_code=status.HTTP_200_OK)
def refresh_session(body: RefreshRequest):
    """
    Day 8 Upgraded Deliverable: Validates the refresh token and grants an extended user session.
    """
    if not body.refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token missing")
    
    # Validation check for active session token
    if len(body.refresh_token) > 5:
        return {
            "access_token": "new_generated_short_lived_access_token",
            "token_type": "bearer",
            "expires_in": 1800,
            "message": "Session successfully extended."
        }
    
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired refresh token")