from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from api import auth, resume, jobs, interview
from api.analytics import router as analytics_router

app = FastAPI(title="HireSmart API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(auth.router, prefix="/auth")
app.include_router(resume.router, prefix="/resume")
app.include_router(jobs.router, prefix="/jobs")
app.include_router(interview.router, prefix="/interview")
app.include_router(analytics_router, prefix="/analytics")

@app.get("/")
def root():
    return {"message": "HireSmart API is running"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.get("/ui")
def serve_ui():
    return FileResponse("test_ui.html")