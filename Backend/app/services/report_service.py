from typing import Any, Dict, List

from sqlalchemy.orm import Session

from app.models.models import PracticeSession, Assessment, Certificate, Lesson


def _count_lessons_completed(raw_data: Dict[str, Any]) -> int:
    return len(raw_data.get("completed_lessons", []))


def _calculate_average_score(raw_data: Dict[str, Any]) -> float:
    lessons = raw_data.get("completed_lessons", [])
    if not lessons:
        return 0.0
    total_score = sum(lesson["score"] for lesson in lessons)
    return round(total_score / len(lessons), 2)


def _identify_weak_letters(
    raw_data: Dict[str, Any], accuracy_threshold: float = 0.7
) -> List[str]:
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
    return [cert.get("title", "") for cert in raw_data.get("certificates", [])]


def build_progress_report(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "learner_id": raw_data.get("learner_id", ""),
        "lessons_completed": _count_lessons_completed(raw_data),
        "average_score": _calculate_average_score(raw_data),
        "weak_letters": _identify_weak_letters(raw_data),
        "certificates_earned": _list_certificates_earned(raw_data),
    }


def _fetch_learner_raw_data(db: Session, learner_id: str) -> Dict[str, Any]:
    """
    Build raw report data from the real database for a learner.
    """
    user_id = str(learner_id)

    sessions = (
        db.query(PracticeSession)
        .filter(PracticeSession.user_id == user_id, PracticeSession.status == "completed")
        .all()
    )

    assessments: List[Assessment] = []
    for session in sessions:
        assessments.extend(session.assessments)

    # Per-lesson best score (latest overall_accuracy per lesson).
    by_lesson: Dict[str, float] = {}
    for session in sessions:
        for a in session.assessments:
            if session.lesson_id and a.overall_accuracy is not None:
                by_lesson[str(session.lesson_id)] = max(
                    by_lesson.get(str(session.lesson_id), 0.0),
                    a.overall_accuracy,
                )

    completed_lessons = []
    for lesson_id, score in by_lesson.items():
        lesson = db.query(Lesson).filter(Lesson.id == lesson_id).first()
        completed_lessons.append({
            "lesson_id": str(lesson_id),
            "title": lesson.title if lesson else "Completed Lesson",
            "score": round(score, 2),
        })

    # Per-letter attempts across all assessments.
    seen_letters: Dict[str, Dict[str, int]] = {}
    for a in assessments:
        sign = (a.expected_sign or "").strip()
        if not sign:
            continue
        key = sign.upper()
        if key not in seen_letters:
            seen_letters[key] = {"attempts": 0, "correct": 0}
        seen_letters[key]["attempts"] += 1
        if a.overall_accuracy is not None:
            seen_letters[key]["correct"] += a.overall_accuracy / 100.0
    letter_attempts = seen_letters

    certificates = []
    cert_rows = db.query(Certificate).filter(Certificate.user_id == user_id).all()
    for cert in cert_rows:
        certificates.append({
            "certificate_id": str(cert.id),
            "title": f"Certification #{str(cert.id)[:8]}",
            "score": cert.overall_score,
        })

    return {
        "learner_id": learner_id,
        "completed_lessons": completed_lessons,
        "letter_attempts": letter_attempts,
        "certificates": certificates,
    }


def generate_progress_report(learner_id: str, db: Session | None = None) -> Dict[str, Any]:
    if not learner_id:
        raise ValueError("learner_id is required to generate a progress report.")

    if db is None:
        from app.db.database import SessionLocal
        local_db: Session = SessionLocal()
        try:
            raw_data = _fetch_learner_raw_data(local_db, learner_id)
        finally:
            local_db.close()
    else:
        raw_data = _fetch_learner_raw_data(db, learner_id)

    return build_progress_report(raw_data)


def build_progress_report_csv(raw_data: Dict[str, Any]) -> str:
    """Render a progress report as CSV text."""
    lines = [
        "lesson_id,title,score",
    ]
    for lesson in raw_data.get("completed_lessons", []):
        lines.append(
            f"{lesson['lesson_id']},{lesson['title']},{lesson['score']}"
        )
    lines.append("")
    lines.append("letter,attempts,correct")
    for letter, stats in raw_data.get("letter_attempts", {}).items():
        lines.append(f"{letter},{stats['attempts']},{stats['correct']}")
    return "\n".join(lines)