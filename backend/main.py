# backend/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from api.auth import router as auth_router
from api.resume import router as resume_router
from api.jobs import router as jobs_router
import os

app = FastAPI(
    title="HireSmart API",
    description="AI-Powered Interview Preparation Platform",
    version="0.5.0"
)

# ── CORS Middleware ───────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(resume_router)
app.include_router(jobs_router)

# ── Serve Test UI ─────────────────────────────────────────────
@app.get("/ui")
def serve_ui():
    ui_path = os.path.join(os.path.dirname(__file__), "test_ui.html")
    return FileResponse(ui_path)

# ── Core Endpoints ────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "HireSmart API is running 🚀"}

@app.get("/health")
def health():
    return {"status": "healthy", "version": "0.5.0"}