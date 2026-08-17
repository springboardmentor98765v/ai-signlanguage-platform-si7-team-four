from pydantic import BaseModel
from typing import List


class BadgeResponse(BaseModel):
    badge_name: str
    earned: bool
    description: str


class UserBadgesResponse(BaseModel):
    user_id: str
    badges: List[BadgeResponse]