<<<<<<< HEAD
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware  # 🌐 CRITICAL FOR FRONTEND INTEGRATION
import time
import os
from dotenv import load_dotenv
from app.routers import auth, course, practice, analytics, feedback, assessment, recommendation, certificate
from app.db.database import engine
from app.models.models import Base
=======
from fastapi import FastAPI
from app.db.database import engine, Base
from app import models
from app.routers import auth, course, practice
>>>>>>> da135f1 (changes)

# Create database tables automatically
Base.metadata.create_all(bind=engine)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AI-Powered Sign Language Learning & Assessment Platform Backend",
    version="1.0.0"
)

# Clean Health Check
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}

# Include routers without overriding tags (Fixes duplicates and long URLs)
app.include_router(auth.router)
<<<<<<< HEAD
app.include_router(course.router)
app.include_router(practice.router)
app.include_router(analytics.router)
app.include_router(feedback.router)
app.include_router(assessment.router)
app.include_router(recommendation.router)
app.include_router(certificate.router)
=======
app.include_router(course.router, prefix="/courses")
app.include_router(practice.router, prefix="/practice")  # FIXED: Added prefix here

@app.get("/", tags=["default"])
def read_root():
    return {"message": "Welcome to the Sign Language Platform API"}
>>>>>>> da135f1 (changes)
