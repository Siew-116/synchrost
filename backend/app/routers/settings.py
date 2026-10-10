"""Settings API."""
import json
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db, AutomationRule

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings():
    """Return non-sensitive application settings."""
    return {
        "app_name": settings.APP_NAME,
        "demo_mode": settings.DEMO_MODE,
        "busy_mode": settings.EXAM_MODE,
        "telegram_connected": settings.TELEGRAM_CONNECTED,
        "telegram_bot_token_configured": bool(settings.TELEGRAM_BOT_TOKEN),
        "llm_api_key_configured": bool(settings.LLM_API_KEY),
        "llm_model": settings.LLM_MODEL,
        "mode_label": "Demo Mode" if settings.DEMO_MODE else "Connected",
    }


class BusyModeToggle(BaseModel):
    enabled: bool


@router.put("/busy-mode")
def toggle_busy_mode(data: BusyModeToggle):
    """Toggle busy mode on or off at runtime."""
    import app.config as config_module
    config_module.settings.EXAM_MODE = data.enabled
    return {"busy_mode": data.enabled}
