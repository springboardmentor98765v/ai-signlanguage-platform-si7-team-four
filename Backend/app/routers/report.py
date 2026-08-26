from io import BytesIO
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.report_service import generate_progress_report
from app.utils.security import verify_token_and_role

router = APIRouter(
    prefix="/api/reports",
    tags=["Report"],
)

SUPPORTED_FORMATS = {"csv", "pdf", "excel", "xlsx"}


def _report_file_bytes(report: dict, report_type: str, fmt: str):
    """Render a progress report as CSV, PDF or XLSX bytes."""
    if fmt == "csv":
        lines = ["Field,Value"]
        lines.append(f"Learner ID,{report.get('learner_id', '')}")
        lines.append(f"Lessons Completed,{report.get('lessons_completed', 0)}")
        lines.append(f"Average Score,{report.get('average_score', 0)}%")
        for letter in report.get("weak_letters", []) or []:
            lines.append(f"Weak Letter,{letter}")
        for cert in report.get("certificates_earned", []) or []:
            lines.append(f"Certificate Earned,{cert}")
        return "\n".join(lines), "text/csv", "csv"

    if fmt in ("excel", "xlsx"):
        try:
            from openpyxl import Workbook
        except ImportError as exc:  # pragma: no cover - dependency guard
            raise RuntimeError("openpyxl is required for Excel export.") from exc

        wb = Workbook()
        ws = wb.active
        ws.title = f"{report_type} report"
        ws.append(["Field", "Value"])
        ws.append(["Learner ID", report.get("learner_id", "")])
        ws.append(["Lessons Completed", report.get("lessons_completed", 0)])
        ws.append(["Average Score", f"{report.get('average_score', 0)}%"])
        for letter in report.get("weak_letters", []) or []:
            ws.append(["Weak Letter", letter])
        for cert in report.get("certificates_earned", []) or []:
            ws.append(["Certificate Earned", str(cert)])
        for col, width in (("A", 24), ("B", 42)):
            ws.column_dimensions[col].width = width
        buffer = BytesIO()
        wb.save(buffer)
        return buffer.getvalue(), (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ), "xlsx"

    # PDF via ReportLab (already a project dependency).
    from reportlab.lib.colors import darkblue
    from reportlab.lib.enums import TA_CENTER
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    title_style.alignment = TA_CENTER
    title_style.textColor = darkblue

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    story = [
        Paragraph(f"{report_type.capitalize()} Report", title_style),
        Spacer(1, 18),
        Paragraph(f"Learner ID: {report.get('learner_id', '')}", styles["Normal"]),
        Paragraph(f"Lessons Completed: {report.get('lessons_completed', 0)}", styles["Normal"]),
        Paragraph(f"Average Score: {report.get('average_score', 0)}%", styles["Normal"]),
        Spacer(1, 12),
        Paragraph(
            "Weak letters: "
            + (", ".join(str(w) for w in (report.get("weak_letters") or [])) or "None"),
            styles["Normal"],
        ),
        Spacer(1, 12),
        Paragraph(
            f"Generated {datetime.now().strftime('%d-%m-%Y %H:%M UTC')}",
            styles["Normal"],
        ),
    ]
    doc.build(story)
    return buffer.getvalue(), "application/pdf", "pdf"


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


@router.get("/{report_type}/export", summary="Export a progress report as CSV, PDF or Excel")
def export_progress_report(
    report_type: str,
    format: str = Query("csv", pattern="^(csv|pdf|excel|xlsx)$"),
    learner_id: str = Query(..., description="Learner whose report should be exported."),
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token_and_role(["Learner", "Instructor", "Accessibility Trainer", "Admin"])),
):
    if report_type not in {"progress", "translation"}:
        raise HTTPException(status_code=404, detail="Unsupported report type.")

    if report_type == "translation":
        raise HTTPException(status_code=404, detail="Translation reports are not yet available.")

    try:
        report = generate_progress_report(learner_id, db=db)
        content, media_type, extension = _report_file_bytes(report, report_type, format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    filename = f"{report_type}_report_{str(learner_id)[:8]}.{extension}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
