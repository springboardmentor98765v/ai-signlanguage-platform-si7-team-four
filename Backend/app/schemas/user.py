from pydantic import BaseModel, EmailStr
from typing import Optional

# Schema used when a user registers a new account
class UserRegister(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: Optional[str] = "Learner"  # Default role is set to Learner

# Schema used when a user logs in
class UserLogin(BaseModel):
    email: EmailStr
    password: str