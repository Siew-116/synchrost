"""Telegram webhook and integration API."""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.telegram import TelegramService
from app.config import settings

router = APIRouter(prefix="/api/telegram", tags=["telegram"])


@router.get("/status")
def telegram_status():
    """Return the current Telegram integration status."""
    return {
        "connected": settings.TELEGRAM_CONNECTED,
        "mode": "connected" if settings.TELEGRAM_CONNECTED else "demo",
        "webhook_url": settings.TELEGRAM_WEBHOOK_URL or None,
        "bot_token_configured": bool(settings.TELEGRAM_BOT_TOKEN),
    }


@router.post("/webhook")
async def telegram_webhook(request: Request, db: Session = Depends(get_db)):
    """Receive Telegram webhook updates.

    Telegram sends POST requests to this endpoint when a user messages the bot.
    This endpoint is idempotent - duplicate updates are not processed twice.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        return {"error": "Telegram bot token not configured"}

    body = await request.json()
    service = TelegramService(
        db,
        bot_token=settings.TELEGRAM_BOT_TOKEN,
        connected=settings.TELEGRAM_CONNECTED,
        demo_mode=settings.DEMO_MODE,
    )
    result = await service.process_update(body)
    return result


@router.get("/poll")
async def poll_updates(db: Session = Depends(get_db)):
    """Poll for Telegram updates (development mode).

    Uses long polling. For production, use the webhook endpoint instead.
    """
    if not settings.TELEGRAM_BOT_TOKEN:
        return {"error": "Telegram bot token not configured", "updates": []}

    service = TelegramService(
        db,
        bot_token=settings.TELEGRAM_BOT_TOKEN,
        connected=settings.TELEGRAM_CONNECTED,
        demo_mode=settings.DEMO_MODE,
    )
    updates = await service.poll_updates()
    results = []
    for update in updates:
        result = await service.process_update(update)
        results.append(result)
    return {"processed": len(results), "results": results}
