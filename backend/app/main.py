"""
FastAPI application entry point.

Run with:  uvicorn app.main:app --reload --port 8000
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.database import Base, engine
from app.api.routes import auth, users, aircraft, sorties, training_progress, defects, audit_logs

# Create the FastAPI app instance.
app = FastAPI(
    title="Skynet - Flight Operations Module",
    description="Mini Skynet module for AIRMAN technical assessment.",
    version="0.1.0",
)

# Allow the frontend (running on a different port) to call us.
# In production, replace allow_origins with the actual frontend URL.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def create_tables():
    """
    Auto-create all tables on startup.
    In a production app we'd use Alembic migrations instead.
    See docs/known-limitations.md.
    """
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {"app": "Skynet", "status": "ok", "docs": "/docs"}


# Register all the route groups.
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(aircraft.router)
app.include_router(sorties.router)
app.include_router(training_progress.router)
app.include_router(defects.router)
app.include_router(audit_logs.router)
