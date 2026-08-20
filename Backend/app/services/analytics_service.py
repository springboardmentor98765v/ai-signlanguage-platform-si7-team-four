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


def get_learner_dashboard(db, user_id: str) -> dict:
    """Returns the exact metric contract the learner Dashboard page renders."""
    user_id_u = _u(user_id)

    sessions = (
        db.query(PracticeSession)
        .filter(PracticeSession.user_id == user_id_u, PracticeSession.status == "completed")
        .all()
    )
    completed_count = len(sessions)
    practice_hours = round(
        sum(s.duration_seconds or 0.0 for s in sessions) / 3600.0, 2
    )

    assessments = []
    for s in sessions:
        assessments.extend(s.assessments)

    # Overall accuracy: latest per-letter result, averaged. If the user has no
    # completed assessments yet, fall back to the persisted summary row.
    overall_accuracy = 0.0
    by_letter = {}
    for a in assessments:
        if a.expected_sign and a.overall_accuracy is not None:
            key = a.expected_sign
            if key not in by_letter or (by_letter[key][1] or _dt.min) < (a.created_at or _dt.min):
                by_letter[key] = (a.overall_accuracy, a.created_at)
    if by_letter:
        overall_accuracy = round(sum(v[0] for v in by_letter.values()) / len(by_letter), 1)
    else:
        summary = db.query(AnalyticsSummary).filter(AnalyticsSummary.user_id == user_id_u).first()
        overall_accuracy = summary.overall_accuracy_percentage if summary else 0.0

    # Distinct lessons the user has completed.
    distinct_lessons = {s.lesson_id for s in sessions}
    lessons_completed = len(distinct_lessons)

    # Improvement rate: week-over-week change in average assessment accuracy.
    improvement_rate = 0.0
    summary = db.query(AnalyticsSummary).filter(AnalyticsSummary.user_id == user_id_u).first()
    if summary is not None and summary.improvement_rate_percentage:
        improvement_rate = summary.improvement_rate_percentage
    else:
        completed_acc = [a.overall_accuracy for a in assessments if a.overall_accuracy is not None]
        if completed_acc:
            cutoff = _dt.utcnow() - _td(days=7)
            recent = [x for x in completed_acc]
            if len(recent) >= 4:
                second_half = recent[len(recent) // 2:]
                first_half = recent[: len(recent) // 2]
                avg1 = sum(first_half) / len(first_half)
                avg2 = sum(second_half) / len(second_half)
                improvement_rate = round(avg2 - avg1, 1)

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

    # Lessons completed grouped by category.
    category_totals = {}
    category_done = {}
    for s in sessions:
        lesson = db.query(Lesson).filter(Lesson.id == s.lesson_id).first()
        if lesson is None:
            continue
        cat = (lesson.category or "general").capitalize()
        category_totals[cat] = category_totals.get(cat, 0) + 1
        category_done[cat] = category_done.get(cat, 0) + 1
    completion_by_category = [
        {"category": c, "completed": done, "total": done} for c, done in sorted(category_done.items())
    ]

    # Live recommendations persisted for this user.
    rec_rows = (
        db.query(Recommendation)
        .filter(Recommendation.user_id == user_id_u, Recommendation.is_active.is_(True))
        .all()
    )
    recommended_lessons = []
    for rec in rec_rows:
        lesson = db.query(Lesson).filter(Lesson.id == rec.lesson_id).first()
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
    """DB-backed replacement for the placeholder get_learner_analytics()."""
    dash = get_learner_dashboard(db, learner_id)
    return {
        "learner_id": learner_id,
        "average_accuracy": dash["overall_accuracy_percentage"],
        "lessons_completed": dash["lessons_completed"],
        "weak_letters": [
            rec["expected_gesture"]
            for rec in dash["recommended_lessons"]
            if rec.get("expected_gesture")
        ],
        "weekly_accuracy": {},
        "weekly_improvement_rate": {},
        "weekly_weak_letters": {},
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
