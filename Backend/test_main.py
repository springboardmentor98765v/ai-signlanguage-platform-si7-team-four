import uuid

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

# ==============================================================================
# Shared helpers (unique emails per test so the in-memory rate limiter and
# MOCK_USER_DB never leak state between tests)
# ==============================================================================

PASSWORD = "SecurePassword123!"


def _unique_email() -> str:
    return f"main_{uuid.uuid4().hex}@example.com"


def _register(email: str, role: str = "Learner"):
    return client.post("/api/auth/register", json={
        "username": f"user_{uuid.uuid4().hex[:8]}",
        "email": email,
        "password": PASSWORD,
        "role": role,
    })


def _login(email: str, password: str = PASSWORD):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def _access_token(email: str) -> str:
    res = _login(email)
    assert res.status_code == 200, res.text
    return res.json()["access_token"]

def test_gateway_root_and_health_endpoints():
    """Verifies baseline reachability of base system parameters."""
    response = client.get("/")
    assert response.status_code == 200
    assert "milestone_tracker" in response.json()

    health_response = client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json()["status"] == "healthy"

def test_course_seeding_and_retrieval_flow():
    """Verifies that the Alphabet course data seeds automatically load correctly."""
    response = client.get("/api/courses/modules")
    assert response.status_code == 200
    data = response.json()
    
    # Assert that our automatic database seed initialized correctly
    assert len(data) > 0
    assert data[0]["module_id"] == "mod_alphabet_101"
    # Ensure all 26 default alphabet letters generated smoothly
    assert len(data[0]["lessons"]) == 26

def test_unauthenticated_rbac_route_protection():
    """Verifies that unauthorized requests are blocked by the gateway architecture."""
    # Attempting course generation without authentication header badge must trigger block
    response = client.post("/api/courses/modules", json={
        "title": "Hacker Course",
        "description": "Exploiting system parameters"
    })
    # Our dependency system triggers 401 via missing token metadata
    assert response.status_code in [401, 403]


# ==============================================================================
# Milestone 3 Day 7: Core auth endpoint coverage
# ==============================================================================

def test_register_user_success():
    """POST /api/auth/register returns 201 and a user id for a new account."""
    res = _register(_unique_email())
    assert res.status_code == 201, res.text
    body = res.json()
    assert "user_id" in body
    assert body["role"] == "Learner"


def test_register_duplicate_email_fails():
    """Registering the same email twice is rejected with 400."""
    email = _unique_email()
    assert _register(email).status_code == 201
    res = _register(email)
    assert res.status_code == 400, res.text
    assert "already exists" in res.json()["detail"].lower()


def test_login_success_returns_tokens():
    """POST /api/auth/login with correct credentials returns access + refresh tokens."""
    email = _unique_email()
    assert _register(email).status_code == 201

    res = _login(email)
    assert res.status_code == 200, res.text
    tokens = res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


def test_login_wrong_password_fails():
    """Login with an incorrect password is rejected with 401."""
    email = _unique_email()
    assert _register(email).status_code == 201

    res = _login(email, password="WrongPassword123!")
    assert res.status_code == 401, res.text


def test_login_sixth_rapid_attempt_blocked_with_429():
    """Per-user rate limiting: the 6th rapid login for one email returns 429."""
    email = _unique_email()
    assert _register(email).status_code == 201

    for _ in range(5):
        assert _login(email).status_code == 200

    blocked = _login(email)
    assert blocked.status_code == 429, blocked.text
    assert blocked.json()["error"] == "rate_limit_exceeded"
    assert blocked.headers.get("Retry-After") is not None


def test_learner_dashboard_allowed_for_learner():
    """A Learner token can access the learner dashboard."""
    email = _unique_email()
    assert _register(email, role="Learner").status_code == 201
    token = _access_token(email)

    res = client.get("/api/auth/dashboard/learner",
                     headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200, res.text
    assert "Welcome" in res.json()["message"]


def test_instructor_dashboard_denied_for_learner_403():
    """A Learner token accessing the instructor dashboard is denied with 403."""
    email = _unique_email()
    assert _register(email, role="Learner").status_code == 201
    token = _access_token(email)

    res = client.get("/api/auth/dashboard/instructor",
                     headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403, res.text
    assert "Access Denied" in res.json()["detail"]


def test_instructor_dashboard_allowed_for_instructor():
    """An Instructor token can access the instructor dashboard."""
    email = _unique_email()
    assert _register(email, role="Instructor").status_code == 201
    token = _access_token(email)

    res = client.get("/api/auth/dashboard/instructor",
                     headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200, res.text
    assert "Welcome" in res.json()["message"]


def test_dashboards_require_token_401():
    """Dashboards reject requests without a bearer token (401)."""
    res = client.get("/api/auth/dashboard/learner")
    assert res.status_code in (401, 403)