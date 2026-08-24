from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
import os
import time
from dotenv import load_dotenv

from app.utils.ratelimit import limiter

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key")

from app.db.database import engine, Base, DATABASE_URL


def _apply_schema_migrations():
    """
    Idempotent dev-only migrations for columns added after tables were created.

    create_all() adds new tables but not new columns to existing tables, so
    columns added after the DB file already exists need an explicit ALTER TABLE.

    Runs for both SQLite (app_data.db) and PostgreSQL (deployed Neon DB).
    Must run BEFORE the routers are imported: the course router seeds the
    alphabet module/lessons into the DB at import time and needs the columns
    below to already exist.
    """
    if DATABASE_URL.startswith("sqlite"):
        import sqlite3
        from pathlib import Path

        db_path = Path(__file__).resolve().parent.parent / "app_data.db"
        try:
            with sqlite3.connect(db_path) as conn:
                user_cols = {row[1] for row in conn.execute("PRAGMA table_info(users)")}
                for col, ddl in {
                    "instructor_id": "VARCHAR(36)",
                    "reset_token_hash": "VARCHAR(255)",
                    "reset_token_expires_at": "DATETIME",
                }.items():
                    if col not in user_cols:
                        conn.execute(f"ALTER TABLE users ADD COLUMN {col} {ddl}")

                module_cols = {row[1] for row in conn.execute("PRAGMA table_info(modules)")}
                if "description" not in module_cols:
                    conn.execute("ALTER TABLE modules ADD COLUMN description TEXT")
                if "created_at" not in module_cols:
                    conn.execute("ALTER TABLE modules ADD COLUMN created_at DATETIME")

                cert_cols = {row[1] for row in conn.execute("PRAGMA table_info(certificates)")}
                if "lesson_id" not in cert_cols:
                    conn.execute("ALTER TABLE certificates ADD COLUMN lesson_id VARCHAR(36)")
        except Exception:
            pass
    else:
        from sqlalchemy import inspect as sa_inspect
        from sqlalchemy import text as sa_text

        insp = sa_inspect(engine)
        if insp.has_table("users"):
            user_cols = {c["name"] for c in insp.get_columns("users")}
            for col, ddl in {
                "instructor_id": "VARCHAR(36)",
                "reset_token_hash": "VARCHAR(255)",
                "reset_token_expires_at": "TIMESTAMP",
            }.items():
                if col not in user_cols:
                    with engine.begin() as conn:
                        conn.execute(sa_text(f"ALTER TABLE users ADD COLUMN {col} {ddl}"))

            # Widen role so "Accessibility Trainer" (21 chars) fits. Older Neon
            # databases created users.role as VARCHAR(20), which silently
            # rejects that valid role on self-registration with a 500.
            role_type = str(next(
                (c["type"] for c in insp.get_columns("users") if c["name"] == "role"), ""
            ))
            if role_type == "VARCHAR(20)":
                with engine.begin() as conn:
                    conn.execute(sa_text("ALTER TABLE users ALTER COLUMN role TYPE VARCHAR(50)"))

        if insp.has_table("notifications"):
            notif_cols = {c["name"] for c in insp.get_columns("notifications")}
            if "title" not in notif_cols:
                with engine.begin() as conn:
                    conn.execute(sa_text("ALTER TABLE notifications ADD COLUMN title VARCHAR(200) NOT NULL DEFAULT ''"))

        if insp.has_table("certificates"):
            cert_cols = {c["name"] for c in insp.get_columns("certificates")}
            if "lesson_id" not in cert_cols:
                with engine.begin() as conn:
                    conn.execute(sa_text("ALTER TABLE certificates ADD COLUMN lesson_id UUID"))


_apply_schema_migrations()

# Fail fast: abort startup before serving traffic if the production config is
# missing required values or points at dev-only endpoints (see predeploy/).
from predeploy.config_check import validate_config_or_raise

validate_config_or_raise()

# Ensure all database tables exist BEFORE routers are imported. The course
# router seeds the alphabet module/lessons at import time and queries the
# "modules" table, so create_all() must run first or startup crashes with
# "relation modules does not exist" on a fresh database.
from app.models import models
Base.metadata.create_all(bind=engine)

# Import all project routers
from app.routers.profile_router import router as profile_router
from app.routers.gesture_router import router as gesture_router
from app.routers.progress_router import router as progress_router
from app.routers.translation_history_router import router as translation_history_router
from app.routers.dictionary_router import router as dictionary_router
from app.routers.feedback_router import router as feedback_router
from app.routers.integration_router import router as integration_router
from app.routers.lessons import router as lessons_router
from app.routers.admin_router import router as admin_router
from app.routers.instructor_router import router as instructor_router
from app.routers.notification_router import router as notification_router
from app.routers import auth, course, practice, trainer_router
from app.routers import analytics, assessment, recommendation
from app.routers.certificate import router as certificate_router
from app.routers.report import router as report_router


app = FastAPI(
    title="AI Sign Language Platform API",
    description="Final Production-Frozen API documentation for cross-team integration (Frontend, AI, and Business Logic).",
    version="1.0.0"
)

# Attach the per-user rate limiter (slowapi) to the application instance.
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Day 6 Milestone 3: Friendly 429 response when a per-user rate limit is hit.
    Includes the reason and a Retry-After header so clients know when to retry.
    """
    retry_after = 60
    view_limit = getattr(request.state, "view_rate_limit", None)
    if view_limit is not None:
        try:
            item, identifiers = view_limit
            window_stats = limiter.limiter.get_window_stats(item, *identifiers)
            retry_after = max(1, int(window_stats[0] - time.time()))
        except Exception:
            pass

    return JSONResponse(
        status_code=429,
        content={
            "message": "Too many requests. Please slow down and try again shortly.",
            "error": "rate_limit_exceeded",
            "detail": exc.detail,
            "retry_after_seconds": retry_after,
        },
        headers={"Retry-After": str(retry_after)},
    )


# Milestone 3 Security Middleware - Security Headers Enforcement
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# CORS origins are configurable via ALLOWED_ORIGINS (comma-separated).
# Defaults to "*" for local development; a deployment should set the real
# frontend origin(s) in .env.production. Never combine "*" with credentials
# on a public deployment.
ALLOWED_ORIGINS_CFG = os.getenv("ALLOWED_ORIGINS", "*")
_CORS_ORIGINS = [o.strip() for o in ALLOWED_ORIGINS_CFG.split(",") if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register each router EXACTLY ONCE to prevent duplicate endpoints in Swagger UI
app.include_router(profile_router)
app.include_router(gesture_router)
app.include_router(progress_router)
app.include_router(translation_history_router)
app.include_router(dictionary_router)
app.include_router(feedback_router)
app.include_router(integration_router)
app.include_router(auth.router)
app.include_router(admin_router)
app.include_router(instructor_router)
app.include_router(notification_router)
app.include_router(lessons_router)
app.include_router(course.router)
app.include_router(practice.router)
app.include_router(trainer_router.router)
app.include_router(analytics.router)
app.include_router(assessment.router)
app.include_router(recommendation.router)
app.include_router(certificate_router)
app.include_router(report_router)

@app.get("/health", tags=["System Health & Status"], summary="Health Check", description="Confirm the backend is up and environment variables loaded.")
def health_check():
    """
    Health check endpoint reporting the status of each dependency separately
    (database, model inference service, storage) rather than one combined flag.
    """
    import os as _os
    from app.db.database import engine

    deps: dict[str, str] = {}

    # 1. Database
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        deps["database"] = "healthy"
    except Exception as exc:
        deps["database"] = f"unhealthy: {type(exc).__name__}: {exc}"

    # 2. Model inference service
    ai_url = _os.getenv("AI_SERVICE_URL", "http://ai-service:8001").rstrip("/")
    try:
        import httpx
        ai_resp = httpx.get(f"{ai_url}/health", timeout=5.0)
        deps["model_inference"] = "healthy"
        if ai_resp.status_code != 200:
            deps["model_inference"] = f"unhealthy: HTTP {ai_resp.status_code}"
    except Exception as exc:
        deps["model_inference"] = f"unhealthy: {type(exc).__name__}: {exc}"

    # 3. Storage (PDF/certificate output dir)
    pdf_dir = _os.getenv("PDF_OUTPUT_DIR", "/tmp/certificates")
    try:
        _os.makedirs(pdf_dir, exist_ok=True)
        if not _os.access(pdf_dir, os.W_OK):
            deps["storage"] = f"unhealthy: {pdf_dir} not writable"
        else:
            deps["storage"] = "healthy"
    except Exception as exc:
        deps["storage"] = f"unhealthy: {type(exc).__name__}: {exc}"

    # Overall health reflects the CORE backend runtime deps (database + storage).
    # The model_inference service is a separately deployed external dependency:
    # its connectivity is reported for observability but does not downgrade the
    # platform's own health flag (the frontend readiness probes rely on `status`).
    core_ok = all(
        deps.get(dep, "unhealthy") == "healthy"
        for dep in ("database", "storage")
    )
    overall = "healthy" if core_ok else "degraded"

    return {
        "status": overall,
        "env_loaded": bool(SECRET_KEY),
        "api_status": "frozen_production_ready",
        "dependencies": deps,
        "milestone_tracker": {
            "milestone_1": "Complete",
            "milestone_2": "Complete",
            "milestone_3": "Day 10 Complete - API FROZEN"
        }
    }
 
@app.get("/", tags=["System Health & Status"], summary="Root / API Launch Status", description="Platform launch status and milestone tracker.")
def read_root():
    """
    Root endpoint verifying platform launch status and milestone tracker.
    """
    return {
        "message": "Welcome to the Sign Language Platform API - Final Production Release",
        "milestone_tracker": {
            "milestone_1": "Complete",
            "milestone_2": "Complete",
            "milestone_3_day_1": "Passed",
            "milestone_3_day_2": "Passed"
        }
    }