"""
Milestone 4 - Day 2: Accessibility Trainer APIs.

Covers the three Day-2 checkpoints:
  1. "Get my assigned learners" API works for the Trainer role.
  2. Engagement / skill-development / assessment-analytics / certification-status
     APIs return real derived data.
  3. Every /api/trainer endpoint is restricted to the Accessibility Trainer role.
"""
import datetime as dt
import uuid

from fastapi.testclient import TestClient

from app.db.database import SessionLocal
from app.main import app
from app.models.models import Assessment, Certificate, PracticeSession, new_id

client = TestClient(app)
PASSWORD = "SecurePassword123!"


def _register(role, prefix="m4"):
    email = f"{prefix}_{uuid.uuid4().hex[:10]}@example.com"
    res = client.post(
        "/api/auth/register",
        json={"username": f"{prefix}_{uuid.uuid4().hex[:6]}", "email": email, "password": PASSWORD, "role": role},
    )
    assert res.status_code == 201, res.text
    return email, res.json()["user_id"]


def _login(email):
    res = client.post("/api/auth/login", json={"email": email, "password": PASSWORD})
    assert res.status_code == 200, res.text
    return res.json()["access_token"]


def _seed_learner_progress(learner_id):
    """Seed practice sessions + assessments + a certificate so APIs return REAL numbers."""
    db = SessionLocal()
    now = dt.datetime.utcnow()
    for status, attempts, dur, started in [
        ("completed", 3, 120.0, now - dt.timedelta(days=6)),
        ("completed", 4, 150.0, now - dt.timedelta(days=3)),
        ("in_progress", 1, 45.0, now - dt.timedelta(hours=1)),
    ]:
        s = PracticeSession(
            user_id=learner_id,
            lesson_id=new_id(),
            status=status,
            attempt_count=attempts,
            duration_seconds=dur,
            started_at=started,
            ended_at=now if status == "completed" else None,
        )
        db.add(s)
        db.flush()
        for letter, acc, conf, ok in [("A", 92, 0.95, True), ("B", 64, 0.70, False)]:
            db.add(
                Assessment(
                    session_id=s.id,
                    expected_sign=letter,
                    predicted_sign="A",
                    confidence=conf,
                    overall_accuracy=acc,
                    is_correct=ok,
                    created_at=started,
                )
            )
    db.add(
        Certificate(
            user_id=learner_id,
            issued_date=now - dt.timedelta(days=2),
            overall_score=85.0,
            pdf_url="/certs/trainer_test.pdf",
        )
    )
    db.commit()
    db.close()


def test_register_accepts_accessibility_trainer_role():
    email, user_id = _register("Accessibility Trainer")
    assert user_id


def test_trainer_lists_assigned_learners():
    trainer_email, _ = _register("Accessibility Trainer")
    learner_email, learner_id = _register("Learner")
    t_tok = _login(trainer_email)

    # learner token has no access yet
    l_tok = _login(learner_email)
    denied = client.get("/api/trainer/learners", headers={"Authorization": f"Bearer {l_tok}"})
    assert denied.status_code == 403

    res = client.post(
        "/api/trainer/assign-learner",
        json={"learner_email": learner_email},
        headers={"Authorization": f"Bearer {t_tok}"},
    )
    assert res.status_code == 200, res.text

    listed = client.get("/api/trainer/learners", headers={"Authorization": f"Bearer {t_tok}"})
    assert listed.status_code == 200
    ids = [l["learner_id"] for l in listed.json()]
    assert learner_id in ids


def test_trainer_endpoints_return_real_derived_data():
    trainer_email, _ = _register("Accessibility Trainer")
    learner_email, learner_id = _register("Learner")
    t_tok = _login(trainer_email)
    client.post(
        "/api/trainer/assign-learner",
        json={"learner_email": learner_email},
        headers={"Authorization": f"Bearer {t_tok}"},
    )
    _seed_learner_progress(learner_id)

    headers = {"Authorization": f"Bearer {t_tok}"}
    eng = client.get(f"/api/trainer/learners/{learner_id}/engagement", headers=headers)
    assert eng.status_code == 200
    assert eng.json()["sessions_total"] == 3
    assert eng.json()["total_attempts"] == 8

    skill = client.get(f"/api/trainer/learners/{learner_id}/skill-development", headers=headers)
    assert skill.status_code == 200
    assert skill.json()["trend"]

    an = client.get(f"/api/trainer/learners/{learner_id}/assessment-analytics", headers=headers)
    assert an.status_code == 200
    assert an.json()["total_assessments"] == 6
    assert an.json()["average_accuracy"] > 0

    cert = client.get(f"/api/trainer/learners/{learner_id}/certification-status", headers=headers)
    assert cert.status_code == 200
    assert cert.json()["status"] == "passed"
    assert cert.json()["overall_score"] == 85.0


def test_trainer_cannot_read_unassigned_learner():
    trainer_email, _ = _register("Accessibility Trainer")
    _, other_learner_id = _register("Learner")  # never assigned
    t_tok = _login(trainer_email)

    res = client.get(
        f"/api/trainer/learners/{other_learner_id}/engagement",
        headers={"Authorization": f"Bearer {t_tok}"},
    )
    assert res.status_code == 403, res.text


def test_admin_and_learner_roles_denied_all_trainer_endpoints():
    _, admin_id = _register("Admin")
    _, learner_id = _register("Learner")
    for role, uid in [("Admin", admin_id), ("Learner", learner_id)]:
        email, _ = _register(role, prefix="rbac")
        tok = _login(email)
        assert client.get("/api/trainer/learners", headers={"Authorization": f"Bearer {tok}"}).status_code == 403
        assert client.get(
            f"/api/trainer/learners/{uid}/engagement",
            headers={"Authorization": f"Bearer {tok}"},
        ).status_code in (403, 404)
        assert client.get("/api/trainer/learners", headers={}).status_code == 401