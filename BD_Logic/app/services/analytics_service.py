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


def get_learner_analytics(learner_id: str) -> Dict[str, Any]:
    """
    Returns analytics summary for a learner.
    """

    sessions = _get_placeholder_sessions(learner_id)

    return {
        "learner_id": learner_id,
        "average_accuracy": _calculate_average_accuracy(sessions),
        "lessons_completed": _count_lessons_completed(sessions),
        "weak_letters": _collect_weak_letters(sessions),
    }
