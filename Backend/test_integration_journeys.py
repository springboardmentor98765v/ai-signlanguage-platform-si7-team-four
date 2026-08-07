"""
Milestone 3 Day 8: full-journey integration tests.

Each test walks a realistic end-to-end journey across multiple endpoints,
using a fresh unique user per test so no test depends on shared state.

Two run modes (see Backend/milestone3_api_plan.md):

  1. Docker Compose stack: `INTEGRATION_BASE_URL` is set to the local stack,
     e.g.  INTEGRATION_BASE_URL=http://127.0.0.1:8000 pytest test_integration_journeys.py
     after `docker compose up -d` at the repo root.

  2. Local TestClient simulation (DEFAULT when INTEGRATION_BASE_URL is unset).
     Used in this dev environment because Docker is not installed; the same
     FastAPI app under test is exercised via TestClient instead.
"""
import os
import uuid

import pytest

PASSWORD = "SecurePassword123!"

_BASE_URL = os.getenv("INTEGRATION_BASE_URL", "").strip().rstrip("/")

if _BASE_URL:
    import httpx

    client = httpx.Client(base_url=_BASE_URL, timeout=30.0)
else:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)


def _unique_email(prefix):
    return f"{prefix}_{uuid.uuid4().hex}@example.com"


def _register(role="Learner"):
    email = _unique_email("journey")
    res = client.post(
        "/api/auth/register",
        json={"username": email.split("@")[0], "email": email, "password": PASSWORD, "role": role},
    )
    assert res.status_code == 201, res.text
    return email, res.json()["user_id"]


def _login(email):
    res = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def test_journey_a_register_login_lessons_practice():
    """Learner registers, logs in, browses the lesson catalog, then starts a practice session."""
    email, user_id = _register()
    token = _login(email)
    assert token

    res = client.get("/api/lessons", params={"limit": 3})
    assert res.status_code == 200, res.text
    lessons = res.json()["data"]
    assert len(lessons) >= 1

    lesson_id = str(uuid.uuid4())
    start = client.post(
        "/api/practice/start", params={"user_id": user_id, "lesson_id": lesson_id}
    )
    assert start.status_code == 200, start.text
    session = start.json()
    assert session["session_id"]
    assert session["user_id"] == user_id
    assert session["lesson_id"] == lesson_id
    assert session["status"] == "in_progress"
    assert session["attempt_count"] == 0


def test_journey_b_register_login_notification_read():
    """Learner registers, logs in, receives a notification, lists it, and marks it read."""
    email, user_id = _register()
    token = _login(email)
    assert token

    create = client.post(
        "/api/notifications",
        json={
            "user_id": user_id,
            "title": "Welcome to SignLang",
            "message": "You earned your first badge.",
            "event_type": "badge_earned",
        },
    )
    assert create.status_code == 201, create.text
    notif_id = create.json()["id"]

    listed = client.get(f"/api/notifications/{user_id}")
    assert listed.status_code == 200, listed.text
    notifications = listed.json()
    assert isinstance(notifications, list)
    assert any(n["id"] == notif_id and n["is_read"] is False for n in notifications)

    read = client.patch(f"/api/notifications/{notif_id}/read")
    assert read.status_code == 200, read.text
    assert read.json()["is_read"] is True


def test_journey_c_register_login_dashboard_refresh():
    """Learner registers, logs in, views their dashboard, and refreshes the token."""
    email, user_id = _register()
    token = _login(email)
    assert token

    dash = client.get(
        "/api/auth/dashboard/learner", headers={"Authorization": f"Bearer {token}"}
    )
    assert dash.status_code == 200, dash.text

    refresh = client.post("/api/auth/refresh-token", json={"refresh_token": token})
    assert refresh.status_code == 200, refresh.text
    assert refresh.json()["access_token"]


@pytest.mark.integration
def test_journey_rbac_learner_cannot_open_instructor_dashboard():
    """Journeys still enforce RBAC: a Learner token is denied the instructor dashboard (403)."""
    email, _user_id = _register()
    token = _login(email)
    assert token

    res = client.get(
        "/api/auth/dashboard/instructor", headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 403, res.text
