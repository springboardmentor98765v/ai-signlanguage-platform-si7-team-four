from typing import Any, Dict, List


def _fetch_learner_raw_data(learner_id: str) -> Dict[str, Any]:
    """
    Fetch raw learner data needed to build a progress report.

    Args:
        learner_id: Unique identifier of the learner.

    Returns:
        A dictionary of raw data in the shape expected by the report
        builder functions in this module.
    """
    return {
        "learner_id": learner_id,
        "completed_lessons": [
            {"lesson_id": "L1", "title": "Alphabet Basics A-F", "score": 85},
            {"lesson_id": "L2", "title": "Alphabet Basics G-M", "score": 72},
            {"lesson_id": "L3", "title": "Alphabet Basics N-S", "score": 60},
            {"lesson_id": "L4", "title": "Common Greetings", "score": 90},
        ],
        "letter_attempts": {
            "A": {"attempts": 10, "correct": 9},
            "B": {"attempts": 8, "correct": 5},
            "C": {"attempts": 6, "correct": 3},
            "M": {"attempts": 7, "correct": 6},
            "S": {"attempts": 9, "correct": 4},
        },
        "certificates": [
            {"certificate_id": "CERT-ALPHA-1", "title": "Alphabet A-F Completion"},
        ],
    }


def _count_lessons_completed(raw_data: Dict[str, Any]) -> int:
    """
    Count the number of lessons a learner has completed.

    Args:
        raw_data: Raw learner data as returned by _fetch_learner_raw_data.

    Returns:
        Number of completed lessons.
    """
    return len(raw_data.get("completed_lessons", []))


def _calculate_average_score(raw_data: Dict[str, Any]) -> float:
    """
    Calculate the learner's average score across all completed lessons.

    Args:
        raw_data: Raw learner data as returned by _fetch_learner_raw_data.

    Returns:
        Average score rounded to 2 decimal places. Returns 0.0 if the
        learner has no completed lessons.
    """
    lessons = raw_data.get("completed_lessons", [])
    if not lessons:
        return 0.0

    total_score = sum(lesson["score"] for lesson in lessons)
    return round(total_score / len(lessons), 2)


def _identify_weak_letters(
    raw_data: Dict[str, Any], accuracy_threshold: float = 0.7
) -> List[str]:
    """
    Identify letters the learner struggles with, based on accuracy.

    Args:
        raw_data: Raw learner data as returned by _fetch_learner_raw_data.
        accuracy_threshold: Minimum accuracy (0.0 - 1.0) required for a
            letter to NOT be considered weak. Defaults to 0.7 (70%).

    Returns:
        A list of letters (strings) identified as weak, sorted
        alphabetically.
    """
    weak_letters: List[str] = []
    letter_attempts = raw_data.get("letter_attempts", {})

    for letter, stats in letter_attempts.items():
        attempts = stats.get("attempts", 0)
        correct = stats.get("correct", 0)

        if attempts == 0:
            continue

        accuracy = correct / attempts
        if accuracy < accuracy_threshold:
            weak_letters.append(letter)

    return sorted(weak_letters)


def _list_certificates_earned(raw_data: Dict[str, Any]) -> List[str]:
    """
    Extract the titles of certificates earned by the learner.

    Args:
        raw_data: Raw learner data as returned by _fetch_learner_raw_data.

    Returns:
        A list of certificate titles earned by the learner.
    """
    certificates = raw_data.get("certificates", [])
    return [cert["title"] for cert in certificates]


def generate_progress_report(learner_id: str) -> Dict[str, Any]:
    """
    Generate a Progress Report for a single learner.

    Args:
        learner_id: Unique identifier of the learner to report on.

    Returns:
        A dictionary with the following keys:
            - learner_id (str): The learner's unique identifier.
            - lessons_completed (int): Number of lessons completed.
            - average_score (float): Average score across completed lessons.
            - weak_letters (List[str]): Letters the learner struggles with.
            - certificates_earned (List[str]): Titles of earned certificates.

    Raises:
        ValueError: If learner_id is empty or not provided.
    """
    if not learner_id:
        raise ValueError("learner_id is required to generate a progress report.")

    raw_data = _fetch_learner_raw_data(learner_id)

    report: Dict[str, Any] = {
        "learner_id": learner_id,
        "lessons_completed": _count_lessons_completed(raw_data),
        "average_score": _calculate_average_score(raw_data),
        "weak_letters": _identify_weak_letters(raw_data),
        "certificates_earned": _list_certificates_earned(raw_data),
    }

    return report