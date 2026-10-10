"""Dashboard API - overview metrics."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db, Campaign, Order, Conversation, Exception_, ActionLog
from app.services.agent import AgentTools

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/metrics")
def get_metrics(db: Session = Depends(get_db)):
    tools = AgentTools(db)
    metrics = tools.get_dashboard_metrics()

    # Add recent activity
    recent_logs = db.query(ActionLog).order_by(ActionLog.timestamp.desc()).limit(10).all()
    metrics["recent_activity"] = [{
        "id": log.id,
        "actor": log.actor_type,
        "action": log.action_type,
        "entity": log.entity_type,
        "summary": log.input_summary,
        "result": log.result,
        "timestamp": log.timestamp.isoformat() if log.timestamp else None,
    } for log in recent_logs]

    # Priority exceptions
    priority_exceptions = db.query(Exception_).filter(Exception_.status == "open").limit(5).all()
    metrics["priority_exceptions"] = [{
        "id": e.id,
        "type": e.type,
        "description": e.description,
        "recommended_action": e.recommended_action,
    } for e in priority_exceptions]

    # Active campaigns
    active = db.query(Campaign).filter(Campaign.status == "open").all()
    metrics["active_campaigns"] = [{
        "id": c.id,
        "name": c.name,
        "closes_at": c.closes_at.isoformat() if c.closes_at else None,
    } for c in active]

    # AI operations summary
    campaign = active[0] if active else None
    if campaign:
        order_count = db.query(Order).filter(Order.campaign_id == campaign.id).count()
        pending = db.query(Order).filter(Order.campaign_id == campaign.id, Order.status == "pending_payment").count()
        verifying = db.query(Order).filter(Order.campaign_id == campaign.id, Order.payment_status == "verifying").count()
        metrics["ai_summary"] = (
            f"Your {campaign.name} has {order_count} orders. "
            f"{pending} orders are awaiting payment, {verifying} payment needs verification. "
            f"{len(metrics['priority_exceptions'])} exceptions need attention."
        )
    else:
        metrics["ai_summary"] = "No active group buy."

    return metrics
