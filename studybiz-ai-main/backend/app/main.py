"""StudyBiz AI — FastAPI Application Entry Point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import engine, Base
from app.routers import (
    auth, academic, customers, products, orders, bulk_orders,
    suppliers, exceptions, finance, dashboard, agent,
    automation, messages, approvals, notifications, export
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Create tables on startup."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="StudyBiz AI",
    description="Academic & Business Operations Agent for Student Entrepreneurs",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router, prefix="")
app.include_router(academic.router, prefix="")
app.include_router(customers.router, prefix="")
app.include_router(products.router, prefix="")
app.include_router(orders.router, prefix="")
app.include_router(bulk_orders.router, prefix="")
app.include_router(suppliers.router, prefix="")
app.include_router(exceptions.router, prefix="")
app.include_router(finance.router, prefix="")
app.include_router(dashboard.router, prefix="")
app.include_router(agent.router, prefix="")
app.include_router(automation.router, prefix="")
app.include_router(messages.router, prefix="")
app.include_router(approvals.router, prefix="")
app.include_router(notifications.router, prefix="")
app.include_router(export.router, prefix="")


@app.get("/")
def root():
    return {
        "name": "StudyBiz AI",
        "version": "1.0.0",
        "description": "Academic & Business Operations Agent for Student Entrepreneurs",
        "docs": "/docs",
        "status": "running",
    }


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": "ok"}
