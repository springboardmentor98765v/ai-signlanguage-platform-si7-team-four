"""
Milestone 4 - Day 2: Accessibility Trainer API response schemas.

Every numeric metric below is a *derived placeholder* so the endpoints are real
and functional before Intern 4's business-logic formulas land. The exact
weighting/thresholds are owned by Intern 4; see `trainer_service.py`.
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class TrainerLearnerSummary(BaseModel):
    """A learner assigned to the calling trainer (GET /api/trainer/learners)."""

    learner_id: str
    username: str
    email: str
    role: str
    assigned_at: Optional[datetime] = None


class EngagementMetric(BaseModel):
    learner_id: str
    engagement_score: float = Field(..., description="0-100 derived score. PENDING Intern 4 final formula.")
    sessions_total: int
    sessions_completed: int
    total_attempts: int
    total_practice_minutes: float
    last_practiced_at: Optional[datetime] = None
    formula_owner: str = "Intern 4 (pending)"


class SkillPoint(BaseModel):
    week_start: str
    average_accuracy: float


class SkillDevelopmentMetric(BaseModel):
    learner_id: str
    improvement_rate: float = Field(..., description="Percentage-point change over time. PENDING Intern 4 final formula.")
    trend: List[SkillPoint]
    weak_letters: List[str]
    formula_owner: str = "Intern 4 (pending)"


class LetterPerformance(BaseModel):
    letter: str
    attempts: int
    correct: int
    accuracy: float


class AssessmentAnalyticsMetric(BaseModel):
    learner_id: str
    total_assessments: int
    average_accuracy: float
    average_confidence: float
    correct_count: int
    correct_percentage: float
    per_letter: List[LetterPerformance]
    formula_owner: str = "Intern 4 (pending)"


class CertificationStatusMetric(BaseModel):
    learner_id: str
    status: str = Field(..., description="passed | in_progress | not_passed | not_attempted")
    level: Optional[str] = Field(None, description="beginner | intermediate | advanced, when a certificate exists")
    overall_score: Optional[float] = None
    certificate_issued_date: Optional[datetime] = None
    formula_owner: str = "Intern 4 (pending)"
