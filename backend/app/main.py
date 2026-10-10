"""StudyBiz AI - Main FastAPI application.

Entry point for the backend server. Sets up:
- Database initialization
- API routers
- Static file serving (frontend build)
- CORS for development
"""
import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.database import init_db
from app.routers import (
    dashboard_router,
    campaigns_router,
    orders_router,
    customers_router,
    inbox_router,
    exceptions_router,
    supplier_router,
    automation_router,
    agent_router,
    telegram_router,
    settings_router,
)

app = FastAPI(
    title=settings.APP_NAME,
    description="Agentic AI Co-Admin for Student Entrepreneurs",
    version="1.0.0",
)

# CORS - allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(dashboard_router)
app.include_router(campaigns_router)
app.include_router(orders_router)
app.include_router(customers_router)
app.include_router(inbox_router)
app.include_router(exceptions_router)
app.include_router(supplier_router)
app.include_router(automation_router)
app.include_router(agent_router)
app.include_router(telegram_router)
app.include_router(settings_router)


@app.on_event("startup")
def startup():
    """Initialize database and seed demo data on first run."""
    init_db()
    # Run seed if database is empty
    from app.seed import seed
    seed()


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.APP_NAME, "demo_mode": settings.DEMO_MODE}


# Serve frontend - use bundled HTML if React build not available
frontend_dist = Path(__file__).parent.parent.parent / "frontend" / "dist"
bundled_html = Path(__file__).parent / "static" / "index.html"

if frontend_dist.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
elif bundled_html.exists():
    @app.get("/")
    def serve_index():
        return FileResponse(str(bundled_html))
