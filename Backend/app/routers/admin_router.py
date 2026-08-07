from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File
from pydantic import BaseModel
from typing import List, Optional
import csv
import io
import uuid

from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.models import User, Lesson

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

# --- Milestone 3 - Day 4: Bulk admin actions ---

class BulkUserStatusRequest(BaseModel):
    user_ids: List[str]
    is_active: bool


@router.post("/bulk-user-status", status_code=status.HTTP_200_OK)
def bulk_user_status(data: BulkUserStatusRequest, admin_email: str, db: Session = Depends(get_db)):
    """
    Milestone 3 Day 4: Activate/deactivate many users in one call.

    Accepts a list of user IDs (or emails) plus an is_active bool. Updates all
    matching users and reports how many were updated and which were not found.
    """
    verify_admin(admin_email, db)

    updated = []
    not_found = []
    for identifier in data.user_ids:
        # Match by UUID/ID first, then fall back to email.
        user = db.query(User).filter(User.id == identifier).first()
        if user is None:
            user = db.query(User).filter(User.email == identifier).first()

        if user is None:
            not_found.append(identifier)
        else:
            user.is_active = data.is_active
            updated.append(user.id)

    db.commit()

    return {
        "message": f"Bulk status update completed. Updated {len(updated)} user(s) to active={data.is_active}.",
        "is_active": data.is_active,
        "updated_count": len(updated),
        "updated_user_ids": updated,
        "not_found": not_found,
        "not_found_count": len(not_found),
    }


@router.post("/bulk-upload-lessons", status_code=status.HTTP_200_OK)
async def bulk_upload_lessons(
    file: UploadFile = File(...),
    admin_email: str = "",
    db: Session = Depends(get_db),
):
    """
    Milestone 3 Day 4: Bulk upload lessons from an uploaded CSV file.

    Uses Python's built-in csv module (no paid tools, per SRS golden rule).
    Expected CSV header:
        title,description,expected_gesture,category,difficulty,module_id

    Each row is validated; valid rows are inserted as Lesson records. Returns a
    summary of rows processed / inserted / rejected (with reasons).
    """
    verify_admin(admin_email, db)

    raw = await file.read()
    text = raw.decode("utf-8-sig")

    reader = csv.DictReader(io.StringIO(text))
    expected_headers = {"title", "description", "expected_gesture", "category", "difficulty", "module_id"}
    provided_headers = {h.strip() for h in (reader.fieldnames or [])}

    if not expected_headers.issubset(provided_headers):
        missing = sorted(expected_headers - provided_headers)
        raise HTTPException(
            status_code=400,
            detail=f"CSV is missing required column(s): {missing}. Expected: {sorted(expected_headers)}",
        )

    processed = 0
    inserted = 0
    rejected = []

    for row_num, row in enumerate(reader, start=1):
        processed += 1
        # Header rows are DictReader fieldnames; data rows come here.
        title = (row.get("title") or "").strip()
        description = (row.get("description") or "").strip() or None
        expected_gesture = (row.get("expected_gesture") or "").strip()
        category = (row.get("category") or "").strip()
        difficulty = (row.get("difficulty") or "").strip()
        module_id = (row.get("module_id") or "").strip()

        reasons = []
        if not title:
            reasons.append("missing title")
        if not expected_gesture:
            reasons.append("missing expected_gesture")
        elif len(expected_gesture) > 5:
            reasons.append(f"expected_gesture too long ({len(expected_gesture)} > 5)")
        if not category:
            reasons.append("missing category")
        if not difficulty:
            reasons.append("missing difficulty")
        if not module_id:
            reasons.append("missing module_id")
        else:
            try:
                uuid.UUID(module_id)
            except ValueError:
                reasons.append(f"module_id '{module_id}' is not a valid UUID")

        if reasons:
            rejected.append({"row": row_num, "reason": "; ".join(reasons)})
            continue

        new_lesson = Lesson(
            module_id=module_id,
            title=title,
            description=description,
            expected_gesture=expected_gesture,
            category=category,
            difficulty=difficulty,
        )
        db.add(new_lesson)
        inserted += 1

    db.commit()

    return {
        "message": f"CSV bulk upload complete: {inserted} lesson(s) inserted.",
        "rows_processed": processed,
        "rows_inserted": inserted,
        "rows_rejected": len(rejected),
        "rejected_rows": rejected,
    }