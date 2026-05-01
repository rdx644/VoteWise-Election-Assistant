"""
VoteWise — AI Election Education Platform.

Main FastAPI application entry point with route registration,
static file serving, health check, and user management endpoints.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.cloud_logging import log_event
from backend.config import settings
from backend.database import db
from backend.exceptions import VoteWiseError
from backend.middleware import register_middleware
from backend.models import UserProfile
from backend.routes.analytics import router as analytics_router
from backend.routes.chat import router as chat_router
from backend.routes.quiz import router as quiz_router
from backend.routes.timeline import router as timeline_router

logger = logging.getLogger("votewise.app")

FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown lifecycle."""
    log_event("app_startup", {"version": settings.app_version, "env": settings.app_env})
    logger.info("VoteWise v%s starting (%s)", settings.app_version, settings.app_env)
    yield
    log_event("app_shutdown", {"version": settings.app_version})
    logger.info("VoteWise shutting down")


app = FastAPI(
    title=settings.app_title,
    version=settings.app_version,
    description="AI-powered election process education platform",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Register middleware
register_middleware(app)

# Register routers
app.include_router(chat_router)
app.include_router(timeline_router)
app.include_router(quiz_router)
app.include_router(analytics_router)

# User routes
user_router = APIRouter(prefix="/api/users", tags=["Users"])


@user_router.get("")
async def list_users() -> list[dict[str, Any]]:
    """List all registered users."""
    return [u.model_dump(mode="json") for u in db.list_users()]


@user_router.get("/{user_id}")
async def get_user(user_id: str) -> dict[str, Any]:
    """Get a specific user profile."""
    user = db.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user.model_dump(mode="json")


@user_router.post("", status_code=201)
async def create_user(data: dict[str, Any]) -> dict[str, Any]:
    """Create a new user profile."""
    user = UserProfile(**data)
    created = db.create_user(user)
    log_event("user_created", {"user_id": created.id, "name": created.name})
    return created.model_dump(mode="json")


@user_router.put("/{user_id}")
async def update_user(user_id: str, data: dict[str, Any]) -> dict[str, Any]:
    """Update an existing user profile."""
    updated = db.update_user(user_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="User not found")
    return updated.model_dump(mode="json")


@user_router.delete("/{user_id}")
async def delete_user(user_id: str) -> dict[str, str]:
    """Delete a user profile."""
    if not db.delete_user(user_id):
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "deleted"}


app.include_router(user_router)


# ── Health Check ──


@app.get("/api/health")
async def health_check() -> dict[str, Any]:
    """System health endpoint for monitoring and load balancers."""
    return {
        "status": "healthy",
        "service": "votewise-election-assistant",
        "version": settings.app_version,
        "environment": settings.app_env,
        "google_services": {
            "gemini_configured": bool(settings.gemini_api_key),
            "tts_mode": settings.tts_mode,
            "database_mode": settings.database_mode,
            "cloud_project": settings.google_cloud_project or "not configured",
            "cloud_logging": settings.is_production,
            "cloud_storage": bool(settings.gcs_bucket_name),
        },
    }


# ── Exception Handler ──


@app.exception_handler(VoteWiseError)
async def votewise_error_handler(_request: Request, exc: VoteWiseError) -> JSONResponse:
    """Handle custom VoteWise exceptions with structured error responses."""
    return JSONResponse(status_code=exc.status_code, content=exc.to_dict())


# ── Static Files & Frontend ──

if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    async def serve_index() -> FileResponse:
        """Serve the main single-page application."""
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/{path:path}")
    async def serve_frontend(path: str) -> FileResponse:
        """Serve static frontend assets or fall back to index.html."""
        file_path = FRONTEND_DIR / path
        if file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(FRONTEND_DIR / "index.html"))
