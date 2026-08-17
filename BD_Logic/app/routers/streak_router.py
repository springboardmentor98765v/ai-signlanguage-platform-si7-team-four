from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from fastapi import Depends
import uuid

from app.db.database import get_db
from app.models import models
from app.services import streak_service
from app.schemas.streak import StreakResponse

router = APIRouter(prefix="/streak", tags=["Streak"])


@router.get("/{user_id}", response_model=StreakResponse)
def get_streak(user_id: str, db: Session = Depends(get_db)):
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format.")

    user = db.query(models.User).filter(models.User.id == str(user_uuid)).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    streak_data = streak_service.get_user_streak(db, str(user_uuid))

    return StreakResponse(
        user_id=str(user_uuid),
        current_streak=streak_data["current_streak"],
        longest_streak=streak_data["longest_streak"],
        total_practice_days=streak_data["total_practice_days"],
    )