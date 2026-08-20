"""
Milestone 4 - Day 2: Accessibility Trainer data queries (Intern 2).

Every metric is derived directly from existing tables so the endpoints return
REAL numbers (never hardcoded/fake). The formulas used here are reasonable
placeholders and are marked `# PENDING Intern 4 final formula` - Intern 4
(Business Logic) owns the final weighting/thresholds.
"""
import json
from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.models import (
    Assessment,
    Certificate,
    PracticeSession,
    AccessibilityTrainerLearner,
    User,
    WeeklyAnalytics,
)


def assigned_learners(db: Session, trainer_id: str) -> list[dict]:
    """Learners linked to this trainer, with assignment timestamp."""
    rows = (
        db.query(AccessibilityTrainerLearner, User)
        .join(User, User.id == AccessibilityTrainerLearner.learner_id)
        .filter(AccessibilityTrainerLearner.trainer_id == trainer_id)
        .order_by(AccessibilityTrainerLearner.assigned_at.desc())
        .all()
    )
    return [
        {
            "learner_id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "assigned_at": link.assigned_at,
        }
        for link, user in rows
    ]


def is_assigned(db: Session, trainer_id: str, learner_id: str) -> bool:
    return (
        db.query(AccessibilityTrainerLearner)
        .filter(
            AccessibilityTrainerLearner.trainer_id == trainer_id,
            AccessibilityTrainerLearner.learner_id == learner_id,
        )
        .first()
        is not None
    )


def _sessions_for(db: Session, learner_id: str):
    return (
        db.query(PracticeSession)
        .filter(PracticeSession.user_id == learner_id)
        .all()
    )


def _assessments_for(db: Session, learner_id: str):
    return (
        db.query(Assessment)
        .join(PracticeSession, PracticeSession.id == Assessment.session_id)
        .filter(PracticeSession.user_id == learner_id)
        .order_by(Assessment.created_at.asc())
        .all()
    )


def engagement(db: Session, learner_id: str) -> dict:
    sessions = _sessions_for(db, learner_id)
    total_attempts = sum(s.attempt_count or 0 for s in sessions)
    duration_seconds = sum((s.duration_seconds or 0) for s in sessions)
    completed = [s for s in sessions if s.status == "completed"]
    last = max((s.started_at for s in sessions if s.started_at), default=None)

    # PENDING Intern 4 final formula: simple composite, capped at 100.
    engagement_score = min(
        100.0,
        len(sessions) * 6.0 + len(completed) * 3.0 + min(total_attempts, 40) * 0.5,
    )

    return {
        "learner_id": learner_id,
        "engagement_score": round(engagement_score, 2),
        "sessions_total": len(sessions),
        "sessions_completed": len(completed),
        "total_attempts": total_attempts,
        "total_practice_minutes": round(duration_seconds / 60.0, 2),
        "last_practiced_at": last,
    }


def skill_development(db: Session, learner_id: str) -> dict:
    assessments = _assessments_for(db, learner_id)

    # PENDING Intern 4 final formula: simple per-week average-accuracy trend.
    weekly: dict[str, list[float]] = {}
    for a in assessments:
        if a.created_at is None or a.overall_accuracy is None:
            continue
        week = a.created_at.isocalendar()[:2]  # (year, week)
        weekly.setdefault(f"{week[0]}-W{week[1]}", []).append(a.overall_accuracy)

    trend = [
        {
            "week_start": week,
            "average_accuracy": round(sum(v) / len(v), 2),
        }
        for week, v in sorted(weekly.items())
    ]

    improvement_rate = 0.0
    if len(trend) >= 2:
        improvement_rate = round(trend[-1]["average_accuracy"] - trend[0]["average_accuracy"], 2)
    elif trend:
        improvement_rate = round(trend[0]["average_accuracy"], 2)

    # Favour explicit weekly summaries if the analytics pipeline wrote any.
    weak_letters: list[str] = []
    weekly_rows = (
        db.query(WeeklyAnalytics.weak_letters)
        .filter(WeeklyAnalytics.user_id == learner_id, WeeklyAnalytics.weak_letters.isnot(None))
        .all()
    )
    for (raw,) in weekly_rows:
        for parsed in _parse_weak_letters(raw):
            if parsed not in weak_letters:
                weak_letters.append(parsed)

    return {
        "learner_id": learner_id,
        "improvement_rate": improvement_rate,
        "trend": trend,
        "weak_letters": weak_letters,
    }


def assessment_analytics(db: Session, learner_id: str) -> dict:
    assessments = _assessments_for(db, learner_id)

    accuracies = [a.overall_accuracy for a in assessments if a.overall_accuracy is not None]
    confidences = [a.confidence for a in assessments if a.confidence is not None]
    correct = [a for a in assessments if a.is_correct]

    # Per-letter breakdown (PENDING Intern 4 final formula).
    per_letter: dict[str, dict] = {}
    for a in assessments:
        letter = (a.expected_sign or "?").upper()
        bucket = per_letter.setdefault(letter, {"attempts": 0, "correct": 0})
        bucket["attempts"] += 1
        if a.is_correct:
            bucket["correct"] += 1

    letter_list = [
        {
            "letter": letter,
            "attempts": b["attempts"],
            "correct": b["correct"],
            "accuracy": round(100.0 * b["correct"] / b["attempts"], 2) if b["attempts"] else 0.0,
        }
        for letter, b in sorted(per_letter.items())
    ]

    total = len(assessments)
    return {
        "learner_id": learner_id,
        "total_assessments": total,
        "average_accuracy": round(sum(accuracies) / len(accuracies), 2) if accuracies else 0.0,
        "average_confidence": round(sum(confidences) / len(confidences), 2) if confidences else 0.0,
        "correct_count": len(correct),
        "correct_percentage": round(100.0 * len(correct) / total, 2) if total else 0.0,
        "per_letter": letter_list,
    }


def certification_status(db: Session, learner_id: str) -> dict:
    cert = (
        db.query(Certificate)
        .filter(Certificate.user_id == learner_id)
        .order_by(Certificate.issued_date.desc())
        .first()
    )

    if cert is None:
        return {
            "learner_id": learner_id,
            "status": "not_attempted",
            "level": None,
            "overall_score": None,
            "certificate_issued_date": None,
        }

    score = cert.overall_score
    # PENDING Intern 4 final formula: placeholder thresholds.
    if score >= 80:
        status = "passed"
        level = "advanced" if score >= 90 else "intermediate"
    elif score >= 60:
        status = "in_progress"
        level = "intermediate"
    else:
        status = "not_passed"
        level = "beginner"

    return {
        "learner_id": learner_id,
        "status": status,
        "level": level,
        "overall_score": score,
        "certificate_issued_date": cert.issued_date,
    }


def _parse_weak_letters(raw: str) -> list[str]:
    """weekly_analytics.weak_letters is free Text - try JSON, then simple splitting."""
    if not raw:
        return []
    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [str(x) for x in parsed]
    except (ValueError, TypeError):
        pass
    return [item.strip() for item in raw.replace("[", "").replace("]", "").split(",") if item.strip()]