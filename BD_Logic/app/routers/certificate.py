"""
certificate.py

Router for certificate-related endpoints (Milestone 2, Day 6).

Scope (per SRS Milestone 2 / FR-4 / Cross-Domain Dependency Matrix):
- Exposes a single eligibility-check endpoint.
- Contains NO business logic (delegates to certificate_service.py).
- Does NOT generate PDFs (later milestone).
- Does NOT connect to the database (Intern 5 scope) — request data is
  supplied directly by the caller for now.
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.certificate_service import (
    LearnerProgress,
    check_certificate_eligibility,
)

router = APIRouter(prefix="/certificate", tags=["Certificate"])


class CertificateEligibilityRequest(BaseModel):
    average_score: float = Field(
        ..., ge=0, le=100, description="Learner's average assessment score (0-100)."
    )
    all_required_letters_practiced: bool = Field(
        ..., description="Whether the learner has practiced all required letters."
    )


class CertificateEligibilityResponse(BaseModel):
    eligible: bool
    message: str


@router.post("/check-eligibility", response_model=CertificateEligibilityResponse)
def check_eligibility(
    request: CertificateEligibilityRequest,
) -> CertificateEligibilityResponse:
    """
    Check whether a learner is eligible for a certificate based on
    their average score and letter-practice completion.
    """
    progress = LearnerProgress(
        average_score=request.average_score,
        all_required_letters_practiced=request.all_required_letters_practiced,
    )
    result = check_certificate_eligibility(progress)
    return CertificateEligibilityResponse(**result)