"""Orders API."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.database import get_db, Order, OrderItem, Payment, Customer, ProductVariant

router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.get("")
def list_orders(
    campaign_id: int | None = None,
    status: str | None = None,
    payment_status: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Order)
    if campaign_id:
        query = query.filter(Order.campaign_id == campaign_id)
    if status:
        query = query.filter(Order.status == status)
    if payment_status:
        query = query.filter(Order.payment_status == payment_status)
    if search:
        query = query.join(Order.customer).filter(Customer.display_name.ilike(f"%{search}%"))

    orders = query.order_by(Order.created_at.desc()).all()
    result = []
    for o in orders:
        items = []
        for oi in o.items:
            items.append({
                "variant": oi.variant.attributes,
                "quantity": oi.quantity,
                "unit_price": oi.unit_price,
            })
        result.append({
            "id": o.id,
            "customer": o.customer.display_name,
            "customer_id": o.customer_id,
            "campaign_id": o.campaign_id,
            "status": o.status,
            "payment_status": o.payment_status,
            "fulfilment_status": o.fulfilment_status,
            "total_amount": o.total_amount,
            "items": items,
            "created_at": o.created_at.isoformat() if o.created_at else None,
            "updated_at": o.updated_at.isoformat() if o.updated_at else None,
        })
    return result


@router.get("/{order_id}")
def get_order(order_id: int, db: Session = Depends(get_db)):
    o = db.query(Order).filter(Order.id == order_id).first()
    if not o:
        raise HTTPException(status_code=404, detail="Order not found")

    items = [{
        "variant": oi.variant.attributes,
        "quantity": oi.quantity,
        "unit_price": oi.unit_price,
    } for oi in o.items]

    payments = [{
        "id": p.id,
        "amount": p.amount,
        "status": p.status,
        "submitted_at": p.submitted_at.isoformat() if p.submitted_at else None,
        "verified_at": p.verified_at.isoformat() if p.verified_at else None,
        "verification_method": p.verification_method,
    } for p in o.payments]

    messages = [{
        "id": m.id,
        "sender_type": m.sender_type,
        "content": m.content,
        "intent": m.intent,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    } for m in o.messages]

    return {
        "id": o.id,
        "customer": o.customer.display_name,
        "customer_id": o.customer_id,
        "campaign_id": o.campaign_id,
        "status": o.status,
        "payment_status": o.payment_status,
        "fulfilment_status": o.fulfilment_status,
        "total_amount": o.total_amount,
        "items": items,
        "payments": payments,
        "messages": messages,
        "created_at": o.created_at.isoformat() if o.created_at else None,
        "updated_at": o.updated_at.isoformat() if o.updated_at else None,
    }


class OrderUpdate(BaseModel):
    status: str | None = None
    payment_status: str | None = None
    fulfilment_status: str | None = None


@router.put("/{order_id}")
def update_order(order_id: int, data: OrderUpdate, db: Session = Depends(get_db)):
    from app.services.agent import AgentTools
    tools = AgentTools(db)
    changes = {k: v for k, v in data.dict().items() if v is not None}
    result = tools.update_order(order_id, changes)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result
