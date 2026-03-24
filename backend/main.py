from fastapi import FastAPI
from config import APP_NAME, DEBUG

app = FastAPI(
    title=APP_NAME,
    description="AI-powered mock interview preparation platform",
    version="1.0.0",
    debug=DEBUG
)

@app.get("/", tags=["Root"])
def root():
    return {"message": f"Welcome to {APP_NAME}"}

@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "app": APP_NAME,
        "version": "1.0.0"
    }