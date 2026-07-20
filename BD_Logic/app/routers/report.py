from fastapi import APIRouter, HTTPException

from app.services.report_service import generate_progress_report

router = APIRouter(
    prefix="/report",
    tags=["Report"]
)


@router.get("/{learner_id}")
def get_progress_report(learner_id: str):
    try:
        return generate_progress_report(learner_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))