"""
Milestone 3 - Day 3: Event-triggered notification hooks (Intern 2)
------------------------------------------------------------------
Triggers each wired hook (certificate_ready, badge_earned, new_recommendation)
through the service functions and confirms a Notification row is created and
retrievable via the Day 2 "list notifications" API (GET /api/notifications/{user_id}).
"""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.main import app
from app.services.assessment_service import assess
from app.services.certificate_service import LearnerProgress, generate_certificate_pdf
from app.services.recommendation_service import generate_recommendations

client = TestClient(app)


@pytest.fixture
def user_id():
    """Register a fresh user through the real API and return their UUID."""
    res = client.post(
        "/api/auth/register",
        json={
            "username": f"hook{uuid.uuid4().hex[:8]}",
            "email": f"hook_{uuid.uuid4().hex[:10]}@example.com",
            "password": "SecurePassword123!",
            "role": "Learner",
        },
    )
    assert res.status_code == 201
    return res.json()["user_id"]


def _list_notifications(user_id: str):
    res = client.get(f"/api/notifications/{user_id}")
    assert res.status_code == 200
    return res.json()


def test_certificate_ready_hook_creates_notification(user_id):
    """Generate a certificate -> 'certificate_ready' notification appears."""
    db = SessionLocal()
    try:
        pdf = generate_certificate_pdf(
            "Hook Learner",
            LearnerProgress(average_score=95.0, all_required_letters_practiced=True),
            db=db,
            user_id=user_id,
        )
        assert pdf, "certificate PDF should be generated"
    finally:
        db.close()

    notifs = _list_notifications(user_id)
    assert any(
        n["event_type"] == "certificate_ready" for n in notifs
    ), "certificate_ready notification missing"


def test_badge_earned_hook_creates_notification(user_id):
    """Correct assessment (lesson passed) -> 'badge_earned' notification appears."""
    db = SessionLocal()
    try:
        result = assess(
            predicted_sign="A",
            expected_sign="A",
            confidence=0.95,
            hand_shape_score=0.9,
            finger_position_score=0.9,
            timing_score=0.9,
            db=db,
            user_id=user_id,
        )
        assert result["is_correct"] is True
    finally:
        db.close()

    notifs = _list_notifications(user_id)
    assert any(
        n["event_type"] == "badge_earned" for n in notifs
    ), "badge_earned notification missing"


def test_badge_earned_not_fired_on_incorrect_attempt(user_id):
    """Incorrect assessment must NOT raise a badge notification."""
    db = SessionLocal()
    try:
        result = assess(
            predicted_sign="B",
            expected_sign="A",
            confidence=0.4,
            hand_shape_score=0.2,
            finger_position_score=0.2,
            timing_score=0.2,
            db=db,
            user_id=user_id,
        )
        assert result["is_correct"] is False
    finally:
        db.close()

    notifs = _list_notifications(user_id)
    assert not any(n["event_type"] == "badge_earned" for n in notifs)


def test_new_recommendation_hook_creates_notification(user_id):
    """Low scores across 3+ attempts -> 'new_recommendation' notification appears."""
    db = SessionLocal()
    try:
        recs = generate_recommendations(
            [{"sign": "Z", "score": 50.0}] * 5,
            db=db,
            user_id=user_id,
        )
        assert recs, "recommendations should be generated"
    finally:
        db.close()

    notifs = _list_notifications(user_id)
    assert any(
        n["event_type"] == "new_recommendation" for n in notifs
    ), "new_recommendation notification missing"
