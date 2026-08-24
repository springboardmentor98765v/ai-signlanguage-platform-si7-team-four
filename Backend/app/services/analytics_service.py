from typing import List, Dict, Any


def _get_placeholder_sessions(learner_id: str) -> List[Dict[str, Any]]:
    """
    Placeholder for future database integration.
    Replace with a database query once Day 3 persistence is completed.
    """
    return []


def _calculate_average_accuracy(sessions: List[Dict[str, Any]]) -> float:
    if not sessions:
        return 0.0

    total_accuracy = sum(session.get("accuracy", 0.0) for session in sessions)
    return round(total_accuracy / len(sessions), 4)


def _count_lessons_completed(sessions: List[Dict[str, Any]]) -> int:
    return sum(1 for session in sessions if session.get("completed"))


def _collect_weak_letters(sessions: List[Dict[str, Any]]) -> List[str]:
    weak_letters = set()

    for session in sessions:
        weak_letters.update(session.get("weak_letters", []))

    return sorted(weak_letters)


def _group_sessions_by_week(sessions: list) -> dict:
    """
    Groups placeholder session records by ISO week.
    """
    from collections import defaultdict
    from datetime import datetime

    weekly_groups = defaultdict(list)

    for session in sessions:
        session_date = session.get("date")

        if isinstance(session_date, str):
            session_date = datetime.fromisoformat(session_date)

        year, week_num, _ = session_date.isocalendar()
        week_key = f"{year}-W{week_num:02d}"

        weekly_groups[week_key].append(session)

    return dict(weekly_groups)


def _calculate_weekly_accuracy(weekly_sessions: dict) -> dict:
    """
    Calculates average accuracy for each week.
    """
    return {
        week: _calculate_average_accuracy(sessions)
        for week, sessions in weekly_sessions.items()
    }


def _calculate_improvement_rate(weekly_accuracy: dict) -> dict:
    """
    Computes week-over-week improvement.
    """
    sorted_weeks = sorted(weekly_accuracy.keys())
    improvement_by_week = {}

    previous_accuracy = None

    for week in sorted_weeks:
        current_accuracy = weekly_accuracy[week]

        if previous_accuracy is None:
            improvement_by_week[week] = None
        else:
            improvement_by_week[week] = round(
                current_accuracy - previous_accuracy,
                2
            )

        previous_accuracy = current_accuracy

    return improvement_by_week


def _collect_weekly_weak_letters(weekly_sessions: dict) -> dict:
    """
    Collects weak letters for each week.
    """
    return {
        week: _collect_weak_letters(sessions)
        for week, sessions in weekly_sessions.items()
    }


def get_learner_analytics(learner_id: str) -> Dict[str, Any]:
    """
    Returns analytics summary for a learner.
    """

    sessions = _get_placeholder_sessions(learner_id)

    weekly_sessions = _group_sessions_by_week(sessions)
    weekly_accuracy = _calculate_weekly_accuracy(weekly_sessions)
    weekly_improvement = _calculate_improvement_rate(weekly_accuracy)
    weekly_weak_letters = _collect_weekly_weak_letters(weekly_sessions)

    return {
        "learner_id": learner_id,
        "average_accuracy": _calculate_average_accuracy(sessions),
        "lessons_completed": _count_lessons_completed(sessions),
        "weak_letters": _collect_weak_letters(sessions),
        "weekly_accuracy": weekly_accuracy,
        "weekly_improvement_rate": weekly_improvement,
        "weekly_weak_letters": weekly_weak_letters,
    }

# ---------------------------------------------------------------------------
# DB-backed analytics (used by the /api/analytics and /api/analytics/dashboard
# endpoints). All values are computed live from persisted practice records so
# the learner dashboard reflects real activity per user.
# ---------------------------------------------------------------------------

from sqlalchemy import func as sa_func
from datetime import datetime as _dt, timedelta as _td

from app.models.models import (
    PracticeSession,
    Assessment,
    AnalyticsSummary,
    Streak,
    Recommendation,
    Lesson,
)


def _u(value):
    return str(value)


WEAK_LETTER_THRESHOLD = 70.0


def _latest_letter_scores(assessments) -> dict:
    """Latest overall_accuracy per expected_sign (the newest attempt wins)."""
    latest = {}
    for a in assessments:
        if not a.expected_sign or a.overall_accuracy is None:
            continue
        key = str(a.expected_sign)
        prev = latest.get(key)
        if prev is None or ((prev[1] or _dt.min) < (a.created_at or _dt.min)):
            latest[key] = (float(a.overall_accuracy), a.created_at)
    return {k: v[0] for k, v in latest.items()}


def _humanize_day(ts) -> str:
    if ts is None:
        return ""
    day = ts.date() if isinstance(ts, _dt) else ts
    today = _dt.utcnow().date()
    if day == today:
        return "Today"
    if day == today - _td(days=1):
        return "Yesterday"
    return day.strftime("%b %d")


def get_learner_dashboard(db, user_id: str) -> dict:
    """Returns the exact metric contract the learner Dashboard page renders."""
    user_id_u = _u(user_id)

    all_sessions = (
        db.query(PracticeSession)
        .filter(PracticeSession.user_id == user_id_u)
        .all()
    )
    sessions = [s for s in all_sessions if s.status == "completed"]
    completed_count = len(sessions)

    total_seconds = sum(s.duration_seconds or 0.0 for s in all_sessions)
    for s in all_sessions:
        if s.status != "completed" and s.started_at:
            # Open sessions still count toward time-on-task, capped at 2h so a
            # forgotten browser tab cannot inflate the number indefinitely.
            end = s.ended_at or _dt.utcnow()
            total_seconds += min(max((end - s.started_at).total_seconds(), 0.0), 7200.0)
    practice_hours = round(total_seconds / 3600.0, 2)

    assessments = []
    for s in sessions:
        assessments.extend(s.assessments)

    # Overall accuracy: latest per-letter result, averaged. If the user has no
    # completed assessments yet, fall back to the persisted summary row.
    letter_scores = _latest_letter_scores(assessments)
    summary = db.query(AnalyticsSummary).filter(AnalyticsSummary.user_id == user_id_u).first()
    if letter_scores:
        overall_accuracy = round(sum(letter_scores.values()) / len(letter_scores), 1)
    else:
        overall_accuracy = summary.overall_accuracy_percentage if summary else 0.0

    # Distinct lessons the user has completed.
    distinct_lessons = {s.lesson_id for s in sessions}
    lessons_completed = len(distinct_lessons)

    # Improvement rate: prefer the persisted rate; otherwise compute the
    # second-half vs first-half change from this learner's real score history.
    improvement_rate = 0.0
    persisted_rate = summary.improvement_rate_percentage if summary else None
    if persisted_rate:
        improvement_rate = persisted_rate
    else:
        completed_acc = [a.overall_accuracy for a in assessments if a.overall_accuracy is not None]
        if len(completed_acc) >= 4:
            first_half = completed_acc[: len(completed_acc) // 2]
            second_half = completed_acc[len(completed_acc) // 2 :]
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)
            improvement_rate = round(avg_second - avg_first, 1)

    # Current streak (from the persisted streaks table).
    current_streak = 0
    streak_row = db.query(Streak).filter(Streak.user_id == user_id_u).first()
    if streak_row is not None:
        current_streak = streak_row.current_streak_count or 0
    else:
        dates = {a.created_at.date() for a in assessments if a.created_at}
        current_streak = _consecutive_days(dates)

    # Accuracy over time (chronological, labelled by weekday).
    day_scores = {}
    for a in assessments:
        if a.created_at and a.overall_accuracy is not None:
            day_scores.setdefault(a.created_at.date(), []).append(a.overall_accuracy)
    accuracy_over_time = [
        {"day": day.strftime("%a"), "accuracy": round(sum(v) / len(v), 1)}
        for day, v in sorted(day_scores.items())
    ][-7:]

    # Lessons completed grouped by category, against the real catalog totals.
    all_lessons = db.query(Lesson).all()
    lesson_map = {_u(l.id): l for l in all_lessons}

    category_totals = {}
    for lesson in all_lessons:
        cat = (lesson.category or "general").capitalize()
        category_totals[cat] = category_totals.get(cat, 0) + 1

    completed_ids_by_cat = {}
    for s in sessions:
        lesson = lesson_map.get(_u(s.lesson_id)) if s.lesson_id else None
        if lesson is None:
            continue
        cat = (lesson.category or "general").capitalize()
        completed_ids_by_cat.setdefault(cat, set()).add(_u(s.lesson_id))

    completion_by_category = [
        {
            "category": cat,
            "completed": len(completed_ids_by_cat.get(cat, set())),
            "total": total,
        }
        for cat, total in sorted(category_totals.items())
    ]

    # Live recommendations persisted for this user. Regenerated from the
    # learner's real attempt history so the list is never a stale stub.
    try:
        from app.services.recommendation_service import sync_user_recommendations

        sync_user_recommendations(db, user_id_u)
    except Exception:
        db.rollback()

    rec_rows = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == user_id_u, Recommendation.is_active.is_(True))
        .all()
    )
    recommended_lessons = []
    for rec in rec_rows:
        lesson = lesson_map.get(_u(rec.lesson_id))
        if lesson is None:
            continue
        recommended_lessons.append(
            {
                "lesson_id": _u(lesson.id),
                "title": lesson.title,
                "reason": rec.reason,
                "expected_gesture": lesson.expected_gesture,
            }
        )

    # Next suggested sign: the learner's weakest practiced sign, or the first
    # alphabet lesson they have not touched yet.
    practiced_ids = {_u(s.lesson_id) for s in sessions if s.lesson_id}
    if letter_scores:
        target_sign = min(letter_scores, key=letter_scores.get)
    else:
        target_sign = "A"
        for lesson in all_lessons:
            if (lesson.category or "").lower() != "alphabet":
                continue
            if _u(lesson.id) not in practiced_ids:
                target_sign = (lesson.expected_gesture or "A")[:5]
                break

    recent_rows = sorted(
        (a for a in assessments if a.created_at),
        key=lambda a: a.created_at,
        reverse=True,
    )[:8]
    recent_activities = [
        {
            "id": _u(a.id),
            "sign": str(a.expected_sign)[:5] if a.expected_sign else "?",
            "score": round(float(a.overall_accuracy or 0.0), 1),
            "date": _humanize_day(a.created_at),
        }
        for a in recent_rows
    ]

    return {
        "user_id": user_id_u,
        "overall_accuracy_percentage": overall_accuracy,
        "lessons_completed": lessons_completed,
        "practice_hours": practice_hours,
        "improvement_rate_percentage": improvement_rate,
        "current_streak": current_streak,
        "accuracy_over_time": accuracy_over_time,
        "completion_by_category": completion_by_category,
        "recommended_lessons": recommended_lessons,
        "target_sign": target_sign,
        "recent_activities": recent_activities,
    }


def _consecutive_days(dates) -> int:
    if not dates:
        return 0
    ordered = sorted(dates)
    streak = 1
    best = 1
    for prev, cur in zip(ordered, ordered[1:]):
        if (cur - prev).days == 1:
            streak += 1
            best = max(best, streak)
        else:
            streak = 1
    if ordered[-1] == _dt.utcnow().date():
        return streak
    return 0


def get_learner_analytics_db(db, learner_id: str) -> dict:
    """DB-backed learner analytics: live averages, weak letters, weekly trends."""
    user_id_u = _u(learner_id)
    dash = get_learner_dashboard(db, learner_id)

    rows = (
        db.query(Assessment)
        .join(PracticeSession, Assessment.session_id == PracticeSession.id)
        .filter(
            PracticeSession.user_id == user_id_u,
            Assessment.created_at.isnot(None),
            Assessment.overall_accuracy.isnot(None),
        )
        .order_by(Assessment.created_at.asc())
        .all()
    )

    weekly_scores = {}
    weekly_letter_scores = {}
    for a in rows:
        iso = a.created_at.isocalendar()
        week_key = f"{iso[0]}-W{iso[1]:02d}"
        weekly_scores.setdefault(week_key, []).append(float(a.overall_accuracy))
        letter = str(a.expected_sign or "?")
        weekly_letter_scores.setdefault(week_key, {}).setdefault(letter, []).append(
            float(a.overall_accuracy)
        )

    weekly_accuracy = {
        week: round(sum(values) / len(values), 1)
        for week, values in sorted(weekly_scores.items())
    }

    weekly_improvement_rate = {}
    previous = None
    for week, acc in weekly_accuracy.items():
        weekly_improvement_rate[week] = None if previous is None else round(acc - previous, 1)
        previous = acc

    weekly_weak_letters = {
        week: sorted(
            letter
            for letter, scores in letters.items()
            if sum(scores) / len(scores) < WEAK_LETTER_THRESHOLD
        )
        for week, letters in weekly_letter_scores.items()
    }

    weak_letters = sorted(
        letter
        for letter, score in _latest_letter_scores(rows).items()
        if score < WEAK_LETTER_THRESHOLD
    )

    return {
        "learner_id": learner_id,
        "average_accuracy": dash["overall_accuracy_percentage"],
        "lessons_completed": dash["lessons_completed"],
        "weak_letters": weak_letters,
        "weekly_accuracy": weekly_accuracy,
        "weekly_improvement_rate": weekly_improvement_rate,
        "weekly_weak_letters": weekly_weak_letters,
    }


def get_leaderboard(db, sort: str = "accuracy", user_id: str = None) -> list:
    """Class leaderboard from real persisted metrics (accuracy or streak)."""
    rows = db.query(AnalyticsSummary).all()
    board = []
    from app.models.models import User as _UserModel

    for summary in rows:
        user = db.query(_UserModel).filter(_UserModel.id == summary.user_id).first()
        if user is None:
            continue
        streak = 0
        streak_row = db.query(Streak).filter(Streak.user_id == summary.user_id).first()
        if streak_row is not None:
            streak = streak_row.current_streak_count or 0
        board.append(
            {
                "user_id": _u(summary.user_id),
                "name": user.username,
                "accuracy": round(summary.overall_accuracy_percentage or 0.0, 1),
                "streak": streak,
                "is_user": user_id is not None and _u(summary.user_id) == _u(user_id),
            }
        )

    if sort == "streak":
        board.sort(key=lambda r: r["streak"], reverse=True)
    else:
        board.sort(key=lambda r: r["accuracy"], reverse=True)

    for idx, entry in enumerate(board):
        entry["rank"] = idx + 1
    return board
