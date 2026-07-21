from fastapi import FastAPI

# Import your router files
from app.routers.profile_router import router as profile_router
from app.routers.gesture_router import router as gesture_router
from app.routers.progress_router import router as progress_router
from app.routers.translation_history_router import router as translation_history_router
from app.routers.dictionary_router import router as dictionary_router
from app.routers import auth, course, practice

app = FastAPI()

# Register the routers
app.include_router(profile_router)
app.include_router(gesture_router)
app.include_router(progress_router)
app.include_router(translation_history_router)
app.include_router(dictionary_router)
app.include_router(auth.router)
app.include_router(course.router)
app.include_router(practice.router)

# Additional prefixed routers if your app structure uses them
app.include_router(course.router, prefix="/courses")
app.include_router(practice.router, prefix="/practice")

# Clean Health Check
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}

@app.get("/", tags=["default"])
def read_root():
    return {"message": "Welcome to the Sign Language Platform API"}