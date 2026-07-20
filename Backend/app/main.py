

# Clean Health Check
@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "healthy"}

# Include routers without overriding tags (Fixes duplicates and long URLs)
app.include_router(auth.router)

app.include_router(course.router)
app.include_router(practice.router)
app.include_router(analytics.router)
app.include_router(feedback.router)
app.include_router(assessment.router)
app.include_router(recommendation.router)
app.include_router(certificate.router)

app.include_router(course.router, prefix="/courses")
app.include_router(practice.router, prefix="/practice")  # FIXED: Added prefix here

@app.get("/", tags=["default"])
def read_root():
    return {"message": "Welcome to the Sign Language Platform API"}

