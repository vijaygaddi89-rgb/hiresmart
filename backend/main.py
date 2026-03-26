# backend/main.py

from fastapi import FastAPI
from api.auth import router as auth_router
from api.resume import router as resume_router

app = FastAPI(
    title="HireSmart API",
    description="AI-Powered Interview Preparation Platform",
    version="0.4.0"
)


# ── Routers ───────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(resume_router)


# ── Core Endpoints ────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "HireSmart API is running 🚀"}


@app.get("/health")
def health():
    return {"status": "healthy", "version": "0.4.0"}