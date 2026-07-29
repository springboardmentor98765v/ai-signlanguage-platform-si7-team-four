from fastapi import APIRouter, HTTPException, status, Depends
from pydantic import BaseModel
from typing import List, Optional
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

@router.delete("/users/{user_id}", status_code=status.HTTP_200_OK)
def delete_single_user(user_id: str, admin_email: Optional[str] = None, db: Session = Depends(get_db)):
    """Milestone 2 & 3: Delete user by ID"""
    if admin_email:
        verify_admin(admin_email, db)
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    db.delete(user)
    db.commit()
    return {"message": f"User {user_id} deleted successfully."}

# --- Milestone 3 Bulk Admin Actions ---

class BulkDeleteRequest(BaseModel):
    user_ids: List[str]

class BulkStatusRequest(BaseModel):
    user_ids: List[str]
    is_active: bool

class BulkRoleRequest(BaseModel):
    user_ids: List[str]
    new_role: str

@router.post("/users/bulk-delete", status_code=status.HTTP_200_OK)
def bulk_delete_users(data: BulkDeleteRequest, admin_email: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Milestone 3 Requirement: Bulk delete multiple users by ID array.
    """
    if admin_email:
        verify_admin(admin_email, db)
    
    deleted_count = 0
    not_found = []
    for uid in data.user_ids:
        user = db.query(User).filter(User.id == uid).first()
        if user:
            db.delete(user)
            deleted_count += 1
        else:
            not_found.append(uid)
            
    db.commit()
    return {
        "message": f"Bulk delete completed. Deleted {deleted_count} users.",
        "deleted_count": deleted_count,
        "not_found_ids": not_found
    }

@router.patch("/users/bulk-status", status_code=status.HTTP_200_OK)
def bulk_update_status(data: BulkStatusRequest, admin_email: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Milestone 3 Requirement: Bulk update active/inactive status across users.
    """
    if admin_email:
        verify_admin(admin_email, db)
        
    updated_count = 0
    for uid in data.user_ids:
        user = db.query(User).filter(User.id == uid).first()
        if user:
            user.is_active = data.is_active
            updated_count += 1
            
    db.commit()
    return {
        "message": f"Bulk status update completed for {updated_count} users to active={data.is_active}.",
        "updated_count": updated_count
    }

@router.patch("/users/bulk-role", status_code=status.HTTP_200_OK)
def bulk_update_roles(data: BulkRoleRequest, admin_email: Optional[str] = None, db: Session = Depends(get_db)):
    """
    Milestone 3 Requirement: Bulk update user roles across multiple accounts.
    """
    if admin_email:
        verify_admin(admin_email, db)
        
    updated_count = 0
    for uid in data.user_ids:
        user = db.query(User).filter(User.id == uid).first()
        if user:
            user.role = data.new_role
            updated_count += 1
            
    db.commit()
    return {
        "message": f"Bulk role update completed for {updated_count} users to role={data.new_role}.",
        "updated_count": updated_count
    }