"""
Shared pytest fixtures & test isolation for the Backend test suite.

Runs the entire suite against a throwaway SQLite database in a temp directory so
that no test run ever writes to / corrupts the real `Backend/app_data.db`.

How it works:
  - A temporary engine + sessionmaker are created here (conftest is loaded
    before any test module, so the patch happens before `app.main` is imported).
  - `app.db.database.engine` and `app.db.database.SessionLocal` are swapped to
    point at the temp DB. Because `get_db()` resolves the module-global
    `SessionLocal` at call time, every FastAPI `Depends(get_db)` session (and any
    direct `SessionLocal()` use, e.g. the Day-3 certificate tests) is redirected.
  - `Base.metadata.create_all()` runs on the temp engine, mirroring the app's
    own startup behaviour without touching the real data file.

This reuses the app's normal database wiring rather than duplicating a test
harness, and lets the existing `TestClient(app)` module-level pattern keep
working unchanged.
"""

import tempfile

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import database
from app.db.database import Base
from app.models import models  # noqa: F401  (registers every table on Base.metadata)

# --- Fresh temp database, created once per test session ---
_TEST_DB_DIR = tempfile.mkdtemp(prefix="signlang_test_db_")
_TEST_DB_PATH = f"{_TEST_DB_DIR}/test_app.db"

_TEST_DB_ENGINE = create_engine(
    f"sqlite:///{_TEST_DB_PATH}",
    connect_args={"check_same_thread": False},
)
_TEST_SESSION_MAKER = sessionmaker(autocommit=False, autoflush=False, bind=_TEST_DB_ENGINE)

# Build all tables on the temp DB (same schema as production).
Base.metadata.create_all(bind=_TEST_DB_ENGINE)

# Redirect the whole app to the temp DB:
#   - `get_db()` sessions (all routers) resolve `database.SessionLocal` at call time
#   - direct `SessionLocal()` usage (Day-3 service tests) is covered as well
#   - `app.main`'s startup `create_all(bind=engine)` now targets the temp DB too
database.engine = _TEST_DB_ENGINE
database.SessionLocal = _TEST_SESSION_MAKER


# ---------------------------------------------------------------------------
# Shared test helpers.
#
# Admin accounts cannot be self-registered (security rule enforced in auth.py),
# so tests that need Admin / Instructor accounts seed them DIRECTLY into the
# isolated temp database. Password hashes are real bcrypt so API login works.
# ---------------------------------------------------------------------------
import bcrypt as _bcrypt
import uuid as _uuid


def make_user(email, username=None, role="Learner", password="SecurePassword123!", is_active=True):
    """Insert a real user row directly into the isolated temp DB."""
    local_db = _TEST_SESSION_MAKER()
    try:
        user = models.User(
            id=str(_uuid.uuid4()),
            username=username or f"u_{_uuid.uuid4().hex[:8]}",
            email=email,
            password_hash=_bcrypt.hashpw(password.encode("utf-8"), _bcrypt.gensalt()).decode("utf-8"),
            role=role,
            is_active=is_active,
        )
        local_db.add(user)
        local_db.commit()
        local_db.refresh(user)
        return {"id": str(user.id), "email": user.email, "username": user.username, "role": user.role}
    finally:
        local_db.close()


def login_token(client, email, password="SecurePassword123!"):
    """Log in via the API and return the access token."""
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    data = res.json()
    token = data.get("access_token") or data.get("accessToken") or data["token"]
    return token
