from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.report_service import generate_progress_report, build_progress_report_csv
from app.utils.security import verify_token_and_role

router = APIRouter(
    prefix="/api/reports",
    tags=["Report"],
)


@router.get("/{learner_id}")
def get_progress_report(
    learner_id: str,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token_and_role(["Learner", "Instructor", "Accessibility Trainer", "Admin"])),
):
    try:
        return generate_progress_report(learner_id, db=db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{report_type}/export", summary="Export a progress report as a file")
def export_progress_report(
    report_type: str,
    format: str = Query("csv", pattern="^(csv)$"),
    learner_id: str = Query(..., description="Learner whose report should be exported."),
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token_and_role(["Learner", "Instructor", "Accessibility Trainer", "Admin"])),
):
    if report_type not in {"progress", "translation"}:
        raise HTTPException(status_code=404, detail="Unsupported report type.")

    try:
        report = generate_progress_report(learner_id, db=db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if report_type == "translation":
        raise HTTPException(status_code=404, detail="Translation reports are not yet available.")

    filename = f"progress_report_{learner_id[:8]}.csv"
    return Response(
        content=build_progress_report_csv(report),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )