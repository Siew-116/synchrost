"""Customer message drafts router."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models import MessageDraft, Order, Customer, User, MessageStatus
from app.schemas import MessageDraftCreate, MessageDraftResponse
from app.utils.auth import get_current_user
from datetime import datetime

router = APIRouter(prefix="/api/messages", tags=["messages"])

# Template definitions with required variables
TEMPLATES = {
    "order_confirmation": {
        "en": "Hi {customer_name}, your order {order_number} has been confirmed! Total: RM {total}. Please proceed with payment to reserve your items.",
        "ms": "Hi {customer_name}, pesanan anda {order_number} telah disahkan! Jumlah: RM {total}. Sila buat pembayaran untuk menempah item anda.",
    },
    "payment_reminder": {
        "en": "Hi {customer_name}, this is a friendly reminder that your order {order_number} has a balance of RM {balance_due}. Please complete payment to proceed.",
        "ms": "Hi {customer_name}, peringatan mesra bahawa pesanan anda {order_number} mempunyai baki RM {balance_due}. Sila lengkapkan pembayaran untuk meneruskan.",
    },
    "purchase_proof": {
        "en": "Hi {customer_name}, I've placed the supplier order for your items in {order_number}. Attached is the purchase proof. ETA: {eta}.",
        "ms": "Hi {customer_name}, saya telah membuat pesanan pembekal untuk item anda dalam {order_number}. Bukti pembelian dilampirkan. Anggaran tiba: {eta}.",
    },
    "ems_sharing": {
        "en": "Hi {customer_name}, your order {order_number} is part of a group order with EMS sharing. Your EMS share: RM {ems_share}.",
        "ms": "Hi {customer_name}, pesanan anda {order_number} adalah sebahagian daripada pesanan kumpulan dengan perkongsian EMS. Bahagian EMS anda: RM {ems_share}.",
    },
    "group_order_progress": {
        "en": "Hi {customer_name}, update on group order {group_id}: {progress_update}. Your items: {items_summary}.",
        "ms": "Hi {customer_name}, kemas kini pesanan kumpulan {group_id}: {progress_update}. Item anda: {items_summary}.",
    },
    "parcel_arrival": {
        "en": "Hi {customer_name}, your parcel for order {order_number} has arrived! I'll start packing and notify you when it's shipped.",
        "ms": "Hi {customer_name}, parcel anda untuk pesanan {order_number} telah tiba! Saya akan mula membungkus dan maklumkan anda apabila dihantar.",
    },
    "packaging_notice": {
        "en": "Hi {customer_name}, your order {order_number} is being packed now! Expected dispatch: {dispatch_date}.",
        "ms": "Hi {customer_name}, pesanan anda {order_number} sedang dibungkus sekarang! Anggaran penghantaran: {dispatch_date}.",
    },
    "postage_scheduling": {
        "en": "Hi {customer_name}, your order {order_number} is scheduled for postage on {dispatch_date} via {shipping_service}.",
        "ms": "Hi {customer_name}, pesanan anda {order_number} dijadualkan untuk pos pada {dispatch_date} melalui {shipping_service}.",
    },
    "tracking_update": {
        "en": "Hi {customer_name}, your order {order_number} has been dispatched! Tracking number: {tracking_number}. Service: {shipping_service}.",
        "ms": "Hi {customer_name}, pesanan anda {order_number} telah dihantar! Nombor penjejakan: {tracking_number}. Perkhidmatan: {shipping_service}.",
    },
    "blackout_announcement": {
        "en": "Hi {customer_name}, please note there will be a shipping blackout from {blackout_start} to {blackout_end}. Orders during this period will be dispatched after.",
        "ms": "Hi {customer_name}, sila ambil perhatian akan berlaku hitam penghantaran dari {blackout_start} hingga {blackout_end}. Pesanan tempoh ini akan dihantar selepas itu.",
    },
    "shipping_delay": {
        "en": "Hi {customer_name}, unfortunately there's a shipping delay for your order {order_number}. New expected dispatch: {new_dispatch_date}. Reason: {delay_reason}.",
        "ms": "Hi {customer_name}, malangnya terdapat kelewatan penghantaran untuk pesanan anda {order_number}. Anggaran penghantaran baru: {new_dispatch_date}. Sebab: {delay_reason}.",
    },
    "cancellation": {
        "en": "Hi {customer_name}, your order {order_number} has been cancelled. {cancellation_reason}. Refund amount: RM {refund_amount}.",
        "ms": "Hi {customer_name}, pesanan anda {order_number} telah dibatalkan. {cancellation_reason}. Amaun bayaran balik: RM {refund_amount}.",
    },
    "missing_item": {
        "en": "Hi {customer_name}, we found that item(s) from your order {order_number} are missing from the supplier parcel. Missing: {missing_items}. Options: {options}.",
        "ms": "Hi {customer_name}, kami mendapati item dari pesanan anda {order_number} hilang dari parcel pembekal. Hilang: {missing_items}. Pilihan: {options}.",
    },
    "defective_item": {
        "en": "Hi {customer_name}, we found a defective item in your order {order_number}. Item: {defective_item}. Options: replacement or refund of RM {refund_amount}.",
        "ms": "Hi {customer_name}, kami mendapati item rosak dalam pesanan anda {order_number}. Item: {defective_item}. Pilihan: penggantian atau bayaran balik RM {refund_amount}.",
    },
    "refund": {
        "en": "Hi {customer_name}, a refund of RM {refund_amount} has been processed for your order {order_number}. Reason: {refund_reason}.",
        "ms": "Hi {customer_name}, bayaran balik RM {refund_amount} telah diproses untuk pesanan anda {order_number}. Sebab: {refund_reason}.",
    },
    "replacement": {
        "en": "Hi {customer_name}, a replacement for {defective_item} in order {order_number} is being prepared. Expected dispatch: {dispatch_date}.",
        "ms": "Hi {customer_name}, penggantian untuk {defective_item} dalam pesanan {order_number} sedang disediakan. Anggaran penghantaran: {dispatch_date}.",
    },
}


def render_template(template_type: str, language: str, context: dict) -> str:
    """Render a message template with context variables."""
    template_set = TEMPLATES.get(template_type, {})
    template = template_set.get(language, template_set.get("en", ""))
    if not template:
        return f"[Template '{template_type}' not found]"
    try:
        return template.format(**context)
    except KeyError as e:
        return f"[Missing variable: {e}] " + template


@router.get("/", response_model=List[MessageDraftResponse])
def list_messages(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(MessageDraft).filter(
        MessageDraft.user_id == current_user.id
    ).order_by(MessageDraft.created_at.desc()).all()


@router.post("/", response_model=MessageDraftResponse)
def create_message(
    msg: MessageDraftCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Build context from order/customer data
    context = {}
    order = None
    customer = None

    if msg.order_id:
        order = db.query(Order).filter(
            Order.id == msg.order_id,
            Order.user_id == current_user.id,
        ).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        context.update({
            "order_number": order.order_number,
            "total": str(order.total),
            "balance_due": str(order.balance_due),
            "tracking_number": order.tracking_number or "[pending]",
            "shipping_service": order.shipping_service or "[TBD]",
            "dispatch_date": order.promised_dispatch_date.isoformat() if order.promised_dispatch_date else "[TBD]",
        })

    if msg.customer_id:
        customer = db.query(Customer).filter(
            Customer.id == msg.customer_id,
            Customer.user_id == current_user.id,
        ).first()
    elif order:
        customer = db.query(Customer).filter(Customer.id == order.customer_id).first()

    if customer:
        context["customer_name"] = customer.name

    body = render_template(msg.template_type, msg.language, context)

    db_msg = MessageDraft(
        user_id=current_user.id,
        order_id=msg.order_id,
        customer_id=customer.id if customer else msg.customer_id,
        template_type=msg.template_type,
        language=msg.language,
        subject=f"{msg.template_type.replace('_', ' ').title()} - {order.order_number if order else ''}",
        body=body,
        status=MessageStatus.DRAFTED,
    )
    db.add(db_msg)
    db.commit()
    db.refresh(db_msg)
    return db_msg


@router.put("/{msg_id}/approve", response_model=MessageDraftResponse)
def approve_message(
    msg_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    msg = db.query(MessageDraft).filter(
        MessageDraft.id == msg_id,
        MessageDraft.user_id == current_user.id,
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    if msg.status != MessageStatus.DRAFTED:
        raise HTTPException(status_code=400, detail=f"Cannot approve message with status: {msg.status.value}")

    # Check for unfilled variables
    if "[" in msg.body and "]" in msg.body:
        raise HTTPException(status_code=400, detail="Message contains unfilled variables. Please edit before approving.")

    msg.status = MessageStatus.AWAITING_APPROVAL
    db.commit()
    db.refresh(msg)
    return msg


@router.put("/{msg_id}/mark-sent", response_model=MessageDraftResponse)
def mark_message_sent(
    msg_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    msg = db.query(MessageDraft).filter(
        MessageDraft.id == msg_id,
        MessageDraft.user_id == current_user.id,
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")

    if msg.status != MessageStatus.AWAITING_APPROVAL and msg.status != MessageStatus.APPROVED:
        raise HTTPException(status_code=400, detail=f"Message must be approved before marking as sent. Current status: {msg.status.value}")

    msg.status = MessageStatus.EXECUTED
    msg.executed_at = datetime.utcnow()
    db.commit()
    db.refresh(msg)
    return msg


@router.delete("/{msg_id}")
def delete_message(
    msg_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    msg = db.query(MessageDraft).filter(
        MessageDraft.id == msg_id,
        MessageDraft.user_id == current_user.id,
    ).first()
    if not msg:
        raise HTTPException(status_code=404, detail="Message not found")
    db.delete(msg)
    db.commit()
    return {"detail": "Message deleted"}
