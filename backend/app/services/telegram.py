"""Telegram Bot API integration service.

Supports:
- Webhook mode (production): receives updates via webhook
- Polling mode (development): polls Telegram getUpdates
- Demo mode (no credentials): simulated messages through the same backend

Idempotency: tracks processed update IDs to prevent duplicate processing.
"""
import hashlib
import httpx
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.database import ProcessedUpdate
from app.services.agent import AIAgent


class TelegramService:
    """Handles Telegram Bot API communication."""

    def __init__(self, db: Session, bot_token: str = "", connected: bool = False, demo_mode: bool = True):
        self.db = db
        self.bot_token = bot_token
        self.connected = connected and bool(bot_token)
        self.demo_mode = demo_mode or not self.connected
        self.api_base = f"https://api.telegram.org/bot{bot_token}" if bot_token else ""

    @property
    def mode_label(self):
        if self.connected:
            return "connected"
        return "demo"

    def is_update_processed(self, update_id):
        """Check if a Telegram update has already been processed (idempotency)."""
        existing = self.db.query(ProcessedUpdate).filter(ProcessedUpdate.update_id == update_id).first()
        return existing is not None

    def mark_update_processed(self, update_id):
        """Record that an update has been processed."""
        record = ProcessedUpdate(update_id=update_id)
        self.db.add(record)
        self.db.commit()

    async def send_message(self, chat_id, text, reply_markup=None):
        """Send a message to a Telegram chat."""
        if not self.connected:
            # In demo mode, messages are stored in the database only
            return {"success": True, "demo": True, "message": "Message stored (demo mode)"}

        url = f"{self.api_base}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
        }
        if reply_markup:
            payload["reply_markup"] = reply_markup

        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, json=payload, timeout=10)
                data = resp.json()
                if data.get("ok"):
                    return {"success": True, "message_id": data["result"]["message_id"]}
                else:
                    return {"success": False, "error": data.get("description", "Unknown error")}
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def process_update(self, update):
        """Process a single Telegram update.

        This is the entry point for all incoming Telegram messages,
        whether from webhook or polling. It is idempotent.
        """
        update_id = update.get("update_id")
        if update_id is not None and self.is_update_processed(update_id):
            return {"skipped": True, "reason": "duplicate"}

        message = update.get("message", {})
        if not message:
            if update_id is not None:
                self.mark_update_processed(update_id)
            return {"skipped": True, "reason": "no_message"}

        chat_id = message.get("chat", {}).get("id")
        text = message.get("text", "")
        from_user = message.get("from", {})

        telegram_user_id = str(from_user.get("id", "")) if from_user else None
        display_name = " ".join(filter(None, [
            from_user.get("first_name", ""),
            from_user.get("last_name", ""),
        ])) or from_user.get("username", "Unknown Customer")
        telegram_username = from_user.get("username")

        # Process through AI agent
        agent = AIAgent(self.db, demo_mode=self.demo_mode)
        result = agent.process_customer_message(
            customer_id=None,
            display_name=display_name,
            text=text,
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
        )

        # Send response via Telegram if connected
        if self.connected and chat_id:
            await self.send_message(chat_id, result.get("response", "I did not understand that."))

        # Mark update as processed
        if update_id is not None:
            self.mark_update_processed(update_id)

        return result

    async def process_simulated_message(self, display_name, text, telegram_user_id=None, telegram_username=None):
        """Process a simulated customer message (for demo mode).

        This exercises the same backend and business rules as real Telegram messages.
        """
        agent = AIAgent(self.db, demo_mode=True)
        result = agent.process_customer_message(
            customer_id=None,
            display_name=display_name,
            text=text,
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
        )
        return result

    async def setup_webhook(self, webhook_url):
        """Set the Telegram webhook URL."""
        if not self.bot_token:
            return {"success": False, "error": "No bot token configured"}

        url = f"{self.api_base}/setWebhook"
        payload = {"url": webhook_url}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, json=payload, timeout=10)
                data = resp.json()
                return {"success": data.get("ok", False), "data": data}
            except Exception as e:
                return {"success": False, "error": str(e)}

    async def poll_updates(self):
        """Poll for updates (development mode). Not used in production."""
        if not self.connected:
            return []

        url = f"{self.api_base}/getUpdates"
        params = {"timeout": 0}
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.post(url, json=params, timeout=15)
                data = resp.json()
                if data.get("ok"):
                    return data.get("result", [])
                return []
            except Exception:
                return []
