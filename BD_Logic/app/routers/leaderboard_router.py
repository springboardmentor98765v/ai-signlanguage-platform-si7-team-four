from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.leaderboard_service import get_leaderboard
from app.schemas.leaderboard import LeaderboardResponse

router = APIRouter(tags=["Leaderboard"])


@router.get("/leaderboard", response_model=LeaderboardResponse)
def get_leaderboard_endpoint(
    sort_by: str = Query(default="accuracy"),
    db: Session = Depends(get_db),
):
    if sort_by not in ("accuracy", "streak"):
        raise HTTPException(
            status_code=400,
            detail="sort_by must be 'accuracy' or 'streak'",
        )

    entries = get_leaderboard(db, sort_by)

    return LeaderboardResponse(
        sort_by=sort_by,
        entries=entries,
    )