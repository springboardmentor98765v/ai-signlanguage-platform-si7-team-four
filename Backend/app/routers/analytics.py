from fastapi import APIRouter, Depends, HTTPException, Query

from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services import analytics_service

router = APIRouter(
    prefix="/api/analytics",
    tags=["Analytics"]
)


@router.get("/dashboard/{user_id}")
def get_dashboard(user_id: str, db: Session = Depends(get_db)):
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")
    return analytics_service.get_learner_dashboard(db, user_id)


@router.get("/leaderboard")
def get_leaderboard(
    sort: str = Query("accuracy", pattern="^(accuracy|streak)$"),
    user_id: str = Query(None),
    db: Session = Depends(get_db),
):
    return analytics_service.get_leaderboard(db, sort=sort, user_id=user_id)


@router.get("/{learner_id}")
def get_analytics(learner_id: str, db: Session = Depends(get_db)):
    """
    Returns summary analytics for a learner:
    - Average accuracy
    - Lessons completed
    - Weak-letter list
    """
    if not learner_id:
        raise HTTPException(
            status_code=400,
            detail="learner_id is required"
        )

    return analytics_service.get_learner_analytics_db(db, learner_id)