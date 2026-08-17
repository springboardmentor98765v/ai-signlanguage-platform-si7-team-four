"""
Milestone 3 Day 7: Admin bulk-operation endpoint coverage.

Covers the Day-4 bulk admin APIs:
  - POST /api/admin/bulk-user-status       (activate/deactivate many users)
  - POST /api/admin/bulk-upload-lessons    (CSV bulk lesson upload)

Admin verification is email-based (`?admin_email=` query param), so each test
registers a fresh admin through the API first. All writes go to the isolated
temp database from `conftest.py`.
"""

import uuid

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

PASSWORD = "SecurePassword123!"


def _unique_email() -> str:
    return f"adminbulk_{uuid.uuid4().hex}@example.com"


def _register_user(role: str = "Learner") -> str:
    """Register a user and return the JSON body (contains user_id)."""
    res = client.post("/api/auth/register", json={
        "username": f"bulk_{uuid.uuid4().hex[:8]}",
        "email": _unique_email(),
        "password": PASSWORD,
        "role": role,
    })
    assert res.status_code == 201, res.text
    return res.json()


def _admin_email() -> str:
    """Register a fresh admin and return its email."""
    email = _unique_email()
    res = client.post("/api/auth/register", json={
        "username": f"bulkadmin_{uuid.uuid4().hex[:8]}",
        "email": email,
        "password": PASSWORD,
        "role": "Admin",
    })
    assert res.status_code == 201, res.text
    return email


def _registered_user_email() -> str:
    """Register a fresh learner and return its email."""
    email = _unique_email()
    res = client.post("/api/auth/register", json={
        "username": f"bulkuser_{uuid.uuid4().hex[:8]}",
        "email": email,
        "password": PASSWORD,
        "role": "Learner",
    })
    assert res.status_code == 201, res.text
    return email


def test_bulk_user_status_success():
    """POST /api/admin/bulk-user-status deactivates the given users by email."""
    admin = _admin_email()
    user_a = _registered_user_email()
    user_b = _registered_user_email()

    res = client.post(
        "/api/admin/bulk-user-status",
        params={"admin_email": admin},
        json={"user_ids": [user_a, user_b], "is_active": False},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["updated_count"] == 2
    assert body["is_active"] is False
    assert body["not_found_count"] == 0


def test_bulk_user_status_reports_missing_users():
    """Unknown user ids are reported in `not_found`, not silently dropped."""
    admin = _admin_email()
    known = _registered_user_email()

    res = client.post(
        "/api/admin/bulk-user-status",
        params={"admin_email": admin},
        json={"user_ids": [known, "no_such_user@example.com"], "is_active": True},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["updated_count"] == 1
    assert body["not_found_count"] == 1
    assert "no_such_user@example.com" in body["not_found"]


def test_bulk_user_status_requires_admin():
    """A non-admin caller is denied with 403."""
    learner = _registered_user_email()
    res = client.post(
        "/api/admin/bulk-user-status",
        params={"admin_email": learner},
        json={"user_ids": [learner], "is_active": False},
    )
    assert res.status_code == 403


def test_bulk_upload_lessons_success():
    """A valid CSV upload inserts every lesson row."""
    admin = _admin_email()
    module_id = str(uuid.uuid4())
    csv_text = (
        "title,description,expected_gesture,category,difficulty,module_id\n"
        f"CSV Lesson One,description one,A,alphabet,easy,{module_id}\n"
        f"CSV Lesson Two,description two,B,words,medium,{module_id}\n"
    )

    res = client.post(
        "/api/admin/bulk-upload-lessons",
        params={"admin_email": admin},
        files={"file": ("lessons.csv", csv_text, "text/csv")},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["rows_processed"] == 2
    assert body["rows_inserted"] == 2
    assert body["rows_rejected"] == 0


def test_bulk_upload_lessons_rejects_bad_rows():
    """Rows with an invalid category are rejected with per-row reasons."""
    admin = _admin_email()
    csv_text = (
        "title,description,expected_gesture,category,difficulty,module_id\n"
        f"Bad Category Lesson,desc,A,NotACategory,easy,{uuid.uuid4()}\n"
    )

    res = client.post(
        "/api/admin/bulk-upload-lessons",
        params={"admin_email": admin},
        files={"file": ("lessons.csv", csv_text, "text/csv")},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["rows_inserted"] == 0
    assert body["rows_rejected"] == 1
    assert "category" in body["rejected_rows"][0]["reason"].lower()


def test_bulk_upload_lessons_requires_valid_header():
    """A CSV missing a required column returns 400."""
    admin = _admin_email()
    csv_text = (
        "title,description,expected_gesture,category,difficulty\n"
        f"Missing module_id,'desc','A','alphabet','easy'\n"
    )

    res = client.post(
        "/api/admin/bulk-upload-lessons",
        params={"admin_email": admin},
        files={"file": ("bad.csv", csv_text, "text/csv")},
    )
    assert res.status_code == 400, res.text
    assert "missing required column" in res.json()["detail"]
