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
from app.models.models import AccessibilityTrainerLearner, User
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
    "/analytics",
    status_code=status.HTTP_200_OK,
    summary="Get Trainer Dashboard Analytics",
    description=(
        "Accessibility Trainer only. Aggregate dashboard metrics computed live "
        "from the trainer's assigned learners: counts, average accuracy, "
        "certifications issued, per-learner rows and per-skill breakdown."
    ),
)
def get_trainer_analytics(
    token_data: dict = Depends(verify_token_and_role([TRAINER_ROLE])),
    db: Session = Depends(get_db),
):
    from datetime import timedelta as _td
    from app.models.models import Assessment, Certificate, PracticeSession as _PS, User as _U
    from sqlalchemy import func as _f

    trainer_id = str(token_data["user_id"])
    links = trainer_service.assigned_learners(db, trainer_id)
    learner_ids = [str(row["learner_id"]) for row in links]

    assigned_count = len(learner_ids)
    active_this_week = 0
    all_accuracies: list[float] = []
    by_letter: dict[str, list[float]] = {}
    learners_rows = []
    certifications_issued = 0

    week_ago = datetime.utcnow() - _td(days=7)

    cert_count_by_user = {}
    if learner_ids:
        cert_query = (
            db.query(Certificate.user_id, _f.count(Certificate.id))
            .filter(Certificate.user_id.in_(learner_ids))
            .group_by(Certificate.user_id)
            .all()
        )
        cert_count_by_user = dict(cert_query)
        certifications_issued = sum(cert_count_by_user.values())

    for row in links:
        learner_id = str(row["learner_id"])
        sessions = (
            db.query(_PS)
            .filter(_PS.user_id == learner_id)
            .all()
        )
        completed = [s for s in sessions if s.status == "completed"]

        latest = None
        if sessions:
            latest = max((s.started_at for s in sessions if s.started_at), default=None)
        if latest is not None and latest >= week_ago:
            active_this_week += 1

        assessments = (
            db.query(Assessment)
            .join(_PS, _PS.id == Assessment.session_id)
            .filter(_PS.user_id == learner_id)
            .all()
        )

        accuracies = [a.overall_accuracy for a in assessments if a.overall_accuracy is not None]
        avg = round(sum(accuracies) / len(accuracies), 1) if accuracies else 0.0
        all_accuracies.extend(accuracies)

        for a in assessments:
            sign = (a.expected_sign or "").strip().upper()
            if sign and a.overall_accuracy is not None:
                by_letter.setdefault(sign, []).append(a.overall_accuracy)

        done_lessons = {s.lesson_id for s in completed}
        has_cert = cert_count_by_user.get(learner_id, 0) > 0

        learners_rows.append({
            "id": learner_id,
            "name": row["username"],
            "email": row["email"],
            "level": "Beginner" if avg < 80 else "Intermediate" if avg < 90 else "Advanced",
            "progress": len(done_lessons),
            "accuracy": avg,
            "status": "Certified" if has_cert else
                      ("In Assessment" if sessions else "Needs Support"),
        })

    overall_avg = round(sum(all_accuracies) / len(all_accuracies), 1) if all_accuracies else 0.0
    skill_breakdown = [
        {"skill": key, "score": round(sum(v) / len(v), 1)}
        for key, v in sorted(by_letter.items())
    ]

    return {
        "assigned_learners": assigned_count,
        "active_this_week": active_this_week,
        "avg_accuracy": overall_avg,
        "certifications_issued": certifications_issued,
        "learners": learners_rows,
        "skill_breakdown": skill_breakdown,
    }


@router.get(
    "/learners",
    response_model=list[TrainerLearnerSummary],
    status_code=status.HTTP_200_OK,
    summary="Get My Assigned Learners",
    description=(
        "Accessibility Trainer only. Returns every learner assigned to the "
        "logged-in trainer via the accessibility_trainer_learner table."
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
        db.query(AccessibilityTrainerLearner)
        .filter(
            AccessibilityTrainerLearner.trainer_id == token_data["user_id"],
            AccessibilityTrainerLearner.learner_id == learner.id,
        )
        .first()
    )
    if existing is None:
        db.add(AccessibilityTrainerLearner(trainer_id=token_data["user_id"], learner_id=learner.id))
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