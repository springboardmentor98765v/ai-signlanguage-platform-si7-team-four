from sqlalchemy.orm import Session
from datetime import timedelta

from app.models import models


def get_practice_dates(db: Session, user_id: str):
    sessions = (
        db.query(models.PracticeSession)
        .filter(
            models.PracticeSession.user_id == user_id,
            models.PracticeSession.status == "completed",
        )
        .all()
    )
    dates = {s.started_at.date() for s in sessions if s.started_at is not None}
    return sorted(dates)


def calculate_longest_streak(dates):
    if not dates:
        return 0
    longest = 1
    current = 1
    for i in range(1, len(dates)):
        if dates[i] == dates[i - 1] + timedelta(days=1):
            current += 1
            longest = max(longest, current)
        elif dates[i] != dates[i - 1]:
            current = 1
    return longest


def calculate_current_streak(dates, today):
    if not dates:
        return 0
    date_set = set(dates)
    most_recent = dates[-1]
    if most_recent != today and most_recent != today - timedelta(days=1):
        return 0
    streak = 0
    cursor = most_recent
    while cursor in date_set:
        streak += 1
        cursor -= timedelta(days=1)
    return streak


def get_user_streak(db: Session, user_id: str, today=None):
    from datetime import datetime

    if today is None:
        today = datetime.utcnow().date()
    dates = get_practice_dates(db, user_id)
    current = calculate_current_streak(dates, today)
    longest = calculate_longest_streak(dates)
    return {
        "current_streak": current,
        "longest_streak": longest,
        "total_practice_days": len(dates),
    }