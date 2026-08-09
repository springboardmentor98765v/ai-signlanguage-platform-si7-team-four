import uuid

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

# ==============================================================================
# PER-USER RATE LIMITING TESTS (Milestone 3 Day 6)
#
# Verifies slowapi-based per-user (email-keyed) limiting on the sensitive auth
# endpoints:
#   - POST /api/auth/login            (5/minute per account)
#   - POST /api/auth/register         (5/minute per account)
#   - POST /api/auth/forgot-password  (5/minute per account)
#
# All emails are unique per test so a limited account never leaks into another
# test's window (the limiter storage is in-memory for the whole pytest process).
# ==============================================================================

PASSWORD = "SecurePassword123!"


def _unique_email() -> str:
    return f"ratelimit_{uuid.uuid4().hex}@example.com"


def _register(email: str) -> int:
    return client.post("/api/auth/register", json={
        "username": f"user_{uuid.uuid4().hex[:8]}",
        "email": email,
        "password": PASSWORD,
        "role": "Learner",
    }).status_code


def _login(email: str) -> "Response":
    return client.post("/api/auth/login", json={
        "email": email,
        "password": PASSWORD,
    })


# ------------------------------------------------------------------------------
# Checkpoint: normal user is NOT blocked during regular use
# ------------------------------------------------------------------------------

def test_normal_user_is_not_blocked_during_regular_use():
    email = _unique_email()
    assert _register(email) == 201

    # A handful of logins well below the 5/min limit must all succeed.
    for _ in range(3):
        res = _login(email)
        assert res.status_code == 200, res.text
        assert "access_token" in res.json()


# ------------------------------------------------------------------------------
# Checkpoint: rapid repeated attempts are correctly blocked
# ------------------------------------------------------------------------------

def test_sixth_rapid_login_is_blocked_with_429():
    email = _unique_email()
    assert _register(email) == 201

    # First 5 attempts within the window are allowed.
    for i in range(5):
        res = _login(email)
        assert res.status_code == 200, f"attempt {i + 1}: {res.text}"

    # The 6th rapid attempt is blocked with a friendly 429.
    blocked = _login(email)
    assert blocked.status_code == 429, blocked.text

    body = blocked.json()
    assert body["error"] == "rate_limit_exceeded"
    assert "Too many requests" in body["message"]
    assert 1 <= body["retry_after_seconds"] <= 120
    assert blocked.headers.get("Retry-After") == str(body["retry_after_seconds"])


def test_register_is_rate_limited_per_email():
    email = _unique_email()

    statuses = [_register(email) for _ in range(6)]
    # First registration succeeds, duplicates are 400 (already exists), and the
    # 6th call must be throttled to 429.
    assert statuses[:5] == [201, 400, 400, 400, 400], statuses
    assert statuses[5] == 429


def test_forgot_password_is_rate_limited_per_email():
    email = _unique_email()
    assert _register(email) == 201

    for _ in range(5):
        res = client.post("/api/auth/forgot-password", json={"email": email})
        assert res.status_code == 200, res.text

    blocked = client.post("/api/auth/forgot-password", json={"email": email})
    assert blocked.status_code == 429, blocked.text
    assert blocked.json()["error"] == "rate_limit_exceeded"


# ------------------------------------------------------------------------------
# Checkpoint: per-user (not per-IP) limiting - shared IP must not be blocked
# ------------------------------------------------------------------------------

def test_different_email_on_same_ip_is_not_blocked():
    victim_email = _unique_email()
    other_email = _unique_email()
    assert _register(victim_email) == 201
    assert _register(other_email) == 201

    # Exhaust the victim's login budget...
    for _ in range(5):
        assert _login(victim_email).status_code == 200
    assert _login(victim_email).status_code == 429

    # ...but a DIFFERENT account from the same client (same IP) still works.
    res = _login(other_email)
    assert res.status_code == 200, res.text
    assert "access_token" in res.json()
