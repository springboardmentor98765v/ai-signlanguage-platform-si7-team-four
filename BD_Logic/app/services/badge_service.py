from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models import models
from app.services import streak_service


def check_practice_starter(db: Session, user_id: str):
    session = (
        db.query(models.PracticeSession)
        .filter(
            models.PracticeSession.user_id == user_id,
            models.PracticeSession.status == "completed",
        )
        .first()
    )
    return session is not None


def check_seven_day_streak(db: Session, user_id: str):
    streak_data = streak_service.get_user_streak(db, user_id)
    return streak_data["longest_streak"] >= 7


def check_alphabet_master(db: Session, user_id: str):
    alphabet_lessons = (
        db.query(models.Lesson)
        .filter(models.Lesson.category == "alphabet")
        .all()
    )
    if not alphabet_lessons:
        return False
    for lesson in alphabet_lessons:
        best_accuracy = (
            db.query(func.max(models.Assessment.overall_accuracy))
            .join(
                models.PracticeSession,
                models.Assessment.session_id == models.PracticeSession.id,
            )
            .filter(
                models.PracticeSession.user_id == user_id,
                models.PracticeSession.lesson_id == lesson.id,
            )
            .scalar()
        )
        if best_accuracy is None or best_accuracy < 80:
            return False
    return True


def get_user_badges(db: Session, user_id: str):
    return [
        {
            "badge_name": "Practice Starter",
            "earned": check_practice_starter(db, user_id),
            "description": "Complete your first practice session.",
        },
        {
            "badge_name": "7-Day Streak",
            "earned": check_seven_day_streak(db, user_id),
            "description": "Practice for 7 consecutive days.",
        },
        {
            "badge_name": "Alphabet Master",
            "earned": check_alphabet_master(db, user_id),
            "description": "Complete all alphabet letters with at least 80% accuracy.",
        },
    ]