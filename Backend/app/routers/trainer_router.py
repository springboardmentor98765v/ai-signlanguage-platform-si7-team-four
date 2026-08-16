"""
Milestone 4 - Day 2: Accessibility Trainer router.

Every endpoint is restricted to the "Accessibility Trainer" role using the same
`verify_token_and_role([...])` dependency pattern as the existing learner /
instructor dashboards (`app/routers/auth.py`). A trainer can only view THEIR
assigned learners.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.models import TrainerLearnerLink, User
from app.services import trainer_service
from app.schemas.trainer import (
    TrainerLearnerSummary,
    EngagementMetric,
    SkillDevelopmentMetric,
    AssessmentAnalyticsMetric,
    CertificationStatusMetric,
)
from app.utils.security import verify_token_and_role
from app.utils.validation import reject_malicious

router = APIRouter(prefix="/api/trainer", tags=["Accessibility Trainer"])

TRAINER_ROLE = "Accessibility Trainer"


class AssignLearnerRequest(BaseModel):
    learner_id: str | None = Field(default=None, min_length=1, max_length=80)
    learner_email: str | None = Field(default=None, max_length=180)

    @field_validator("learner_id", "learner_email")
    @classmethod
    def _reject_malicious_identifiers(cls, value):
        if value is None:
            return value
        return reject_malicious(value)


def _get_assigned_learner(db: Session, trainer_id: str, learner_id: str) -> User:
    """404 if the learner doesn't exist, 403 if not assigned to this trainer."""
    learner = db.query(User).filter(User.id == learner_id, User.role == "Learner").first()
    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found.")
    if not trainer_service.is_assigned(db, trainer_id, learner_id):
        raise HTTPException(
            status_code=403,
            detail="This learner is not assigned to you.",
        )
    return learner


@router.get(
    "/learners",
    response_model=list[TrainerLearnerSummary],
    status_code=status.HTTP_200_OK,
    summary="Get My Assigned Learners",
    description=(
        "Accessibility Trainer only. Returns every learner assigned to the "
        "logged-in trainer via the trainer_learner_links table."
    ),
)
def get_my_learners(
    token_data: dict = Depends(verify_token_and_role([TRAINER_ROLE])),
    db: Session = Depends(get_db),
):
    """Checkpoint: 'Get my assigned learners' API working for the Trainer role."""
    return trainer_service.assigned_learners(db, token_data["user_id"])


@router.post(
    "/assign-learner",
    status_code=status.HTTP_200_OK,
    summary="Assign a Learner to the Trainer",
    description=(
        "Accessibility Trainer only. Links a Learner account (by id or email) "
        "to the logged-in trainer. Idempotent: re-assigning is a no-op."
    ),
)
def assign_learner(
    payload: AssignLearnerRequest,
    token_data: dict = Depends(verify_token_and_role([TRAINER_ROLE])),
    db: Session = Depends(get_db),
):
    if not payload.learner_id and not payload.learner_email:
        raise HTTPException(
            status_code=400,
            detail="Provide learner_id or learner_email.",
        )

    learner = None
    if payload.learner_id:
        learner = db.query(User).filter(User.id == payload.learner_id).first()
    else:
        learner = db.query(User).filter(User.email == payload.learner_email).first()

    if not learner:
        raise HTTPException(status_code=404, detail="Learner not found.")
    if learner.role != "Learner":
        raise HTTPException(status_code=400, detail="Target user is not a Learner.")
    if learner.id == token_data["user_id"]:
        raise HTTPException(status_code=400, detail="A trainer cannot assign themself.")

    existing = (
        db.query(TrainerLearnerLink)
        .filter(
            TrainerLearnerLink.trainer_id == token_data["user_id"],
            TrainerLearnerLink.learner_id == learner.id,
        )
        .first()
    )
    if existing is None:
        db.add(TrainerLearnerLink(trainer_id=token_data["user_id"], learner_id=learner.id))
        db.commit()

    return {
        "message": "Learner successfully assigned to trainer.",
        "trainer_id": token_data["user_id"],
        "learner_id": learner.id,
    }


@router.get(
    "/learners/{learner_id}/engagement",
    response_model=EngagementMetric,
    status_code=status.HTTP_200_OK,
    summary="Learner Engagement",
    description=(
        "Accessibility Trainer only, assigned learner only. How often the learner "
        "practices, derived from practice_session records. Score is a placeholder "
        "formula - final weighting owned by Intern 4."
    ),
)
def get_learner_engagement(
    learner_id: str,
    token_data: dict = Depends(verify_token_and_role([TRAINER_ROLE])),
    db: Session = Depends(get_db),
):
    _get_assigned_learner(db, token_data["user_id"], learner_id)
    return trainer_service.engagement(db, learner_id)


@router.get(
    "/learners/{learner_id}/skill-development",
    response_model=SkillDevelopmentMetric,
    status_code=status.HTTP_200_OK,
    summary="Learner Skill Development",
    description=(
        "Accessibility Trainer only, assigned learner only. Improvement over time "
        "derived from historical assessment scores and weekly weak-letter summaries. "
        "Trend computation is a placeholder (Intern 4 owns the final formula)."
    ),
)
def get_learner_skill_development(
    learner_id: str,
    token_data: dict = Depends(verify_token_and_role([TRAINER_ROLE])),
    db: Session = Depends(get_db),
):
    _get_assigned_learner(db, token_data["user_id"], learner_id)
    return trainer_service.skill_development(db, learner_id)


@router.get(
    "/learners/{learner_id}/assessment-analytics",
    response_model=AssessmentAnalyticsMetric,
    status_code=status.HTTP_200_OK,
    summary="Learner Assessment Analytics",
    description=(
        "Accessibility Trainer only, assigned learner only. Average scores / accuracy "
        "aggregated from assessment records, with a per-letter breakdown."
    ),
)
def get_learner_assessment_analytics(
    learner_id: str,
    token_data: dict = Depends(verify_token_and_role([TRAINER_ROLE])),
    db: Session = Depends(get_db),
):
    _get_assigned_learner(db, token_data["user_id"], learner_id)
    return trainer_service.assessment_analytics(db, learner_id)


@router.get(
    "/learners/{learner_id}/certification-status",
    response_model=CertificationStatusMetric,
    status_code=status.HTTP_200_OK,
    summary="Learner Certification Status",
    description=(
        "Accessibility Trainer only, assigned learner only. Pass/fail and level from "
        "the learner's latest certificate (or 'not_attempted' if none exists). "
        "Pass thresholds are placeholders - Intern 4 owns the final policy."
    ),
)
def get_learner_certification_status(
    learner_id: str,
    token_data: dict = Depends(verify_token_and_role([TRAINER_ROLE])),
    db: Session = Depends(get_db),
):
    _get_assigned_learner(db, token_data["user_id"], learner_id)
    return trainer_service.certification_status(db, learner_id)