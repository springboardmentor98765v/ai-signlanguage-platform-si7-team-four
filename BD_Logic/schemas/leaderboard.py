from pydantic import BaseModel
from typing import List


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    learner_name: str
    overall_accuracy: float
    current_streak: int


class LeaderboardResponse(BaseModel):
    sort_by: str
    entries: List[LeaderboardEntry]