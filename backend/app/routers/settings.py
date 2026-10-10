"""Settings API."""
from fastapi import APIRouter
from app.config import settings

router = APIRouter(prefix="/api/settings", tags=["settings"])


@router.get("")
def get_settings():
    """Return non-sensitive application settings."""
    return {
        "app_name": settings.APP_NAME,
        "demo_mode": settings.DEMO_MODE,
        "exam_mode": settings.EXAM_MODE,
        "telegram_connected": settings.TELEGRAM_CONNECTED,
        "telegram_bot_token_configured": bool(settings.TELEGRAM_BOT_TOKEN),
        "llm_api_key_configured": bool(settings.LLM_API_KEY),
        "llm_model": settings.LLM_MODEL,
        "mode_label": "Demo Mode" if settings.DEMO_MODE else "Connected",
    }
