from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import Response
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import Certificate, User
from app.services.certificate_service import (
    CertificateNotEligibleError,
    LearnerProgress,
    check_certificate_eligibility,
    generate_certificate_pdf,
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


def _to_response(cert: Certificate, issued_to: str) -> dict:
    return {
        "certificate_id": str(cert.id),
        "user_id": str(cert.user_id),
        "issued_to": issued_to,
        "issued_date": cert.issued_date.isoformat() if cert.issued_date else None,
        "overall_score": cert.overall_score,
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


@router.get("/{certificate_id}/download", summary="Download a certificate PDF")
def download_certificate_pdf(
    certificate_id: str,
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
    progress = LearnerProgress(
        average_score=cert.overall_score,
        all_required_letters_practiced=True,
    )
    try:
        pdf_buffer = generate_certificate_pdf(learner_name, progress)
    except CertificateNotEligibleError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    filename = f"{learner_name.replace(' ', '_')}_certificate.pdf"
    return Response(
        content=pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )