from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key")

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
from app.routers import auth, course, practice
from app.db.database import engine, Base
from app.models import models

# Ensure all database tables exist on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI Sign Language Platform API",
    description="Final Production-Frozen API documentation for cross-team integration (Frontend, AI, and Business Logic).",
    version="1.0.0"
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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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

@app.get("/health", tags=["System Health & Status"])
def health_check():
    """
    Health check endpoint supporting GET to confirm backend status.
    """
    return {
        "status": "healthy", 
        "env_loaded": bool(SECRET_KEY), 
        "api_status": "frozen_production_ready",
        "milestone_tracker": {
            "milestone_1": "Complete",
            "milestone_2": "Complete",
            "milestone_3": "Day 1 Complete"
        }
    }
 
@app.get("/", tags=["System Health Status"])
def read_root():
    """
    Root endpoint verifying platform launch status and milestone tracker.
    """
    return {
        "message": "Welcome to the Sign Language Platform API - Final Production Release",
        "milestone_tracker": {
            "milestone_1": "Complete",
            "milestone_2": "Complete",
            "milestone_3_day_1": "Passed"
        }
    }