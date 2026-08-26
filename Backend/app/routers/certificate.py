from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import Certificate, User, Lesson
from app.services.certificate_service import (
    MINIMUM_AVERAGE_SCORE,
    CertificateNotEligibleError,
    LearnerProgress,
    check_certificate_eligibility,
    generate_certificate_pdf,
    generate_certificate_excel,
)
from app.utils.security import verify_token_and_role

router = APIRouter(
    prefix="/api/certificates",
    tags=["Certificate"],
)


class CertificateEligibilityRequest(BaseModel):
    average_score: float = Field(..., ge=0, le=100)
    all_required_letters_practiced: bool = Field(...)


class CertificateEligibilityResponse(BaseModel):
    eligible: bool
    message: str


class IssueCertificateRequest(BaseModel):
    score: float = Field(..., ge=0, le=100, description="Score achieved on the completed task.")
    lesson_id: str | None = Field(None, description="Lesson/task the certificate is earned from.")


def _to_response(cert: Certificate, issued_to: str) -> dict:
    return {
        "certificate_id": str(cert.id),
        "user_id": str(cert.user_id),
        "issued_to": issued_to,
        "issued_date": cert.issued_date.isoformat() if cert.issued_date else None,
        "overall_score": cert.overall_score,
        "lesson_id": str(cert.lesson_id) if cert.lesson_id else None,
    }


@router.post("/check-eligibility", response_model=CertificateEligibilityResponse)
def check_eligibility(
    request: CertificateEligibilityRequest,
    token_payload: dict = Depends(verify_token_and_role(["Learner", "Instructor", "Accessibility Trainer", "Admin"])),
) -> CertificateEligibilityResponse:
    progress = LearnerProgress(
        average_score=request.average_score,
        all_required_letters_practiced=request.all_required_letters_practiced,
    )
    result = check_certificate_eligibility(progress)
    return CertificateEligibilityResponse(**result)


@router.post("/issue", summary="Issue a certificate for a completed task")
def issue_task_certificate(
    request: IssueCertificateRequest,
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token_and_role(["Learner", "Instructor", "Accessibility Trainer", "Admin"])),
):
    """
    Issues (or returns the already-issued) certificate for a completed task.

    Called by the Practice page right after a learner completes a task with a
    passing score, so the learner can immediately download the certificate as
    PDF or Excel. Idempotent per (user, lesson) pair.
    """
    user_id = token_payload.get("user_id")
    username = token_payload.get("username") or "Learner"
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload.")

    progress = LearnerProgress(
        average_score=request.score,
        all_required_letters_practiced=True,
    )
    result = check_certificate_eligibility(progress)
    if not result["eligible"]:
        raise HTTPException(status_code=400, detail=result["message"])

    lesson_id = None
    if request.lesson_id:
        lesson = db.query(Lesson).filter(Lesson.id == request.lesson_id).first()
        if lesson is not None:
            lesson_id = str(lesson.id)

    query = db.query(Certificate).filter(Certificate.user_id == str(user_id))
    if lesson_id:
        query = query.filter(Certificate.lesson_id == lesson_id)
    else:
        query = query.filter(Certificate.lesson_id.is_(None))

    cert = query.order_by(Certificate.issued_date.desc()).first()
    if cert is None:
        cert = Certificate(
            user_id=str(user_id),
            overall_score=request.score,
            lesson_id=lesson_id,
        )
        db.add(cert)

        from app.services.notification_service import create_notification

        task_label = f" for completing '{lesson.title}'" if lesson_id else ""
        create_notification(
            db,
            user_id=str(user_id),
            title="Certificate Earned",
            message=f"Congratulations {username}! You earned a certificate{task_label}.",
            event_type="certificate_ready",
        )
        db.commit()
        db.refresh(cert)
        issued = True
    else:
        # Keep the stored score at its best recorded value.
        if request.score > (cert.overall_score or 0.0):
            cert.overall_score = request.score
            db.commit()
            db.refresh(cert)
        issued = False

    return {
        "issued": issued,
        **_to_response(cert, username),
    }


@router.get("/my-certificates")
def list_my_certificates(
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token_and_role(["Learner", "Instructor", "Accessibility Trainer", "Admin"])),
):
    user_id = token_payload.get("user_id")
    username = token_payload.get("username") or "Learner"
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload.")

    certs = (
        db.query(Certificate)
        .filter(Certificate.user_id == str(user_id))
        .order_by(Certificate.issued_date.desc())
        .all()
    )
    return {
        "certificates": [_to_response(c, username) for c in certs],
    }


@router.get(
    "/{certificate_id}/download",
    summary="Download a certificate as PDF or Excel",
)
def download_certificate_file(
    certificate_id: str,
    format: str = Query("pdf", pattern="^(pdf|excel|xlsx)$"),
    db: Session = Depends(get_db),
    token_payload: dict = Depends(verify_token_and_role(["Learner", "Instructor", "Accessibility Trainer", "Admin"])),
):
    user_id = token_payload.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload.")

    cert = db.query(Certificate).filter(Certificate.id == certificate_id).first()
    if cert is None:
        raise HTTPException(status_code=404, detail="Certificate not found.")
    if str(cert.user_id) != str(user_id):
        raise HTTPException(status_code=403, detail="Certificate does not belong to this account.")

    learner = db.query(User).filter(User.id == cert.user_id).first()
    learner_name = learner.username if learner else "Learner"
    task_label = None
    if cert.lesson_id:
        task = db.query(Lesson).filter(Lesson.id == cert.lesson_id).first()
        task_label = task.title if task else "Completed Task"
    progress = LearnerProgress(
        average_score=cert.overall_score,
        all_required_letters_practiced=True,
    )
    try:
        if format in ("excel", "xlsx"):
            file_bytes = generate_certificate_excel(learner_name, progress, task_label)
            media_type = (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            extension = "xlsx"
        else:
            file_bytes = generate_certificate_pdf(learner_name, progress)
            media_type = "application/pdf"
            extension = "pdf"
    except CertificateNotEligibleError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    filename = f"{learner_name.replace(' ', '_')}_certificate.{extension}"
    return Response(
        content=file_bytes,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )