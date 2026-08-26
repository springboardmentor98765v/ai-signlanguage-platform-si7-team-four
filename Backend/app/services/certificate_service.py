from typing import NamedTuple
from io import BytesIO
from datetime import datetime

from reportlab.lib.colors import darkblue
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

MINIMUM_AVERAGE_SCORE: float = 80.0


class LearnerProgress(NamedTuple):
    average_score: float
    all_required_letters_practiced: bool


class CertificateNotEligibleError(Exception):
    pass


def check_certificate_eligibility(progress: LearnerProgress) -> dict:
    score_ok = progress.average_score >= MINIMUM_AVERAGE_SCORE
    letters_ok = progress.all_required_letters_practiced

    if score_ok and letters_ok:
        return {
            "eligible": True,
            "message": "Learner meets all requirements for certificate eligibility.",
        }

    reasons = []

    if not score_ok:
        reasons.append(
            f"average score {progress.average_score} is below the required "
            f"{MINIMUM_AVERAGE_SCORE}"
        )

    if not letters_ok:
        reasons.append("not all required letters have been practiced")

    return {
        "eligible": False,
        "message": "Learner is not eligible: " + "; ".join(reasons) + ".",
    }

def generate_certificate_pdf(
    learner_name: str,
    progress: LearnerProgress,
    db=None,
    user_id: str | None = None,
) -> bytes:

    result = check_certificate_eligibility(progress)

    if not result["eligible"]:
        raise CertificateNotEligibleError(result["message"])

    buffer = BytesIO()

    document = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    title_style.alignment = TA_CENTER
    title_style.textColor = darkblue

    normal_style = styles["Normal"]
    normal_style.alignment = TA_CENTER

    story = []

    story.append(Paragraph("Certificate of Achievement", title_style))
    story.append(Spacer(1, 30))

    story.append(
        Paragraph(
            f"This certificate is proudly presented to <b>{learner_name}</b>.",
            normal_style,
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            f"Average Score: <b>{progress.average_score:.2f}%</b>",
            normal_style,
        )
    )

    story.append(Spacer(1, 20))

    story.append(
        Paragraph(
            f"Date: {datetime.now().strftime('%d-%m-%Y')}",
            normal_style,
        )
    )

    document.build(story)

    pdf = buffer.getvalue()
    buffer.close()

    # Milestone 3 - Day 3 hook: certificate generated -> notify the learner.
    if db is not None and user_id:
        from app.services.notification_service import create_notification

        create_notification(
            db,
            user_id=user_id,
            title="Certificate Ready",
            message=(
                f"Congratulations {learner_name}! Your certificate is ready "
                "to download."
            ),
            event_type="certificate_ready",
        )

    return pdf


def generate_certificate_excel(
    learner_name: str,
    progress: LearnerProgress,
    task_label: str | None = None,
) -> bytes:
    """Render the same certificate content as a real .xlsx workbook."""
    result = check_certificate_eligibility(progress)

    if not result["eligible"]:
        raise CertificateNotEligibleError(result["message"])

    try:
        from openpyxl import Workbook
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise RuntimeError("openpyxl is required for Excel certificate export.") from exc

    wb = Workbook()
    ws = wb.active
    ws.title = "Certificate"

    rows = [
        ("Field", "Value"),
        ("Certificate Title", "Certificate of Achievement"),
        ("Platform", "AI Sign Language Platform"),
        ("Presented To", learner_name),
        (
            "Task / Lesson",
            task_label if task_label else "Full Curriculum Completion",
        ),
        ("Average Score", f"{progress.average_score:.2f}%"),
        ("Issue Date", datetime.now().strftime("%d-%m-%Y")),
        ("Verified By", "AI Assessor"),
    ]
    for row in rows:
        ws.append(row)

    ws.column_dimensions["A"].width = 22
    ws.column_dimensions["B"].width = 45
    for cell in ws[1]:
        cell.font = cell.font.copy(bold=True)

    buffer = BytesIO()
    wb.save(buffer)
    return buffer.getvalue()