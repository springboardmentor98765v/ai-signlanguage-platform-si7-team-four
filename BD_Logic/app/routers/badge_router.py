from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends
import uuid

from app.db.database import get_db
from app.models import models
from app.services import badge_service
from app.schemas.badge import UserBadgesResponse

router = APIRouter(prefix="/badges", tags=["Badges"])


@router.get("/{user_id}", response_model=UserBadgesResponse)
def get_badges(user_id: str, db: Session = Depends(get_db)):
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format.")

    user = db.query(models.User).filter(models.User.id == str(user_uuid)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    badges = badge_service.get_user_badges(db, str(user_uuid))

    return UserBadgesResponse(user_id=str(user_uuid), badges=badges)