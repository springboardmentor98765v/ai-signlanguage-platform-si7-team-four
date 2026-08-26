"""
Milestone 4 - Day 3 (Intern 2, Backend): Full API Pass.

Calls every endpoint from the live OpenAPI inventory (50 paths / 65 operations)
with valid input and asserts:
  * the HTTP status is the documented success status,
  * the response body is parseable JSON,
  * the top-level keys match the documented shape (see docs/api_reference.md),
  * every error path returns the standard FastAPI error body {"detail": ...}.

Groups mirror the router tags used in the OpenAPI / Swagger UI. Uses the shared
conftest temp-DB + module-level TestClient(app) pattern.
"""

import base64
import os
import uuid
from datetime import datetime

import httpx
import pytest

from fastapi.testclient import TestClient

from app.db import database
from app.main import app
from app.models import models

client = TestClient(app)

PASSWORD = "SecurePassword123!"
LESSON_ID = "les_alphabet_a"
MODULE_ID = "mod_alphabet_101"


def _register(role="Learner"):
    """Register a unique user and return (user_id, email)."""
    key = f"{role.lower().replace(' ', '_')}_{uuid.uuid4().hex[:10]}"
    payload = {
        "username": f"fullpass_{key}"[:80],
        "email": f"fullpass_{key}@example.com",
        "password": PASSWORD,
        "role": role,
    }
    if role == "Admin":
        # Admin accounts are seeded by the platform, never self-registered.
        from conftest import make_user
        user = make_user(payload["email"], username=payload["username"], role="Admin")
        return user["id"], user["email"]
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 201, res.text
    body = res.json()
    assert body.get("user_id"), body
    return body["user_id"], payload["email"]


def _login(email):
    res = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert res.status_code == 200, res.text
    body = res.json()
    assert body.get("access_token"), body
    return body["access_token"]


def _bearer(token):
    return {"Authorization": f"Bearer {token}"}


def _register_and_token(role="Learner"):
    user_id, email = _register(role)
    return user_id, _login(email)


def _db():
    return database.SessionLocal()


# ==============================================================================
# System Health
# ==============================================================================

def test_system_health_endpoints():
    root = client.get("/")
    assert root.status_code == 200
    assert "message" in root.json()
    assert "milestone_tracker" in root.json()

    health = client.get("/health")
    assert health.status_code == 200
    body = health.json()
    assert body["status"] == "healthy"
    assert "api_status" in body
    assert "milestone_tracker" in body


# ==============================================================================
# Authentication (register / login / refresh / dashboards / forgot-password)
# ==============================================================================

def test_auth_lifecycle():
    learner_id, learner_email = _register("Learner")
    learner_token = _login(learner_email)

    # Learner dashboard (RBAC: Learner/Admin)
    res = client.get("/api/auth/dashboard/learner", headers=_bearer(learner_token))
    assert res.status_code == 200
    body = res.json()
    assert "message" in body
    assert "accuracy_metric" in body
    assert "lessons_completed" in body

    # Learner token must NOT open the instructor dashboard -> 403 + {"detail": ...}
    denied = client.get("/api/auth/dashboard/instructor", headers=_bearer(learner_token))
    assert denied.status_code == 403
    assert "detail" in denied.json()

    # Instructor dashboard (RBAC: Instructor/Admin)
    _, instructor_token = _register_and_token("Instructor")
    res = client.get("/api/auth/dashboard/instructor", headers=_bearer(instructor_token))
    assert res.status_code == 200
    assert "class_performance_average" in res.json()

    # No token -> 401 + {"detail": ...}
    no_token = client.get("/api/auth/dashboard/learner")
    assert no_token.status_code in (401, 403)
    assert "detail" in no_token.json()

    # Refresh token
    login = client.post(
        "/api/auth/login", json={"email": learner_email, "password": PASSWORD}
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    refresh = client.post(
        "/api/auth/refresh-token",
        json={"refresh_token": login.json()["refresh_token"]},
    )
    assert refresh.status_code == 200
    assert "access_token" in refresh.json()
    assert "token_type" in refresh.json()

    # Forgot password (registered email) -> 200
    forgot = client.post("/api/auth/forgot-password", json={"email": learner_email})
    assert forgot.status_code == 200
    assert "message" in forgot.json()

    # Forgot password (unknown email) -> 404 + {"detail": ...}
    unknown = client.post(
        "/api/auth/forgot-password",
        json={"email": f"nobody_{uuid.uuid4().hex[:8]}@example.com"},
    )
    assert unknown.status_code == 404
    assert "detail" in unknown.json()

    assert isinstance(learner_id, str) and len(learner_id) == 36
    assert isinstance(headers, dict)


# ==============================================================================
# Day 2 Milestone 2: Profile update / change password
# (operate on the first user row by design of M2; assert documented shape)
# ==============================================================================

def test_profile_update_and_password():
    _, email = _register("Learner")
    token = _login(email)
    headers = _bearer(token)

    update = client.patch("/api/users/me", json={"username": "fullpass_updated_user"}, headers=headers)
    assert update.status_code == 200
    body = update.json()
    assert "message" in body
    assert "username" in body
    assert "email" in body

    pw = client.post(
        "/api/users/change-password",
        json={"current_password": PASSWORD, "new_password": "NewSecurePassword456!"},
        headers=headers,
    )
    assert pw.status_code == 200
    assert "message" in pw.json()


# ==============================================================================
# Lessons Service (catalog, CRUD with Instructor/Admin RBAC, CSV bulk upload)
# ==============================================================================

def test_lessons_service():
    # List lessons (paginated)
    res = client.get("/api/lessons")
    assert res.status_code == 200
    body = res.json()
    assert body["skip"] == 0 and body["limit"] == 10
    assert body["total"] > 0
    assert isinstance(body["data"], list) and body["data"]

    # Advanced lessons
    adv = client.get("/api/lessons/advanced")
    assert adv.status_code == 200
    assert "advanced_lessons" in adv.json()
    assert "count" in adv.json()

    # Get lesson by id (use a real DB-backed lesson id)
    real_lesson_id = body["data"][0]["lesson_id"]
    one = client.get(f"/api/lessons/{real_lesson_id}")
    assert one.status_code == 200
    assert one.json()["lesson_id"] == real_lesson_id
    assert one.json()["expected_gesture"]

    # Unknown lesson -> 404 + {"detail": ...}
    missing = client.get("/api/lessons/les_does_not_exist")
    assert missing.status_code == 404
    assert "detail" in missing.json()

    # RBAC CRUD: Learner token rejected on create -> 403
    _, learner_token = _register_and_token("Learner")
    _, instructor_token = _register_and_token("Instructor")
    create_payload = {
        "module_id": MODULE_ID,
        "title": "RBAC Lesson A",
        "content_description": "Learner must be denied here.",
        "expected_gesture": "A",
        "category": "alphabet",
        "difficulty": "easy",
    }
    denied = client.post("/api/lessons", json=create_payload, headers=_bearer(learner_token))
    assert denied.status_code == 403
    assert "detail" in denied.json()

    # Instructor token can create / update / delete
    created = client.post("/api/lessons", json=create_payload, headers=_bearer(instructor_token))
    assert created.status_code == 201
    new_id = created.json()["lesson_id"]

    updated = client.put(
        f"/api/lessons/{new_id}", json=create_payload, headers=_bearer(instructor_token)
    )
    assert updated.status_code == 200
    assert updated.json()["title"] == create_payload["title"]

    deleted = client.delete(f"/api/lessons/{new_id}", headers=_bearer(instructor_token))
    assert deleted.status_code == 200
    assert "message" in deleted.json()

    # Bulk upload CSV (string payload) — Instructor only.
    csv_content = (
        "module_id,title,content_description,expected_gesture,category,difficulty\n"
        f"{MODULE_ID},Bulk Letter Z,CSV seeded lesson.,Z,alphabet,easy\n"
    )
    bulk = client.post(
        "/api/lessons/bulk-upload-csv",
        json={"csv_content": csv_content},
        headers=_bearer(instructor_token),
    )
    assert bulk.status_code == 201
    bbody = bulk.json()
    assert bbody["created_count"] == 1
    assert bbody["errors"] == []

    # No token -> 401
    no_auth = client.post("/api/lessons", json=create_payload)
    assert no_auth.status_code in (401, 403)
    assert "detail" in no_auth.json()


# ==============================================================================
# Course Service
# ==============================================================================

def test_courses_service():
    modules = client.get("/api/courses/modules")
    assert modules.status_code == 200
    assert len(modules.json()) > 0
    assert "course_id" in modules.json()[0]

    lessons = client.get(f"/api/courses/modules/{modules.json()[0]['module_id']}/lessons")
    assert lessons.status_code == 200
    assert len(lessons.json()) > 0
    assert "lesson_id" in lessons.json()[0]

    unknown = client.get("/api/courses/modules/mod_missing/lessons")
    assert unknown.status_code == 404
    assert "detail" in unknown.json()

    # Create module: Learner denied, Instructor granted
    _, learner_token = _register_and_token("Learner")
    _, instructor_token = _register_and_token("Instructor")
    payload = {
        "title": "Custom Module",
        "description": "Module created via full API pass.",
        "course_id": str(uuid.uuid4())[:36],
    }
    denied = client.post("/api/courses/modules", json=payload, headers=_bearer(learner_token))
    assert denied.status_code == 403
    assert "detail" in denied.json()

    created = client.post("/api/courses/modules", json=payload, headers=_bearer(instructor_token))
    assert created.status_code == 201
    assert created.json()["title"] == payload["title"]
    assert created.json()["lessons"] == []
    assert created.json()["module_id"] == created.json()["course_id"]

    # The newly created module must be listable again (no KeyError)
    after = client.get("/api/courses/modules")
    assert after.status_code == 200
    assert any(m.get("module_id") for m in after.json())


# ==============================================================================
# Admin Management (email-keyed RBAC, verified against the users table)
# ==============================================================================

def test_admin_endpoints():
    admin_id, admin_email = _register("Admin")
    victim_id, victim_email = _register("Learner")
    spare_id, _ = _register("Learner")

    # List all users
    users = client.get("/api/admin/users", params={"admin_email": admin_email})
    assert users.status_code == 200
    assert any(u["email"] == admin_email for u in users.json())

    # Single status / role updates
    st = client.patch(
        "/api/admin/user-status",
        json={"target_email": victim_email, "is_active": False},
        params={"admin_email": admin_email},
    )
    assert st.status_code == 200
    assert "message" in st.json()

    role = client.patch(
        "/api/admin/user-role",
        json={"target_email": victim_email, "new_role": "Instructor"},
        params={"admin_email": admin_email},
    )
    assert role.status_code == 200
    assert "message" in role.json()

    # Bulk actions
    bulk_delete = client.post(
        "/api/admin/users/bulk-delete",
        json={"user_ids": [spare_id]},
        params={"admin_email": admin_email},
    )
    assert bulk_delete.status_code == 200
    assert bulk_delete.json()["deleted_count"] == 1

    bulk_status = client.patch(
        "/api/admin/users/bulk-status",
        json={"user_ids": [victim_id], "is_active": True},
        params={"admin_email": admin_email},
    )
    assert bulk_status.status_code == 200
    assert bulk_status.json()["updated_count"] == 1

    bulk_role = client.patch(
        "/api/admin/users/bulk-role",
        json={"user_ids": [victim_id], "new_role": "Learner"},
        params={"admin_email": admin_email},
    )
    assert bulk_role.status_code == 200
    assert bulk_role.json()["updated_count"] == 1

    # Day-4 bulk-user-status
    bst = client.post(
        "/api/admin/bulk-user-status",
        json={"user_ids": [victim_id, victim_email], "is_active": False},
        params={"admin_email": admin_email},
    )
    assert bst.status_code == 200
    bst_body = bst.json()
    assert "updated_count" in bst_body
    assert "not_found" in bst_body

    # Bulk-upload lessons CSV (multipart)
    csv_bytes = (
        "title,description,expected_gesture,category,difficulty,module_id\n"
        "Admin CSV Sign,Bulk admin upload.,SIGN,words,medium," + str(uuid.uuid4()) + "\n"
    ).encode("utf-8")
    upload = client.post(
        "/api/admin/bulk-upload-lessons",
        params={"admin_email": admin_email},
        files={"file": ("lessons.csv", csv_bytes, "text/csv")},
    )
    assert upload.status_code == 200
    up_body = upload.json()
    assert up_body["rows_inserted"] == 1
    assert up_body["rows_rejected"] == 0

    # Non-admin email -> 403 + {"detail": ...}
    denied = client.get("/api/admin/users", params={"admin_email": victim_email})
    assert denied.status_code == 403
    assert "detail" in denied.json()

    # Delete a single user (DELETE /users/{user_id})
    rm = client.delete(
        f"/api/admin/users/{victim_id}", params={"admin_email": admin_email}
    )
    assert rm.status_code == 200
    assert "message" in rm.json()


# ==============================================================================
# Instructor-Student Management
# ==============================================================================

def test_instructor_student_management():
    _, instructor_email = _register("Instructor")
    _, student_email = _register("Learner")

    instructor_token = _login(instructor_email)

    assign = client.post(
        "/api/instructor/assign-student",
        headers=_bearer(instructor_token),
        json={"instructor_email": instructor_email, "student_email": student_email},
    )
    assert assign.status_code == 200
    body = assign.json()
    assert "message" in body
    assert body["instructor"] and body["student"]

    students = client.get(
        f"/api/instructor/students/{instructor_email}", headers=_bearer(instructor_token)
    )
    assert students.status_code == 200
    sbody = students.json()
    assert sbody["total_students"] >= 1
    assert any(s["email"] == student_email for s in sbody["students"])

    # Unknown instructor -> 404 + {"detail": ...}
    unknown = client.post(
        "/api/instructor/assign-student",
        headers=_bearer(instructor_token),
        json={"instructor_email": f"unknown_{uuid.uuid4().hex[:6]}@example.com",
              "student_email": student_email},
    )
    assert unknown.status_code == 404
    assert "detail" in unknown.json()


# ==============================================================================
# Notifications
# ==============================================================================

def test_notifications_service():
    user_id, _ = _register("Learner")

    created = client.post(
        "/api/notifications",
        json={
            "user_id": user_id,
            "title": "Full API Pass Notice",
            "message": "Milestone 4 Day 3 notification check.",
            "event_type": "info",
        },
    )
    assert created.status_code in (200, 201)
    notif = created.json()
    assert notif["id"]
    assert notif["user_id"] == user_id
    assert "created_at" in notif

    listing = client.get(f"/api/notifications/{user_id}")
    assert listing.status_code == 200
    assert any(n["id"] == notif["id"] for n in listing.json())

    read = client.patch(f"/api/notifications/{notif['id']}/read")
    assert read.status_code == 200
    assert read.json()["is_read"] is True


# ==============================================================================
# Practice Service (start / submit -> AI relay mocked / end)
# ==============================================================================

class _FakeAIResponse:
    def __init__(self):
        self.status_code = 200

    def json(self):
        return {
            "predicted_sign": "A",
            "confidence": 0.94,
            "hand_detected": True,
            "correct": True,
            "possible_issue": None,
        }


@pytest.fixture(autouse=False)
def _mock_ai_service(monkeypatch):
    def _fake_post(url, files=None, data=None, timeout=None):
        return _FakeAIResponse()

    monkeypatch.setattr(httpx, "post", _fake_post)


def test_practice_flow(_mock_ai_service):
    user_id, _ = _register("Learner")

    started = client.post(
        "/api/practice/start",
        params={"user_id": user_id, "lesson_id": LESSON_ID},
    )
    assert started.status_code == 200
    sbody = started.json()
    assert sbody["status"] == "in_progress"
    session_id = sbody["session_id"]

    tiny_png = base64.b64encode(b"\x89PNG\r\n\x1a\nbinary").decode()
    image_data = f"data:image/png;base64,{tiny_png}"
    submitted = client.post(
        "/api/practice/submit",
        json={"session_id": session_id, "image_data": image_data, "target_letter": "A"},
    )
    assert submitted.status_code == 200
    pbody = submitted.json()
    assert pbody["status"] == "success"
    assert pbody["session_id"] == session_id
    assert pbody["hand_detected"] is True

    # Auto-start submit path (no session_id): backend creates a session
    auto = client.post(
        "/api/practice/submit",
        json={"user_id": user_id, "lesson_id": 1, "image_data": image_data},
    )
    assert auto.status_code == 200
    assert auto.json()["session_id"]

    ended = client.post("/api/practice/end", params={"session_id": session_id})
    assert ended.status_code == 200
    ebody = ended.json()
    assert ebody["status"] == "completed"
    assert ebody["duration_seconds"] >= 0

    # Ending an unknown session -> 404 + {"detail": ...}
    unknown = client.post(
        "/api/practice/end",
        params={"session_id": str(uuid.uuid4())},
    )
    assert unknown.status_code == 404
    assert "detail" in unknown.json()


def test_practice_submit_invalid_image():
    """Malformed image_data -> 400 + {"detail": ...}, no AI call."""
    user_id, _ = _register("Learner")
    bad = client.post(
        "/api/practice/submit",
        json={"user_id": user_id, "lesson_id": LESSON_ID, "image_data": "not-base64"},
    )
    assert bad.status_code == 400
    assert "detail" in bad.json()


def test_practice_numeric_looking_lesson_id_is_stable():
    """Digit-only UUID strings must not crash the practice tables on SQLite.

    Regression: a valid UUID made of only digits (e.g. 11111111-...-1111) was
    stored as a FLOAT by SQLite's NUMERIC column affinity, so reading the row
    back crashed with `AttributeError: 'float' object has no attribute 'replace'`.
    The tables now store ids as String(36) (same pattern as notifications).
    """
    user_id, _ = _register("Learner")
    numeric_uuid = "11111111-1111-1111-1111-111111111111"

    started = client.post(
        "/api/practice/start",
        params={"user_id": user_id, "lesson_id": numeric_uuid},
    )
    assert started.status_code == 200, started.text
    session_id = started.json()["session_id"]
    assert started.json()["lesson_id"] == numeric_uuid

    # Reading the row back (start and end both SELECT it) must not crash.
    ended = client.post("/api/practice/end", params={"session_id": session_id})
    assert ended.status_code == 200, ended.text
    assert ended.json()["status"] == "completed"


# ==============================================================================
# Accessibility Trainer (role-gated endpoints)
# ==============================================================================

def _seed_trainer_data(learner_id):
    """Give the learner practice/assessment/certificate rows so metrics are real."""
    db = _db()
    lesson_uuid = str(uuid.uuid4())
    sess = models.PracticeSession(
        user_id=learner_id,
        lesson_id=lesson_uuid,
        status="completed",
        attempt_count=4,
        duration_seconds=180.0,
        started_at=datetime.utcnow(),
        ended_at=datetime.utcnow(),
    )
    db.add(sess)
    db.commit()
    db.refresh(sess)

    for sign, acc, conf, correct in (("A", 85.0, 0.9, True), ("B", 70.0, 0.8, False)):
        db.add(
            models.Assessment(
                session_id=sess.id,
                expected_sign=sign,
                overall_accuracy=acc,
                confidence=conf,
                is_correct=correct,
                created_at=datetime.utcnow(),
            )
        )
    db.add(
        models.Certificate(
            user_id=learner_id,
            issued_date=datetime.utcnow(),
            overall_score=85.0,
        )
    )
    db.commit()
    db.close()


def test_trainer_endpoints():
    trainer_id, trainer_email = _register("Accessibility Trainer")
    trainer_token = _login(trainer_email)
    learner_id, _ = _register("Learner")

    headers = _bearer(trainer_token)

    # Assign the learner
    assigned = client.post(
        "/api/trainer/assign-learner",
        json={"learner_id": learner_id},
        headers=headers,
    )
    assert assigned.status_code == 200
    assert assigned.json()["learner_id"] == learner_id

    # List assigned learners
    listing = client.get("/api/trainer/learners", headers=headers)
    assert listing.status_code == 200
    assert any(l["learner_id"] == learner_id for l in listing.json())

    # Seed business data, then verify every metric endpoint shape
    _seed_trainer_data(learner_id)

    eng = client.get(f"/api/trainer/learners/{learner_id}/engagement", headers=headers)
    assert eng.status_code == 200
    ebody = eng.json()
    for key in ("learner_id", "engagement_score", "sessions_total", "sessions_completed",
                "total_attempts", "total_practice_minutes", "formula_owner"):
        assert key in ebody
    assert ebody["sessions_total"] >= 1

    skill = client.get(f"/api/trainer/learners/{learner_id}/skill-development", headers=headers)
    assert skill.status_code == 200
    sbody = skill.json()
    for key in ("learner_id", "improvement_rate", "trend", "weak_letters", "formula_owner"):
        assert key in sbody

    anal = client.get(f"/api/trainer/learners/{learner_id}/assessment-analytics", headers=headers)
    assert anal.status_code == 200
    abody = anal.json()
    for key in ("learner_id", "total_assessments", "average_accuracy", "average_confidence",
                "correct_count", "correct_percentage", "per_letter", "formula_owner"):
        assert key in abody
    assert abody["total_assessments"] >= 1

    cert = client.get(f"/api/trainer/learners/{learner_id}/certification-status", headers=headers)
    assert cert.status_code == 200
    cbody = cert.json()
    for key in ("learner_id", "status", "level", "overall_score", "certificate_issued_date",
                "formula_owner"):
        assert key in cbody

    # RBAC: a Learner token is denied all trainer endpoints -> 403
    _, learner_token = _register_and_token("Learner")
    lheaders = _bearer(learner_token)
    denied = client.get("/api/trainer/learners", headers=lheaders)
    assert denied.status_code == 403
    assert "detail" in denied.json()

    # Another trainer who never assigned this learner -> 403
    _, other_trainer_email = _register("Accessibility Trainer")
    other_headers = _bearer(_login(other_trainer_email))
    unassigned = client.get(
        f"/api/trainer/learners/{learner_id}/engagement", headers=other_headers
    )
    assert unassigned.status_code == 403
    assert "detail" in unassigned.json()

    # Unknown learner id -> 404
    ghost = str(uuid.uuid4())
    missing = client.get(f"/api/trainer/learners/{ghost}/engagement", headers=headers)
    assert missing.status_code == 404
    assert "detail" in missing.json()


# ==============================================================================
# v1 Community Feedback
# ==============================================================================

def test_v1_feedback_service():
    submitted = client.post(
        "/api/v1/feedback/submit",
        json={
            "user_id": 9001,
            "category": "General",
            "rating": 5,
            "comments": "Full API pass feedback.",
        },
    )
    assert submitted.status_code == 201
    body = submitted.json()
    for key in ("id", "user_id", "category", "rating", "comments", "submitted_at"):
        assert key in body

    listing = client.get("/api/v1/feedback/all")
    assert listing.status_code == 200
    assert len(listing.json()) >= 1


# ==============================================================================
# v1 Translation History & Logs
# ==============================================================================

def test_v1_translations_service():
    logged = client.post(
        "/api/v1/translations/log",
        json={
            "user_id": 9002,
            "translated_text": "Hello welcome",
            "confidence_level": 0.95,
        },
    )
    assert logged.status_code == 200
    body = logged.json()
    for key in ("id", "user_id", "translated_text", "confidence_level", "timestamp"):
        assert key in body

    history = client.get("/api/v1/translations/history/9002")
    assert history.status_code == 200
    assert len(history.json()) >= 1


# ==============================================================================
# v1 Progress & Analytics
# ==============================================================================

def test_v1_progress_service():
    updated = client.post(
        "/api/v1/progress/update",
        json={
            "user_id": 9003,
            "course_id": 101,
            "completed_lessons": 8,
            "total_lessons": 10,
            "accuracy_score": 91.5,
        },
    )
    assert updated.status_code == 200
    body = updated.json()
    for key in ("id", "user_id", "course_id", "completed_lessons", "total_lessons",
                "accuracy_score", "last_updated"):
        assert key in body

    listing = client.get("/api/v1/progress/user/9003")
    assert listing.status_code == 200
    assert len(listing.json()) >= 1


# ==============================================================================
# v1 Sign Dictionary & Vocabulary
# ==============================================================================

def test_v1_dictionary_service():
    signs = client.get("/api/v1/dictionary/signs")
    assert signs.status_code == 200
    assert len(signs.json()) >= 1
    first = signs.json()[0]
    assert "sign_name" in first

    searched = client.get("/api/v1/dictionary/signs", params={"search": "Hello"})
    assert searched.status_code == 200
    assert len(searched.json()) >= 1

    one = client.get(f"/api/v1/dictionary/signs/{first['id']}")
    assert one.status_code == 200
    assert one.json()["id"] == first["id"]

    missing = client.get("/api/v1/dictionary/signs/99999")
    assert missing.status_code == 404
    assert "detail" in missing.json()


# ==============================================================================
# v1 Day 3 Core Features (gesture eval + upload)
# ==============================================================================

def test_v1_gesture_service():
    evaluated = client.post(
        "/api/v1/day3/evaluate-sign",
        json={"sign_text": "HELLO", "user_id": 101},
    )
    assert evaluated.status_code == 200
    body = evaluated.json()
    for key in ("success", "confidence_score", "matched_sign", "message"):
        assert key in body
    assert body["success"] is True

    filename = f"fullpass_{uuid.uuid4().hex[:8]}.png"
    uploaded = client.post(
        "/api/v1/day3/upload-gesture-frame",
        files={"file": (filename, b"fake-image-bytes", "image/png")},
    )
    assert uploaded.status_code == 200
    ubody = uploaded.json()
    assert ubody["filename"] == filename
    assert "status" in ubody
    assert "saved_path" in ubody
    saved = ubody["saved_path"]
    if os.path.exists(saved):
        os.remove(saved)


# ==============================================================================
# Team Integration Testing
# ==============================================================================

def test_integration_test_sync():
    # snake_case input (the platform-wide convention)
    sync = client.post(
        "/api/integration/test-sync",
        json={"user_id": "user-1", "action_type": "translate", "confidence_score": 0.9},
    )
    assert sync.status_code == 200
    body = sync.json()
    assert body["status"] == "success"
    received = body["received_data"]
    # Response must be snake_case, matching every other endpoint
    assert "user_id" in received
    assert "action_type" in received
    assert "confidence_score" in received

    # camelCase aliases must still be accepted
    aliased = client.post(
        "/api/integration/test-sync",
        json={"userId": "user-2", "actionType": "translate", "confidenceScore": 0.8},
    )
    assert aliased.status_code == 200
    assert aliased.json()["received_data"]["user_id"] == "user-2"