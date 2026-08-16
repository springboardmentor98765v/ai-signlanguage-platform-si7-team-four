"""
Milestone 4 Day 7: final acceptance walkthrough — "the whole team".

Registers every actor the platform knows (Learner, Instructor, Accessibility
Trainer, Admin) and walks each role through its KEY endpoints end to end, the
same way the four interns would exercise them together:

    Learner    -> register, login, learner dashboard, lessons, practice
                  start/end, notifications (create/list/read)
    Instructor -> register, login, instructor dashboard, create lesson,
                  assign student, list students
    Trainer    -> register, login, assign learner, list assigned learners,
                  engagement / skill-development / assessment-analytics /
                  certification-status, plus a 403 for an unassigned learner
    Admin      -> register, login, list users, deactivate + reactivate a
                  user (and confirm login is blocked while deactivated),
                  change a user's role

Run against a live deployment (same one-command style as test_smoke_live.py):

    BACKEND_BASE_URL=https://<live-url> python3 -m pytest test_acceptance_walkthrough.py -q

Without BACKEND_BASE_URL it runs in-process via TestClient (suite stays green
with no server running).
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
    safe = "".join(ch if ch.isalnum() else "_" for ch in prefix)
    return f"{safe}_{uuid.uuid4().hex[:12]}"


def _register(role):
    email = f"{_uid(role)}@example.com"
    res = client.post(
        "/api/auth/register",
        json={
            "username": f"{role}_{uuid.uuid4().hex[:8]}",
            "email": email,
            "password": PASSWORD,
            "role": role,
        },
    )
    assert res.status_code == 201, res.text
    return email, res.json()["user_id"]


def _login(email):
    res = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _auth(token):
    return {"Authorization": f"Bearer {token}"}


def test_team_role_walkthrough_end_to_end():
    # --- LEARNER -------------------------------------------------------------
    learner_email, learner_id = _register("Learner")
    learner_token = _login(learner_email)

    dash = client.get("/api/auth/dashboard/learner", headers=_auth(learner_token))
    assert dash.status_code == 200, dash.text

    lessons = client.get("/api/lessons", params={"limit": 3})
    assert lessons.status_code == 200, lessons.text
    assert len(lessons.json()["data"]) >= 1

    practice = client.post(
        "/api/practice/start",
        params={"user_id": learner_id, "lesson_id": "11111111-1111-1111-1111-111111111111"},
    )
    assert practice.status_code == 200, practice.text
    session_id = practice.json()["session_id"]
    assert practice.json()["status"] == "in_progress"
    assert client.post("/api/practice/end", params={"session_id": session_id}).status_code == 200

    notif = client.post(
        "/api/notifications",
        json={
            "user_id": learner_id,
            "title": "Acceptance walkthrough",
            "message": "All systems nominal.",
            "event_type": "badge_earned",
        },
    )
    assert notif.status_code == 201, notif.text
    notif_id = notif.json()["id"]
    listed = client.get(f"/api/notifications/{learner_id}")
    assert listed.status_code == 200 and any(n["id"] == notif_id for n in listed.json())
    assert client.patch(f"/api/notifications/{notif_id}/read").json()["is_read"] is True

    # Learner must NOT reach the instructor dashboard (RBAC).
    assert client.get("/api/auth/dashboard/instructor", headers=_auth(learner_token)).status_code == 403

    # --- INSTRUCTOR ----------------------------------------------------------
    instructor_email, _instructor_id = _register("Instructor")
    instructor_token = _login(instructor_email)

    assert client.get("/api/auth/dashboard/instructor", headers=_auth(instructor_token)).status_code == 200

    lesson = client.post(
        "/api/lessons",
        headers=_auth(instructor_token),
        json={
            "module_id": "acceptance_mod",
            "title": "Acceptance Lesson",
            "expected_gesture": "A",
        },
    )
    assert lesson.status_code == 201, lesson.text
    lesson_id = lesson.json()["lesson_id"]

    assign = client.post(
        "/api/instructor/assign-student",
        json={"instructor_email": instructor_email, "student_email": learner_email},
    )
    assert assign.status_code == 200, assign.text

    students = client.get(f"/api/instructor/students/{instructor_email}")
    assert students.status_code == 200 and students.json()["total_students"] >= 1
    assert any(s["email"] == learner_email for s in students.json()["students"])

    # --- ACCESSIBILITY TRAINER ----------------------------------------------
    trainer_email, trainer_id = _register("Accessibility Trainer")
    trainer_token = _login(trainer_email)

    assert client.get("/api/trainer/learners", headers=_auth(trainer_token)).json() == []

    assigned = client.post(
        "/api/trainer/assign-learner",
        headers=_auth(trainer_token),
        json={"learner_email": learner_email},
    )
    assert assigned.status_code == 200, assigned.text

    mine = client.get("/api/trainer/learners", headers=_auth(trainer_token))
    assert mine.status_code == 200
    assert any(l["learner_id"] == learner_id for l in mine.json())

    for metric in ("engagement", "skill-development", "assessment-analytics", "certification-status"):
        res = client.get(f"/api/trainer/learners/{learner_id}/{metric}", headers=_auth(trainer_token))
        assert res.status_code == 200, f"{metric}: {res.text}"

    # Trainer cannot inspect an unassigned learner (403).
    _other_email, other_id = _register("Learner")
    unassigned = client.get(
        f"/api/trainer/learners/{other_id}/engagement", headers=_auth(trainer_token)
    )
    assert unassigned.status_code == 403

    # --- ADMIN ---------------------------------------------------------------
    admin_email, _admin_id = _register("Admin")
    admin_token = _login(admin_email)

    users = client.get("/api/admin/users", params={"admin_email": admin_email})
    assert users.status_code == 200
    assert any(u["email"] == trainer_email for u in users.json())

    deact = client.patch(
        "/api/admin/user-status",
        params={"admin_email": admin_email},
        json={"target_email": learner_email, "is_active": False},
    )
    assert deact.status_code == 200, deact.text
    assert client.post("/api/auth/login", json={"email": learner_email, "password": PASSWORD}).status_code == 403

    react = client.patch(
        "/api/admin/user-status",
        params={"admin_email": admin_email},
        json={"target_email": learner_email, "is_active": True},
    )
    assert react.status_code == 200
    assert client.post("/api/auth/login", json={"email": learner_email, "password": PASSWORD}).status_code == 200

    # Promote a Learner to Instructor -> the new role takes effect on login.
    client.patch(
        "/api/admin/user-role",
        params={"admin_email": admin_email},
        json={"target_email": _other_email, "new_role": "Instructor"},
    )
    promoted_token = _login(_other_email)
    created = client.post(
        "/api/lessons",
        headers=_auth(promoted_token),
        json={"module_id": "acceptance_mod2", "title": "Promoted Lesson", "expected_gesture": "B"},
    )
    assert created.status_code == 201, created.text

    # Role change is also reflected in the admin user listing.
    roles = {u["email"]: u.get("role") for u in client.get(
        "/api/admin/users", params={"admin_email": admin_email}
    ).json()}
    assert roles.get(_other_email) == "Instructor"

    # Instructor cleanup check is intentionally absent - lesson_id is kept for
    # the demo; delete path is already covered by the unit suite.
