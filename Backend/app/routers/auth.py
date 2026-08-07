import os
from dotenv import load_dotenv
from fastapi import APIRouter, HTTPException, status, Depends, Request, Response
from pydantic import BaseModel
from app.schemas.user import UserRegister, UserLogin
# Import security utilities and shared secrets directly from security.py to avoid key mismatches
from app.utils.security import create_access_token, create_refresh_token, verify_token_and_role, JWT_SECRET, JWT_ALGORITHM
from app.utils.ratelimit import (
    limiter,
    LOGIN_LIMIT,
    REGISTER_LIMIT,
    LOGIN_ERROR_MESSAGE,
    REGISTER_ERROR_MESSAGE,
)
import bcrypt
import uuid
import jwt 

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()

# Synchronize keys with security.py
SECRET_KEY = JWT_SECRET
ALGORITHM = JWT_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# --- ROUTER & DATABASE IMPORTS ---
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Temporary simulated database storage dictionary (kept for login path compatibility)
MOCK_USER_DB = {}

@router.post("/register", status_code=status.HTTP_201_CREATED)
@limiter.limit(REGISTER_LIMIT, error_message=REGISTER_ERROR_MESSAGE)
def register_user(
    request: Request,
    response: Response,
    user_data: UserRegister,
    db: Session = Depends(get_db),
):
    # 1. Check if user already exists in the real database using the imported User model
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user or user_data.email in MOCK_USER_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User account already exists with this email."
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
        "message": "User registered successfully.",
        "user_id": new_user_id,
        "role": user_data.role
    }

@router.post("/login", status_code=status.HTTP_200_OK)
@limiter.limit(LOGIN_LIMIT, error_message=LOGIN_ERROR_MESSAGE)
def login_user(
    request: Request,
    response: Response,
    login_data: UserLogin,
    db: Session = Depends(get_db),
):
    """
    Day 4 Upgraded Deliverable: Validates credentials and returns cryptographic access & refresh tokens.
    """
    # Fallback to check real database if MOCK_USER_DB was wiped on server restart
    user_record = MOCK_USER_DB.get(login_data.email)
    
    if not user_record:
        db_user = db.query(User).filter(User.email == login_data.email).first()
        if db_user:
            # Re-sync into mock dict dynamically so login succeeds
            MOCK_USER_DB[db_user.email] = {
                "user_id": str(db_user.id),
                "username": db_user.username,
                "email": db_user.email,
                "password": db_user.password_hash,
                "role": db_user.role
            }
            user_record = MOCK_USER_DB.get(login_data.email)

    if not user_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password provided."
        )
    
    provided_password_bytes = login_data.password.encode('utf-8')
    stored_hash_bytes = user_record["password"].encode('utf-8')
    
    if not bcrypt.checkpw(provided_password_bytes, stored_hash_bytes):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password provided."
        )
    
    # --- Generate token payload containing user identity & role ---
    token_payload = {
        "user_id": user_record["user_id"],
        "username": user_record["username"],
        "role": user_record["role"]
    }
    
    # Generate both short-lived access token and long-lived refresh token
    access_token = create_access_token(data=token_payload)
    refresh_token = create_refresh_token(data=token_payload)
        
    return {
        "message": "Login successful.",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "user_id": user_record["user_id"],
            "username": user_record["username"],
            "role": user_record["role"]
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
    Day 8 Upgraded Deliverable: Validates the real refresh token and issues a fresh short-lived access token.
    """
    if not body.refresh_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Refresh token is missing."
        )
    
    try:
        # Decode and verify the refresh token using the synchronized key and algorithm
        payload = jwt.decode(body.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("user_id")
        username: str = payload.get("username")
        role: str = payload.get("role")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, 
                detail="Invalid refresh token payload."
            )
        
        # Create a brand new short-lived access token
        new_token_payload = {
            "user_id": user_id,
            "username": username,
            "role": role
        }
        new_access_token = create_access_token(data=new_token_payload)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "message": "Session successfully extended."
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Refresh token has expired. Please log in again."
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid or malformed refresh token provided."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )