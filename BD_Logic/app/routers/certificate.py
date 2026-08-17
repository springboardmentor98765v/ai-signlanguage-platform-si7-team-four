from fastapi import APIRouter, HTTPException, Query, Response
from pydantic import BaseModel, Field

from app.services.certificate_service import (
    CertificateNotEligibleError,
    LearnerProgress,
    check_certificate_eligibility,
    generate_certificate_pdf,
)

router = APIRouter(prefix="/certificate", tags=["Certificate"])


class CertificateEligibilityRequest(BaseModel):
    average_score: float = Field(..., ge=0, le=100)
    all_required_letters_practiced: bool = Field(...)


class CertificateEligibilityResponse(BaseModel):
    eligible: bool
    message: str


@router.post("/check-eligibility", response_model=CertificateEligibilityResponse)
def check_eligibility(
    request: CertificateEligibilityRequest,
) -> CertificateEligibilityResponse:
    progress = LearnerProgress(
        average_score=request.average_score,
        all_required_letters_practiced=request.all_required_letters_practiced,
    )
    result = check_certificate_eligibility(progress)
    return CertificateEligibilityResponse(**result)

@router.get("/generate-pdf")
def generate_pdf(
    learner_name: str = Query(...),
    average_score: float = Query(..., ge=0, le=100),
    all_required_letters_practiced: bool = Query(...),
):
    progress = LearnerProgress(
        average_score=average_score,
        all_required_letters_practiced=all_required_letters_practiced,
    )

    try:
        pdf_buffer = generate_certificate_pdf(learner_name, progress)
    except CertificateNotEligibleError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    filename = f"{learner_name.replace(' ', '_')}_certificate.pdf"

    return Response(
        content=pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )