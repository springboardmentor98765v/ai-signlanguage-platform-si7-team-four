import csv
import os

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

def _fetch_class_summary_data() -> List[Dict[str, Any]]:
    """
    Fetch placeholder class summary data for instructor export.

    Returns:
        A list of learner summary records.
    """
    return [
        {
            "learner_id": "L001",
            "learner_name": "Sample Learner 1",
            "lessons_completed": 8,
            "average_score": 91.50,
            "current_streak": 6,
        },
        {
            "learner_id": "L002",
            "learner_name": "Sample Learner 2",
            "lessons_completed": 7,
            "average_score": 84.25,
            "current_streak": 4,
        },
        {
            "learner_id": "L003",
            "learner_name": "Sample Learner 3",
            "lessons_completed": 5,
            "average_score": 73.00,
            "current_streak": 2,
        },
    ]

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

def export_progress_report_csv(learner_id: str) -> str:
    """
    Exports the learner's progress report as a CSV file.

    Args:
        learner_id: Unique identifier of the learner.

    Returns:
        Path to the generated CSV file.
    """

    report = generate_progress_report(learner_id)

    os.makedirs("reports", exist_ok=True)

    file_path = os.path.join(
        "reports",
        f"progress_report_{learner_id}.csv"
    )

    with open(file_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(["Field", "Value"])
        writer.writerow(["Learner ID", report["learner_id"]])
        writer.writerow(["Lessons Completed", report["lessons_completed"]])
        writer.writerow(["Average Score", report["average_score"]])
        writer.writerow(
            ["Weak Letters", ", ".join(report["weak_letters"])]
        )
        writer.writerow(
            ["Certificates Earned",
             ", ".join(report["certificates_earned"])]
        )

    return file_path

def export_class_summary_csv() -> str:
    """
    Exports the instructor class summary as a CSV file.

    Returns:
        Path to the generated CSV file.
    """

    class_summary = _fetch_class_summary_data()

    os.makedirs("reports", exist_ok=True)

    file_path = os.path.join(
        "reports",
        "class_summary_report.csv"
    )

    with open(file_path, mode="w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)

        writer.writerow(
            [
                "Learner ID",
                "Learner Name",
                "Lessons Completed",
                "Average Score",
                "Current Streak",
            ]
        )

        for learner in class_summary:
            writer.writerow(
                [
                    learner["learner_id"],
                    learner["learner_name"],
                    learner["lessons_completed"],
                    learner["average_score"],
                    learner["current_streak"],
                ]
            )

    return file_path