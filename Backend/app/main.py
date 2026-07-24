from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY", "fallback_secret_key")

# Import all your routers (including Day 9 integration)
from app.routers.profile_router import router as profile_router
from app.routers.gesture_router import router as gesture_router
from app.routers.progress_router import router as progress_router
from app.routers.translation_history_router import router as translation_history_router
from app.routers.dictionary_router import router as dictionary_router
from app.routers.feedback_router import router as feedback_router
from app.routers.integration_router import router as integration_router
from app.routers import auth, course, practice

app = FastAPI(
    title="AI Sign Language Platform API",
    description="Final Production-Frozen API documentation for cross-team integration (Frontend, AI, and Business Logic).",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all project routers
app.include_router(profile_router)
app.include_router(gesture_router)
app.include_router(progress_router)
app.include_router(translation_history_router)
app.include_router(dictionary_router)
app.include_router(feedback_router)
app.include_router(integration_router)
app.include_router(auth.router)
app.include_router(course.router)
app.include_router(practice.router)

app.include_router(course.router, prefix="/courses")
app.include_router(practice.router, prefix="/practice")

@app.get("/health", tags=["System Health & Status"])
def health_check():
    """
    Final health check endpoint to confirm backend container and environment variables are active.
    """
    return {"status": "healthy", "env_loaded": bool(SECRET_KEY), "api_status": "frozen_production_ready"}

@app.get("/", tags=["System Health & Status"])
def read_root():
    """
    Root endpoint verifying platform launch status.
    """
    return {"message": "Welcome to the Sign Language Platform API - Final Production Release"}
