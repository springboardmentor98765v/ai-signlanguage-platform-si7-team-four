"""
Milestone 4 Day 6: live-deploy smoke tests.

Proves a running backend (local or deployed) is healthy and the core auth loop
works end to end:
    - /health          -> healthy
    - register (Learner)
    - login            -> access token
    - one protected route (learner dashboard, Bearer JWT)

Run against a live deployment with:

    BACKEND_BASE_URL=https://<live-url> python3 -m pytest test_smoke_live.py -q

With BACKEND_BASE_URL unset the tests run in-process against the FastAPI app via
TestClient (same convention as test_integration_journeys.py), so the default
`python3 -m pytest -q` suite stays green without a running server.
"""
import os
import uuid

import pytest

PASSWORD = "SecurePassword123!"

_BASE_URL = os.getenv("BACKEND_BASE_URL", "").strip().rstrip("/")

pytestmark = pytest.mark.integration

if _BASE_URL:
    import httpx

    client = httpx.Client(base_url=_BASE_URL, timeout=30.0)
else:
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)


def _uid(prefix):
    return f"{prefix}_{uuid.uuid4().hex}"


def test_health_check():
    res = client.get("/health")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["status"] == "healthy"
    assert body["env_loaded"] is True


def test_register_login_protected_route():
    email = f"{_uid('smoke')}@example.com"
    username = _uid("smokeuser")[:40]

    reg = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "email": email,
            "password": PASSWORD,
            "role": "Learner",
        },
    )
    assert reg.status_code == 201, reg.text
    assert reg.json()["user_id"]

    login = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    assert token

    dash = client.get(
        "/api/auth/dashboard/learner",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert dash.status_code == 200, dash.text
    assert "message" in dash.json()
