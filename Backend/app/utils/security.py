from datetime import datetime, timedelta, timezone
import jwt
import os
from dotenv import load_dotenv
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# --- LOAD ENVIRONMENT VARIABLES ---
load_dotenv()

# Securely load configuration from .env matching SECRET_KEY
JWT_SECRET = os.getenv("SECRET_KEY", os.getenv("JWT_SECRET", "SUPER_SECRET_SIGN_LANGUAGE_KEY_XYZ_123"))
JWT_ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))

security_scheme = HTTPBearer()

def create_access_token(data: dict) -> str:
    """
    Day 4 Deliverable: Encodes a JSON Web Token containing the user payload 
    along with a concrete expiration timestamp.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def create_refresh_token(data: dict) -> str:
    """
    Day 8 Deliverable: Encodes a long-lived refresh token valid for 7 days.
    """
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode.update({"exp": expire})
    
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token_and_role(required_roles: list[str]):
    """
    Day 4 Deliverable: Middleware dependency that validates incoming bearer JWT tokens 
    and checks Role-Based Access Control (RBAC) clearance.
    """
    def dependency(credentials: HTTPAuthorizationCredentials = Depends(security_scheme)):
        token = credentials.credentials
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            user_role = payload.get("role")
            user_id = payload.get("user_id")
            
            if not user_role or not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token structure: Missing role or user identity parameters."
                )
                
            if user_role not in required_roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Access Denied. Your role '{user_role}' does not match required permissions: {required_roles}."
                )
                
            return payload
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication token has expired. Please log in again."
            )
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials signature token."
            )
            
    return dependency