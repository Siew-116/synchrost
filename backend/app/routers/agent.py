"""AI Co-Admin API."""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.agent import AIAgent
from app.config import settings

router = APIRouter(prefix="/api/agent", tags=["agent"])


class AdminQuery(BaseModel):
    query: str


@router.post("/query")
def admin_query(data: AdminQuery, db: Session = Depends(get_db)):
    agent = AIAgent(db, llm_api_key=settings.LLM_API_KEY, demo_mode=settings.DEMO_MODE)
    response = agent.process_admin_query(data.query)
    return {"response": response, "mode": "demo" if agent.demo_mode else "llm"}


class SimulatedMessage(BaseModel):
    display_name: str
    text: str
    telegram_user_id: str | None = None
    telegram_username: str | None = None


@router.post("/simulate")
def simulate_customer_message(data: SimulatedMessage, db: Session = Depends(get_db)):
    """Simulate a customer message for demo mode.

    This exercises the same backend and business rules as real Telegram messages.
    """
    agent = AIAgent(db, llm_api_key=settings.LLM_API_KEY, demo_mode=settings.DEMO_MODE)
    result = agent.process_customer_message(
        customer_id=None,
        display_name=data.display_name,
        text=data.text,
        telegram_user_id=data.telegram_user_id,
        telegram_username=data.telegram_username,
    )
    return result
