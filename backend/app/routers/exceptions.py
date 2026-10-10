"""Exceptions (Approvals) API."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.database import get_db, Exception_, Order

router = APIRouter(prefix="/api/exceptions", tags=["exceptions"])


@router.get("")
def list_exceptions(status: str = "open", db: Session = Depends(get_db)):
    query = db.query(Exception_)
    if status:
        query = query.filter(Exception_.status == status)
    excs = query.order_by(Exception_.created_at.desc()).all()
    result = []
    for e in excs:
        order_info = None
        if e.order_id:
            o = db.query(Order).filter(Order.id == e.order_id).first()
            if o:
                order_info = {
                    "id": o.id,
                    "customer": o.customer.display_name,
                    "status": o.status,
                    "payment_status": o.payment_status,
                    "total_amount": o.total_amount,
                }
        result.append({
            "id": e.id,
            "type": e.type,
            "order_id": e.order_id,
            "order": order_info,
            "description": e.description,
            "recommended_action": e.recommended_action,
            "status": e.status,
            "resolved_by": e.resolved_by,
            "resolved_at": e.resolved_at.isoformat() if e.resolved_at else None,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        })
    return result


class ExceptionResolve(BaseModel):
    action: str  # approved, rejected, more_info
    admin_name: str = "admin"


@router.post("/{exception_id}/resolve")
def resolve_exception(exception_id: int, data: ExceptionResolve, db: Session = Depends(get_db)):
    e = db.query(Exception_).filter(Exception_.id == exception_id).first()
    if not e:
        raise HTTPException(status_code=404, detail="Exception not found")

    e.status = data.action
    e.resolved_by = data.admin_name
    e.resolved_at = datetime.now(timezone.utc)
    db.commit()

    # If approved and has a late order, activate it
    if data.action == "approved" and e.type == "late_order" and e.order_id:
        order = db.query(Order).filter(Order.id == e.order_id).first()
        if order and order.status == "draft":
            order.status = "pending_payment"
            order.updated_at = datetime.now(timezone.utc)
            db.commit()

    return {"id": e.id, "status": e.status}
