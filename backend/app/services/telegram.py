```python
"""Telegram Bot API integration service.

Supports:
- Webhook mode (production): receives updates via webhook
- Polling mode (development): polls Telegram getUpdates
- Demo mode (no credentials): simulated messages through the same backend

Idempotency: tracks processed update IDs to prevent duplicate processing.
"""

import httpx
from sqlalchemy.orm import Session

from app.database import ProcessedUpdate
from app.services.agent import AIAgent


class TelegramService:
    """Handles Telegram Bot API communication."""

    def __init__(
        self,
        db: Session,
        bot_token: str = "",
        connected: bool = False,
        demo_mode: bool = True,
    ):
        self.db = db
        self.bot_token = bot_token
        self.connected = connected and bool(bot_token)
        self.demo_mode = demo_mode or not self.connected
        self.api_base = (
            f"https://api.telegram.org/bot{bot_token}"
            if bot_token
            else ""
        )

    @property
    def mode_label(self):
        return "connected" if self.connected else "demo"

    def is_update_processed(self, update_id):
        """Check whether an update has already been processed."""
        if update_id is None:
            return False

        return (
            self.db.query(ProcessedUpdate)
            .filter(ProcessedUpdate.update_id == update_id)
            .first()
            is not None
        )

    def mark_update_processed(self, update_id):
        """Record an update after successful processing."""
        if update_id is None or self.is_update_processed(update_id):
            return

        self.db.add(ProcessedUpdate(update_id=update_id))
        self.db.commit()

    async def send_message(self, chat_id, text, reply_markup=None):
        """Send a message to Telegram."""
        if not self.connected:
            return {
                "success": True,
                "demo": True,
                "message": "Message stored (demo mode)",
            }

        url = f"{self.api_base}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": text,
        }

        if reply_markup:
            payload["reply_markup"] = reply_markup

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json=payload,
                    timeout=10,
                )
                data = response.json()

                if data.get("ok"):
                    return {
                        "success": True,
                        "message_id": data["result"]["message_id"],
                    }

                return {
                    "success": False,
                    "error": data.get(
                        "description",
                        "Unknown Telegram API error",
                    ),
                }

        except Exception as exc:
            return {"success": False, "error": str(exc)}

    async def process_update(self, update):
        """Process one incoming Telegram update."""
        update_id = update.get("update_id")

        if self.is_update_processed(update_id):
            return {
                "skipped": True,
                "reason": "duplicate",
            }

        message = update.get("message") or {}

        if not message:
            if update_id is not None:
                self.mark_update_processed(update_id)

            return {
                "skipped": True,
                "reason": "no_message",
            }

        chat = message.get("chat") or {}
        from_user = message.get("from") or {}

        chat_id = chat.get("id")
        text = (message.get("text") or "").strip()

        # Use the stable Telegram sender ID to identify the customer.
        raw_user_id = from_user.get("id")
        telegram_user_id = (
            str(raw_user_id) if raw_user_id is not None else None
        )

        telegram_username = from_user.get("username")

        display_name = " ".join(
            part
            for part in (
                from_user.get("first_name"),
                from_user.get("last_name"),
            )
            if part
        ).strip()

        if not display_name:
            display_name = telegram_username or "Telegram Customer"

        if not text:
            if update_id is not None:
                self.mark_update_processed(update_id)

            return {
                "skipped": True,
                "reason": "no_text",
            }

        if telegram_user_id is None:
            # Do not create an anonymous customer that could be duplicated
            # on every incoming message.
            return {
                "success": False,
                "error": "Telegram sender ID is missing.",
            }

        print(
            "[TELEGRAM DEBUG] "
            f"update_id={update_id}, "
            f"sender_id={telegram_user_id}, "
            f"username={telegram_username}, "
            f"text={text!r}"
        )

        try:
            agent = AIAgent(self.db, demo_mode=self.demo_mode)

            result = agent.process_customer_message(
                customer_id=None,
                display_name=display_name,
                text=text,
                telegram_user_id=telegram_user_id,
                telegram_username=telegram_username,
            )

            # Mark only after processing succeeds. If processing raises an
            # exception, Telegram can retry the update.
            if update_id is not None:
                self.mark_update_processed(update_id)

        except Exception:
            self.db.rollback()
            raise

        if self.connected and chat_id is not None:
            reply = result.get(
                "response",
                "I did not understand that.",
            )

            send_result = await self.send_message(chat_id, reply)

            if not send_result.get("success"):
                print(
                    "[TELEGRAM ERROR] Failed to send reply: "
                    f"{send_result.get('error')}"
                )

        return result

    async def process_simulated_message(
        self,
        display_name,
        text,
        telegram_user_id=None,
        telegram_username=None,
    ):
        """Process a simulated customer message in demo mode."""
        agent = AIAgent(self.db, demo_mode=True)

        return agent.process_customer_message(
            customer_id=None,
            display_name=display_name,
            text=text,
            telegram_user_id=(
                str(telegram_user_id)
                if telegram_user_id is not None
                else None
            ),
            telegram_username=telegram_username,
        )

    async def setup_webhook(self, webhook_url):
        """Configure the Telegram webhook."""
        if not self.bot_token:
            return {
                "success": False,
                "error": "No bot token configured",
            }

        url = f"{self.api_base}/setWebhook"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json={"url": webhook_url},
                    timeout=10,
                )
                data = response.json()

                return {
                    "success": data.get("ok", False),
                    "data": data,
                }

        except Exception as exc:
            return {
                "success": False,
                "error": str(exc),
            }

    async def poll_updates(self):
        """Poll Telegram updates during development."""
        if not self.connected:
            return []

        url = f"{self.api_base}/getUpdates"

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    url,
                    json={"timeout": 0},
                    timeout=15,
                )
                data = response.json()

                if data.get("ok"):
                    return data.get("result", [])

                return []

        except Exception as exc:
            print(f"[TELEGRAM ERROR] Polling failed: {exc}")
            return []
```
