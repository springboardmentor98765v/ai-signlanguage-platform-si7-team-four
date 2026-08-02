from fastapi import APIRouter, HTTPException

from app.services import analytics_service

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)


@router.get("/{learner_id}")
def get_analytics(learner_id: str):
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

    return analytics_service.get_learner_analytics(learner_id)