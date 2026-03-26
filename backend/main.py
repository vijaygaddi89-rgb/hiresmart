# backend/main.py

from fastapi import FastAPI
from api.auth import router as auth_router

app = FastAPI(
    title="HireSmart API",
    description="AI-Powered Interview Preparation Platform",
    version="0.3.0"
)


# ── Routers ───────────────────────────────────────────────────
app.include_router(auth_router)


# ── Core Endpoints ────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "HireSmart API is running 🚀"}


@app.get("/health")
def health():
    return {"status": "healthy", "version": "0.3.0"}