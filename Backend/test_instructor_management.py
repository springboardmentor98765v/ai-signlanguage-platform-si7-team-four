"""
Milestone 3 Day 10: Instructor-Student Management regression tests.

Day-10 final integration pass found that `User` had no `instructor_id` column:
  - assign-student silently did not persist the assignment (200 but no-op), and
  - GET /api/instructor/students/{instructor_email} raised
    AttributeError -> HTTP 500.

Fixed by adding the column to the model plus an idempotent SQLite migration in
app/main.py. These tests lock in the behavior.
"""

import uuid

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

PASSWORD = "SecurePassword123!"


def _register_user(role: str = "Learner") -> dict:
    email = f"instr_{uuid.uuid4().hex}@example.com"
    res = client.post("/api/auth/register", json={
        "username": f"instr_{uuid.uuid4().hex[:8]}",
        "email": email,
        "password": PASSWORD,
        "role": role,
    })
    assert res.status_code == 201, res.text
    return {"user_id": res.json()["user_id"], "email": email}


def _register_user_with_email(role: str, email: str) -> dict:
    res = client.post("/api/auth/register", json={
        "username": f"instr_{uuid.uuid4().hex[:8]}",
        "email": email,
        "password": PASSWORD,
        "role": role,
    })
    assert res.status_code == 201, res.text
    return res.json()


def _auth(email: str) -> dict:
    """Log in and return an Authorization header for the given email."""
    res = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['access_token']}"}


def test_assign_student_persists_and_is_listed():
    """assign-student persists the instructor link so the students list returns it."""
    instructor = _register_user("Instructor")
    student = _register_user("Learner")

    assign = client.post(
        "/api/instructor/assign-student",
        headers=_auth(instructor["email"]),
        json={"instructor_email": instructor["email"], "student_email": student["email"]},
    )
    assert assign.status_code == 200, assign.text

    listed = client.get(
        f"/api/instructor/students/{instructor['email']}",
        headers=_auth(instructor["email"]),
    )
    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert body["total_students"] == 1
    assert body["students"][0]["student_id"] == student["user_id"]
    assert body["students"][0]["email"] == student["email"]


def test_get_instructor_students_empty_for_unassigned():
    """A fresh instructor with no assigned students returns an empty list, not an error."""
    instructor = _register_user("Instructor")

    listed = client.get(
        f"/api/instructor/students/{instructor['email']}",
        headers=_auth(instructor["email"]),
    )
    assert listed.status_code == 200, listed.text
    assert listed.json()["total_students"] == 0


def test_assign_student_unknown_instructor_404():
    """Assigning to a non-existent instructor returns 404."""
    student = _register_user("Learner")
    instructor = _register_user("Instructor")
    res = client.post(
        "/api/instructor/assign-student",
        headers=_auth(instructor["email"]),
        json={"instructor_email": f"nobody_{uuid.uuid4().hex}@example.com", "student_email": student["email"]},
    )
    assert res.status_code == 404, res.text
