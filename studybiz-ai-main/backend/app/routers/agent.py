"""Agent router — AI assistant chat and agent activity log."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import AgentLog, User
from app.schemas import AgentChatRequest, AgentChatResponse, AgentLogResponse
from app.utils.auth import get_current_user
from app.agent.engine import AgentEngine

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/chat", response_model=AgentChatResponse)
def chat(
    req: AgentChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    engine = AgentEngine(db, current_user)
    result = engine.process(req.message, req.context)
    return AgentChatResponse(**result)


@router.get("/logs", response_model=List[AgentLogResponse])
def get_logs(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    logs = db.query(AgentLog).filter(
        AgentLog.user_id == current_user.id,
    ).order_by(AgentLog.created_at.desc()).limit(limit).all()
    return logs


@router.get("/tools")
def list_agent_tools(
    current_user: User = Depends(get_current_user),
):
    """List all available agent tools."""
    from app.agent.tools import TOOL_REGISTRY
    return [
        {
            "name": name,
            "description": config["description"],
            "requires_approval": config["requires_approval"],
            "params": config["params"],
        }
        for name, config in TOOL_REGISTRY.items()
    ]
