from fastapi import APIRouter, HTTPException, status, Depends
from app.schemas.user import UserRegister, UserLogin
# Import the new Day 4 security utilities
from app.utils.security import create_access_token, verify_token_and_role
import bcrypt

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# Temporary simulated database storage dictionary
MOCK_USER_DB = {}

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserRegister):
    if user_data.email in MOCK_USER_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered."
        )
    
    password_bytes = user_data.password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed_password_bytes = bcrypt.hashpw(password_bytes, salt)
    hashed_password_str = hashed_password_bytes.decode('utf-8')
    
    new_user_id = f"usr_{len(MOCK_USER_DB) + 1001}"
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