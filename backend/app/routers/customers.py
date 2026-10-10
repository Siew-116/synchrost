"""Customers API."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db, Customer, Order, Conversation

router = APIRouter(prefix="/api/customers", tags=["customers"])


@router.get("")
def list_customers(db: Session = Depends(get_db)):
    customers = db.query(Customer).all()
    result = []
    for c in customers:
        order_count = db.query(Order).filter(Order.customer_id == c.id).count()
        result.append({
            "id": c.id,
            "display_name": c.display_name,
            "telegram_user_id": c.telegram_user_id,
            "telegram_username": c.telegram_username,
            "order_count": order_count,
            "created_at": c.created_at.isoformat() if c.created_at else None,
        })
    return result


@router.get("/{customer_id}")
def get_customer(customer_id: int, db: Session = Depends(get_db)):
    c = db.query(Customer).filter(Customer.id == customer_id).first()
    if not c:
        raise HTTPException(status_code=404, detail="Customer not found")

    orders = db.query(Order).filter(Order.customer_id == c.id).all()
    order_list = [{
        "id": o.id,
        "status": o.status,
        "payment_status": o.payment_status,
        "total_amount": o.total_amount,
        "items": [{"variant": oi.variant.attributes, "quantity": oi.quantity} for oi in o.items],
    } for o in orders]

    conversations = db.query(Conversation).filter(Conversation.customer_id == c.id).all()
    conv_list = [{
        "id": conv.id,
        "platform": conv.platform,
        "status": conv.status,
    } for conv in conversations]

    return {
        "id": c.id,
        "display_name": c.display_name,
        "telegram_user_id": c.telegram_user_id,
        "telegram_username": c.telegram_username,
        "orders": order_list,
        "conversations": conv_list,
        "created_at": c.created_at.isoformat() if c.created_at else None,
    }
