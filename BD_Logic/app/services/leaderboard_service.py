from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models.models import User, AnalyticsSummary
from app.services import streak_service


def get_leaderboard(db: Session, sort_by: str = "accuracy") -> list[dict]:
    if sort_by == "accuracy":
        results = (
            db.query(User, AnalyticsSummary)
            .join(AnalyticsSummary, AnalyticsSummary.user_id == User.id)
            .order_by(desc(AnalyticsSummary.overall_accuracy_percentage))
            .all()
        )

        leaderboard = []

        for index, (user, analytics) in enumerate(results, start=1):
            streak = streak_service.get_user_streak(db, str(user.id))
            current_streak = streak["current_streak"]

            leaderboard.append(
                {
                    "rank": index,
                    "user_id": str(user.id),
                    "learner_name": user.username,
                    "overall_accuracy": analytics.overall_accuracy_percentage,
                    "current_streak": current_streak,
                }
            )

        return leaderboard

    elif sort_by == "streak":
        users = db.query(User).all()

        learner_streaks = []

        for user in users:
            streak = streak_service.get_user_streak(db, str(user.id))
            current_streak = streak["current_streak"]

            analytics = (
                db.query(AnalyticsSummary)
                .filter(AnalyticsSummary.user_id == user.id)
                .first()
            )

            overall_accuracy = (
                analytics.overall_accuracy_percentage if analytics else 0.0
            )

            learner_streaks.append(
                {
                    "user_id": str(user.id),
                    "learner_name": user.username,
                    "overall_accuracy": overall_accuracy,
                    "current_streak": current_streak,
                }
            )

        learner_streaks.sort(
            key=lambda entry: entry["current_streak"],
            reverse=True,
        )

        leaderboard = []

        for index, entry in enumerate(learner_streaks, start=1):
            entry["rank"] = index
            leaderboard.append(entry)

        return leaderboard

    else:
        raise ValueError(f"Unsupported sort_by value: {sort_by}")