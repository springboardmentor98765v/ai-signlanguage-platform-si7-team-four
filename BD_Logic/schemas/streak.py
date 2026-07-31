from pydantic import BaseModel


class StreakResponse(BaseModel):
    user_id: str
    current_streak: int
    longest_streak: int
    total_practice_days: int