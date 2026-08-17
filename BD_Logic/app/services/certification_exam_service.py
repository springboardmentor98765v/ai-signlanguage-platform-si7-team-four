from typing import Any

from sqlalchemy.orm import Session

from app.models.models import Lesson
from app.services.certificate_service import generate_exam_certificate_pdf


EXAM_LEVELS = {
    "Beginner": {
        "sign_count": 5,
        "pass_threshold": 70.0,
    },
    "Intermediate": {
        "sign_count": 10,
        "pass_threshold": 75.0,
    },
    "Advanced": {
        "sign_count": 15,
        "pass_threshold": 80.0,
    },
    "Professional": {
        "sign_count": 20,
        "pass_threshold": 85.0,
    },
}


class InvalidExamLevelError(Exception):
    pass


class CertificationExamNotPassedError(Exception):
    pass


def get_exam_structure(level: str) -> dict:
    if level not in EXAM_LEVELS:
        raise InvalidExamLevelError(
            f"Invalid certification level: {level}"
        )

    return EXAM_LEVELS[level]


def get_exam_signs(
    db: Session,
    level: str,
) -> list[Lesson]:
    if level not in EXAM_LEVELS:
        raise InvalidExamLevelError(
            f"Invalid certification level: {level}"
        )

    sign_count = EXAM_LEVELS[level]["sign_count"]

    lessons = (
        db.query(Lesson)
        .filter(
            Lesson.category == "alphabet",
            Lesson.expected_gesture.isnot(None),
        )
        .order_by(Lesson.expected_gesture)
        .limit(sign_count)
        .all()
    )

    if len(lessons) < sign_count:
        raise ValueError(
            f"Not enough alphabet lessons available for {level} exam. "
            f"Required: {sign_count}, available: {len(lessons)}."
        )

    return lessons


def calculate_exam_score(
    assessments: list[dict[str, Any]],
) -> float:
    if not assessments:
        return 0.0

    total_score = sum(
        float(assessment.get("overall_accuracy", 0))
        for assessment in assessments
    )

    return round(total_score / len(assessments), 2)


def check_exam_pass(level: str, score: float) -> bool:
    if level not in EXAM_LEVELS:
        raise InvalidExamLevelError(
            f"Invalid certification level: {level}"
        )

    threshold = EXAM_LEVELS[level]["pass_threshold"]

    if threshold is None:
        raise ValueError(
            f"Pass threshold has not been configured for {level}."
        )

    return score >= threshold


def complete_certification_exam(
    level: str,
    assessments: list[dict[str, Any]],
    learner_name: str | None = None,
) -> dict:
    if level not in EXAM_LEVELS:
        raise InvalidExamLevelError(
            f"Invalid certification level: {level}"
        )

    score = calculate_exam_score(assessments)
    passed = check_exam_pass(level, score)

    result = {
        "level": level,
        "score": score,
        "passed": passed,
        "total_questions": len(assessments),
    }

    if passed and learner_name:
        generate_exam_certificate_pdf(
            learner_name=learner_name,
            level=level,
            score=score,
        )

        result["certificate_generated"] = True
    else:
        result["certificate_generated"] = False

    return result