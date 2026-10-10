"""Automation Rules API."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db, AutomationRule
import json

router = APIRouter(prefix="/api/automation", tags=["automation"])


@router.get("/rules")
def list_rules(db: Session = Depends(get_db)):
    rules = db.query(AutomationRule).all()
    result = []
    for r in rules:
        result.append({
            "id": r.id,
            "name": r.name,
            "configuration": json.loads(r.configuration) if r.configuration else {},
            "enabled": r.enabled,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        })
    return result


class RuleUpdate(BaseModel):
    enabled: bool | None = None
    configuration: dict | None = None


@router.put("/rules/{rule_id}")
def update_rule(rule_id: int, data: RuleUpdate, db: Session = Depends(get_db)):
    r = db.query(AutomationRule).filter(AutomationRule.id == rule_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Rule not found")

    if data.enabled is not None:
        r.enabled = data.enabled
    if data.configuration is not None:
        r.configuration = json.dumps(data.configuration)

    db.commit()
    return {"id": r.id, "name": r.name, "enabled": r.enabled}
