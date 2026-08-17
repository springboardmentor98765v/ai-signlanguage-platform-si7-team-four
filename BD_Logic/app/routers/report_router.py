from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os

from app.services.report_service import (
    generate_progress_report,
    export_progress_report_csv,
    export_class_summary_csv,
)

router = APIRouter(
    prefix="/report",
    tags=["Report"]
)


@router.get("/class-summary/export")
def export_class_summary():
    try:
        file_path = export_class_summary_csv()

        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="text/csv",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{learner_id}/export")
def export_progress_report(learner_id: str):
    try:
        file_path = export_progress_report_csv(learner_id)

        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="text/csv",
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{learner_id}")
def get_progress_report(learner_id: str):
    try:
        return generate_progress_report(learner_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))