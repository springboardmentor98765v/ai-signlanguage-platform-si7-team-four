import uuid

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.routers.recommendation import LearnerHistoryRequest

client = TestClient(app)

# ==============================================================================
# INPUT VALIDATION TESTS (Day 5 hardening)
#
# Verifies that all free-text request fields reject malicious payloads
# (SQL injection / XSS patterns) and that out-of-range numeric / enum values
# are rejected with HTTP 422 via Pydantic validation.
# ==============================================================================

SQLI_PATTERN = "'; DROP TABLE users; --"
XSS_PATTERN = "<script>alert('xss')</script>"


def make_uuid() -> str:
    return str(uuid.uuid4())


def _register_and_login(role: str = "Admin") -> str:
    """Register a fresh user and return its bearer access token."""
    email = f"val_{role.lower()}_{make_uuid()}@example.com"
    reg = client.post("/api/auth/register", json={
        "username": f"val_{role.lower()}_{uuid.uuid4().hex[:6]}",
        "email": email,
        "password": "SecurePassword123!",
        "role": role,
    })
    assert reg.status_code == 201, reg.text
    login = client.post("/api/auth/login", json={"email": email, "password": "SecurePassword123!"})
    assert login.status_code == 200, login.text
    return login.json()["access_token"]


def _auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ------------------------------------------------------------------------------
# Auth & Profile
# ------------------------------------------------------------------------------

def test_login_rejects_sql_injection_in_username():
    res = client.post("/api/auth/login", json={
        "username": "admin' OR '1'='1",
        "password": "x",
    })
    assert res.status_code in (401, 422)


def test_login_rejects_sql_injection_in_password():
    res = client.post("/api/auth/login", json={
        "username": "anyuser",
        "password": "' OR '1'='1' --",
    })
    assert res.status_code in (401, 422)


def test_register_rejects_xss_in_username():
    res = client.post("/api/auth/register", json={
        "username": XSS_PATTERN,
        "email": f"xss_{make_uuid()}@example.com",
        "password": "SecurePassword123!",
    })
    assert res.status_code == 422


def test_register_rejects_sql_injection_in_password():
    res = client.post("/api/auth/register", json={
        "username": "sqluser",
        "email": f"sql_{make_uuid()}@example.com",
        "password": SQLI_PATTERN,
    })
    assert res.status_code == 422


def test_register_rejects_weak_password():
    res = client.post("/api/auth/register", json={
        "username": "shortpwuser",
        "email": f"short_{make_uuid()}@example.com",
        "password": "abc",
    })
    assert res.status_code == 422


def test_profile_update_rejects_sql_injection_username():
    res = client.patch("/api/users/me", json={
        "username": "admin' OR '1'='1",
    })
    assert res.status_code in (404, 422)


def test_change_password_rejects_short_new_password():
    res = client.post("/api/users/change-password", json={
        "current_password": "CurrentPass123!",
        "new_password": "short",
    })
    assert res.status_code == 422


# ------------------------------------------------------------------------------
# Lessons
# ------------------------------------------------------------------------------

def test_lesson_create_valid_payload_succeeds():
    token = _register_and_login()
    res = client.post("/api/lessons", json={
        "module_id": make_uuid(),
        "title": "Valid Lesson Title",
        "expected_gesture": "A",
        "category": "Alphabet",
        "difficulty": "Easy",
    }, headers=_auth_headers(token))
    assert res.status_code == 201


def test_lesson_create_rejects_sql_injection_title():
    token = _register_and_login()
    res = client.post("/api/lessons", json={
        "module_id": make_uuid(),
        "title": SQLI_PATTERN,
        "expected_gesture": "A",
        "category": "Alphabet",
        "difficulty": "Easy",
    }, headers=_auth_headers(token))
    assert res.status_code == 422


def test_lesson_create_rejects_invalid_category():
    token = _register_and_login()
    res = client.post("/api/lessons", json={
        "module_id": make_uuid(),
        "title": "Valid Title",
        "expected_gesture": "A",
        "category": "NotACategory",
        "difficulty": "Easy",
    }, headers=_auth_headers(token))
    assert res.status_code == 422


def test_lesson_create_rejects_invalid_difficulty():
    token = _register_and_login()
    res = client.post("/api/lessons", json={
        "module_id": make_uuid(),
        "title": "Valid Title",
        "expected_gesture": "A",
        "category": "Alphabet",
        "difficulty": "Impossible",
    }, headers=_auth_headers(token))
    assert res.status_code == 422


def test_lesson_create_rejects_oversized_gesture():
    token = _register_and_login()
    res = client.post("/api/lessons", json={
        "module_id": make_uuid(),
        "title": "Valid Title",
        "expected_gesture": "ABCDEF",
        "category": "Alphabet",
        "difficulty": "Easy",
    }, headers=_auth_headers(token))
    assert res.status_code == 422


def test_lesson_bulk_csv_rejects_sql_injection_content():
    res = client.post("/api/lessons/bulk-upload-csv", json={
        "csv_content": "title,expected_gesture\n'; DROP TABLE lessons; --,A\n",
    })
    assert res.status_code == 422


# ------------------------------------------------------------------------------
# Day 3 Features
# ------------------------------------------------------------------------------

def test_feedback_rejects_out_of_range_rating():
    res = client.post("/api/v1/feedback/submit", json={
        "user_id": 1,
        "category": "General",
        "rating": 6,
        "comments": "Great platform",
    })
    assert res.status_code == 422


def test_feedback_rejects_malicious_comments():
    res = client.post("/api/v1/feedback/submit", json={
        "user_id": 1,
        "category": "General",
        "rating": 4,
        "comments": SQLI_PATTERN,
    })
    assert res.status_code == 422


def test_translation_log_rejects_malicious_text():
    res = client.post("/api/v1/translations/log", json={
        "user_id": 1,
        "translated_text": XSS_PATTERN,
        "confidence_level": 0.9,
    })
    assert res.status_code == 422


def test_translation_log_rejects_out_of_range_confidence():
    res = client.post("/api/v1/translations/log", json={
        "user_id": 1,
        "translated_text": "hello",
        "confidence_level": 1.5,
    })
    assert res.status_code == 422


def test_progress_update_rejects_out_of_range_accuracy():
    res = client.post("/api/v1/progress/update", json={
        "user_id": 1,
        "course_id": 1,
        "completed_lessons": 2,
        "total_lessons": 5,
        "accuracy_score": 150,
    })
    assert res.status_code == 422


def test_sign_evaluation_rejects_sql_injection():
    res = client.post("/api/v1/day3/evaluate-sign", json={
        "sign_text": SQLI_PATTERN,
        "user_id": 1,
    })
    assert res.status_code == 422


def test_recommendation_rejects_malicious_sign():
    with pytest.raises(ValidationError):
        LearnerHistoryRequest(
            learner_id="learner-1",
            attempts=[{"sign": SQLI_PATTERN, "score": 80}],
        )


def test_recommendation_rejects_out_of_range_score():
    with pytest.raises(ValidationError):
        LearnerHistoryRequest(
            learner_id="learner-1",
            attempts=[{"sign": "A", "score": 150}],
        )


def test_integration_sync_rejects_malicious_action_type():
    res = client.post("/api/integration/test-sync", json={
        "userId": "user-1",
        "actionType": XSS_PATTERN,
        "confidenceScore": 0.9,
    })
    assert res.status_code == 422


def test_integration_sync_rejects_out_of_range_confidence():
    res = client.post("/api/integration/test-sync", json={
        "userId": "user-1",
        "actionType": "translate",
        "confidenceScore": 2.0,
    })
    assert res.status_code == 422


# ------------------------------------------------------------------------------
# Admin (role enums & CSV upload validation)
# ------------------------------------------------------------------------------

def _ensure_admin() -> str:
    email = "validation_admin@example.com"
    res = client.post("/api/auth/register", json={
        "username": "validation_admin",
        "email": email,
        "password": "SecurePassword123!",
        "role": "Admin",
    })
    return email


def _admin_bulk_upload(csv_text: str) -> "Response":
    admin_email = _ensure_admin()
    return client.post(
        "/api/admin/bulk-upload-lessons",
        files={"file": ("lessons.csv", csv_text, "text/csv")},
        params={"admin_email": admin_email},
    )


def test_admin_role_update_rejects_invalid_role():
    _ensure_admin()
    res = client.patch("/api/admin/user-role", json={
        "target_email": "someone@example.com",
        "new_role": "Superuser",
    })
    assert res.status_code == 422


def test_admin_role_update_rejects_malicious_email():
    _ensure_admin()
    res = client.patch("/api/admin/user-role", json={
        "target_email": "' OR '1'='1",
        "new_role": "Admin",
    })
    assert res.status_code in (404, 422)


def test_admin_bulk_upload_rejects_invalid_category_row():
    csv_text = (
        "title,description,expected_gesture,category,difficulty,module_id\n"
        f"Bad Category,'not allowed','A','NotACategory','Easy','{make_uuid()}'\n"
    )
    res = _admin_bulk_upload(csv_text)
    assert res.status_code == 200
    body = res.json()
    assert body["rows_inserted"] == 0
    assert body["rows_rejected"] == 1
    assert "category" in body["rejected_rows"][0]["reason"].lower()


def test_admin_bulk_upload_rejects_malicious_title_row():
    csv_text = (
        "title,description,expected_gesture,category,difficulty,module_id\n"
        f"'<script>x</script>',description,'A','alphabet','easy','{make_uuid()}'\n"
    )
    res = _admin_bulk_upload(csv_text)
    assert res.status_code == 200
    body = res.json()
    assert body["rows_inserted"] == 0
    assert body["rows_rejected"] == 1
