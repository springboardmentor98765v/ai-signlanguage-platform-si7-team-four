from typing import Dict, List

SCORE_THRESHOLD: float = 70.0
ATTEMPT_WINDOW: int = 3


def group_scores_by_sign(attempts: List[dict]) -> Dict[str, List[float]]:
    grouped: Dict[str, List[float]] = {}
    for attempt in attempts:
        sign = attempt["sign"]
        score = attempt["score"]
        grouped.setdefault(sign, []).append(score)
    return grouped


def get_last_n_scores(scores: List[float], n: int = ATTEMPT_WINDOW) -> List[float]:
    return scores[-n:]


def needs_extra_practice(scores: List[float]) -> bool:
    last_scores = get_last_n_scores(scores)
    if len(last_scores) < ATTEMPT_WINDOW:
        return False
    average_score = sum(last_scores) / len(last_scores)
    return average_score < SCORE_THRESHOLD


def generate_recommendations(attempts: List[dict], db=None, user_id: str | None = None) -> List[dict]:
    grouped_scores = group_scores_by_sign(attempts)
    recommendations: List[dict] = []

    for sign, scores in grouped_scores.items():
        if needs_extra_practice(scores):
            recommendations.append({
                "sign": sign,
                "message": f"Extra practice recommended for '{sign}'."
            })

    # Milestone 3 - Day 3 hook: new recommendations available -> notify the learner.
    if recommendations and db is not None and user_id:
        from app.services.notification_service import create_notification

        signs = ", ".join(r["sign"] for r in recommendations)
        create_notification(
            db,
            user_id=user_id,
            title="New Recommendations",
            message=f"Extra practice recommended for: {signs}.",
            event_type="new_recommendation",
        )

    return recommendations


def sync_user_recommendations(db, user_id) -> int:
    """
    Regenerate a learner's persisted Recommendation rows from their real
    attempt history (last-3-scores rule per sign, threshold 70).

    Idempotent: performs no writes when the desired set already matches the
    active rows. Returns the number of active recommendations afterwards.
    """
    from sqlalchemy import func as sa_func

    from app.models.models import (
        Assessment,
        Lesson,
        PracticeSession,
        Recommendation as RecModel,
    )

    user_id = str(user_id)
    rows = (
        db.query(Assessment)
        .join(PracticeSession, Assessment.session_id == PracticeSession.id)
        .filter(
            PracticeSession.user_id == user_id,
            Assessment.expected_sign.isnot(None),
        )
        .order_by(Assessment.created_at.asc())
        .all()
    )
    attempts = [
        {"sign": str(a.expected_sign), "score": float(a.overall_accuracy or 0.0)}
        for a in rows
    ]
    recs = generate_recommendations(attempts)

    desired = {}
    for rec in recs:
        lesson = (
            db.query(Lesson)
            .filter(sa_func.lower(Lesson.expected_gesture) == rec["sign"].lower())
            .first()
        )
        if lesson is None:
            continue
        desired[str(lesson.id)] = rec["message"]

    active = (
        db.query(RecModel)
        .filter(RecModel.user_id == user_id, RecModel.is_active.is_(True))
        .all()
    )
    current = {str(r.lesson_id): r.reason for r in active}
    if current == desired:
        return len(desired)

    for row in active:
        row.is_active = False
    for lesson_id, reason in desired.items():
        db.add(RecModel(user_id=user_id, lesson_id=lesson_id, reason=reason))
    db.commit()
    return len(desired)