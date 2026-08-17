from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from app.db.database import get_db

from app.services.report_service import (
    generate_progress_report,
    export_progress_report_csv,
    export_class_summary_csv,
    export_progress_report_pdf,
    export_progress_report_excel,
    generate_accuracy_report,
    export_accuracy_report_pdf,
    export_accuracy_report_excel,
    generate_certification_report,
    export_certification_report_pdf,
    export_certification_report_excel,
    generate_learning_report,
    export_learning_report_pdf,
    export_learning_report_excel,
    generate_assessment_report,
    export_assessment_report_pdf,
    export_assessment_report_excel,
)


router = APIRouter(
    prefix="/report",
    tags=["Report"],
)


@router.get("/class-summary/export")
def export_class_summary(
    db: Session = Depends(get_db),
):
    try:
        file_path = export_class_summary_csv(db)

        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="text/csv",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/{learner_id}/assessment")
def get_assessment_report(
    learner_id: str,
    db: Session = Depends(get_db),
):
    try:
        return generate_assessment_report(
            db,
            learner_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/{learner_id}/assessment/export/pdf")
def export_assessment_report_pdf_route(
    learner_id: str,
    db: Session = Depends(get_db),
):
    try:
        file_path = export_assessment_report_pdf(
            db,
            learner_id,
        )

        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="application/pdf",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/{learner_id}/assessment/export/excel")
def export_assessment_report_excel_route(
    learner_id: str,
    db: Session = Depends(get_db),
):
    try:
        file_path = export_assessment_report_excel(
            db,
            learner_id,
        )

        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/{learner_id}/certification")
def get_certification_report(
    learner_id: str,
    db: Session = Depends(get_db),
):
    try:
        return generate_certification_report(
            db,
            learner_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/{learner_id}/certification/export/pdf")
def export_certification_report_pdf_route(
    learner_id: str,
    db: Session = Depends(get_db),
):
    try:
        file_path = export_certification_report_pdf(
            db,
            learner_id,
        )

        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="application/pdf",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/{learner_id}/certification/export/excel")
def export_certification_report_excel_route(
    learner_id: str,
    db: Session = Depends(get_db),
):
    try:
        file_path = export_certification_report_excel(
            db,
            learner_id,
        )

        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/{learner_id}/export")
def export_progress_report(
    learner_id: str,
    db: Session = Depends(get_db),
):
    try:
        file_path = export_progress_report_csv(
            db,
            learner_id,
        )

        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="text/csv",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/{learner_id}/export/pdf")
def export_progress_report_pdf_route(
    learner_id: str,
    db: Session = Depends(get_db),
):
    try:
        file_path = export_progress_report_pdf(
            db,
            learner_id,
        )

        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="application/pdf",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/{learner_id}/export/excel")
def export_progress_report_excel_route(
    learner_id: str,
    db: Session = Depends(get_db),
):
    try:
        file_path = export_progress_report_excel(
            db,
            learner_id,
        )

        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/{learner_id}/accuracy")
def get_accuracy_report(
    learner_id: str,
    db: Session = Depends(get_db),
):
    try:
        return generate_accuracy_report(
            db,
            learner_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/{learner_id}/accuracy/export/pdf")
def export_accuracy_report_pdf_route(
    learner_id: str,
    db: Session = Depends(get_db),
):
    try:
        file_path = export_accuracy_report_pdf(
            db,
            learner_id,
        )

        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="application/pdf",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/{learner_id}/accuracy/export/excel")
def export_accuracy_report_excel_route(
    learner_id: str,
    db: Session = Depends(get_db),
):
    try:
        file_path = export_accuracy_report_excel(
            db,
            learner_id,
        )

        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/{learner_id}/learning")
def get_learning_report(
    learner_id: str,
    db: Session = Depends(get_db),
):
    try:
        return generate_learning_report(
            db,
            learner_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/{learner_id}/learning/export/pdf")
def export_learning_report_pdf_route(
    learner_id: str,
    db: Session = Depends(get_db),
):
    try:
        file_path = export_learning_report_pdf(
            db,
            learner_id,
        )

        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="application/pdf",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/{learner_id}/learning/export/excel")
def export_learning_report_excel_route(
    learner_id: str,
    db: Session = Depends(get_db),
):
    try:
        file_path = export_learning_report_excel(
            db,
            learner_id,
        )

        return FileResponse(
            path=file_path,
            filename=os.path.basename(file_path),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.get("/{learner_id}")
def get_progress_report(
    learner_id: str,
    db: Session = Depends(get_db),
):
    try:
        return generate_progress_report(
            db,
            learner_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )