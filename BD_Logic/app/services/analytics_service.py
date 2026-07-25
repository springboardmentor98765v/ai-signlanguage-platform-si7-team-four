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