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

    return pdf