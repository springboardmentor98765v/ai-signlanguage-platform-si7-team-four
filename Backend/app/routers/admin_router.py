from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User

router = APIRouter(prefix="/api/admin", tags=["Admin Management"])

def verify_admin(admin_email: str, db: Session = Depends(get_db)):
    admin_user = db.query(User).filter(User.email == admin_email).first()
    if not admin_user or admin_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access denied. Admin privileges required."
        )
    return admin_user

# Pydantic schemas for request bodies
class StatusUpdateRequest(BaseModel):
    target_email: str
    is_active: bool

class RoleUpdateRequest(BaseModel):
    target_email: str
    new_role: str

@router.get("/users", status_code=status.HTTP_200_OK)
def list_all_users(admin_email: str, db: Session = Depends(get_db)):
    """Checkpoint 1: Get all users API"""
    verify_admin(admin_email, db)
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "is_active": getattr(u, "is_active", True),
            "created_at": u.created_at
        } for u in users
    ]

@router.patch("/user-status", status_code=status.HTTP_200_OK)
def update_user_status(data: StatusUpdateRequest, admin_email: str, db: Session = Depends(get_db)):
    """Checkpoint 2: Activate/Deactivate user API"""
    verify_admin(admin_email, db)
    user = db.query(User).filter(User.email == data.target_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Target user not found.")
    
    user.is_active = data.is_active
    db.commit()
    return {"message": f"User status successfully updated to active={data.is_active}", "email": user.email}

@router.patch("/user-role", status_code=status.HTTP_200_OK)
def update_user_role(data: RoleUpdateRequest, admin_email: str, db: Session = Depends(get_db)):
    """Checkpoint 3: Change user role API"""
    verify_admin(admin_email, db)
    user = db.query(User).filter(User.email == data.target_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="Target user not found.")
        
    user.role = data.new_role
    db.commit()
    return {"message": f"User role successfully changed to {data.new_role}", "email": user.email}