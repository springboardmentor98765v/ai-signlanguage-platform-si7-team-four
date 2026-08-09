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
