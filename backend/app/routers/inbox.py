"""Customer Inbox API."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db, Conversation, Message, Customer, Order

router = APIRouter(prefix="/api/inbox", tags=["inbox"])


@router.get("/conversations")
def list_conversations(
    status: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Conversation)
    if status:
        query = query.filter(Conversation.status == status)

    convs = query.order_by(Conversation.id.desc()).all()
    result = []
    for c in convs:
        last_msg = db.query(Message).filter(Message.conversation_id == c.id).order_by(Message.created_at.desc()).first()
        result.append({
            "id": c.id,
            "customer": c.customer.display_name,
            "customer_id": c.customer_id,
            "platform": c.platform,
            "status": c.status,
            "last_message": last_msg.content[:100] if last_msg else "",
            "last_intent": last_msg.intent if last_msg else None,
            "last_timestamp": last_msg.created_at.isoformat() if last_msg and last_msg.created_at else None,
        })
    return result


@router.get("/conversations/{conv_id}")
def get_conversation(conv_id: int, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")

    messages = db.query(Message).filter(Message.conversation_id == conv.id).order_by(Message.created_at).all()
    msg_list = [{
        "id": m.id,
        "sender_type": m.sender_type,
        "content": m.content,
        "intent": m.intent,
        "order_id": m.order_id,
        "created_at": m.created_at.isoformat() if m.created_at else None,
    } for m in messages]

    # Related orders
    customer_orders = db.query(Order).filter(Order.customer_id == conv.customer_id).all()
    related_orders = [{
        "id": o.id,
        "status": o.status,
        "payment_status": o.payment_status,
        "total_amount": o.total_amount,
    } for o in customer_orders]

    return {
        "id": conv.id,
        "customer": conv.customer.display_name,
        "customer_id": conv.customer_id,
        "platform": conv.platform,
        "status": conv.status,
        "messages": msg_list,
        "related_orders": related_orders,
    }


@router.post("/conversations/{conv_id}/resolve")
def resolve_conversation(conv_id: int, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv.status = "resolved"
    db.commit()
    return {"id": conv.id, "status": "resolved"}


@router.post("/conversations/{conv_id}/escalate")
def escalate_conversation(conv_id: int, db: Session = Depends(get_db)):
    conv = db.query(Conversation).filter(Conversation.id == conv_id).first()
    if not conv:
        raise HTTPException(status_code=404, detail="Conversation not found")
    conv.status = "escalated"
    db.commit()
    return {"id": conv.id, "status": "escalated"}
