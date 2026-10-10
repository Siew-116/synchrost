"""Orders router with state machine and financial tracking."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from decimal import Decimal
from app.database import get_db
from app.models import (
    Order, OrderItem, OrderStatus, OrderStatusHistory, Product,
    Customer, StockMovement, User, FinanceTransaction
)
from app.schemas import (
    OrderCreate, OrderUpdate, OrderResponse, OrderItemResponse
)
from app.utils.auth import get_current_user
from datetime import datetime
import secrets

router = APIRouter(prefix="/api/orders", tags=["orders"])

# Valid state transitions (from business rules)
VALID_TRANSITIONS = {
    OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.CANCELLED},
    OrderStatus.CONFIRMED: {OrderStatus.PAID, OrderStatus.CANCELLED, OrderStatus.EXCEPTION},
    OrderStatus.PAID: {OrderStatus.PACKED, OrderStatus.EXCEPTION, OrderStatus.CANCELLED},
    OrderStatus.PACKED: {OrderStatus.DISPATCHED, OrderStatus.EXCEPTION},
    OrderStatus.DISPATCHED: {OrderStatus.DELIVERED, OrderStatus.EXCEPTION},
    OrderStatus.DELIVERED: set(),  # Terminal state
    OrderStatus.CANCELLED: {OrderStatus.PENDING},  # Allow reopening
    OrderStatus.EXCEPTION: {OrderStatus.PAID, OrderStatus.PACKED, OrderStatus.CANCELLED, OrderStatus.DISPATCHED},
}


def generate_order_number(db: Session, user_id: int) -> str:
    """Generate unique order number: SB-YYYYMMDD-XXXX"""
    today = datetime.utcnow().strftime("%Y%m%d")
    prefix = f"SB-{today}-"
    count = db.query(Order).filter(
        Order.user_id == user_id,
        Order.order_number.like(f"{prefix}%")
    ).count()
    return f"{prefix}{count + 1:04d}"


@router.get("/", response_model=List[OrderResponse])
def list_orders(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Order).filter(Order.user_id == current_user.id)
    if status_filter:
        try:
            status_enum = OrderStatus(status_filter)
            q = q.filter(Order.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status_filter}")
    return q.order_by(Order.created_at.desc()).all()


@router.post("/", response_model=OrderResponse)
def create_order(
    order: OrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Validate customer exists
    customer = db.query(Customer).filter(
        Customer.id == order.customer_id,
        Customer.user_id == current_user.id,
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Validate products and calculate subtotal
    subtotal = Decimal("0")
    order_items_data = []

    for item in order.order_items:
        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.user_id == current_user.id,
        ).first()
        if not product:
            raise HTTPException(status_code=404, detail=f"Product {item.product_id} not found")

        unit_price = item.unit_price if item.unit_price else product.selling_price
        total_price = unit_price * item.quantity
        subtotal += total_price

        order_items_data.append({
            "product": product,
            "quantity": item.quantity,
            "unit_price": unit_price,
            "total_price": total_price,
        })

    # Calculate totals
    total = subtotal - order.discount + order.shipping_charged
    balance_due = total  # New order, nothing paid yet

    # Create order
    db_order = Order(
        user_id=current_user.id,
        customer_id=order.customer_id,
        order_number=generate_order_number(db, current_user.id),
        status=OrderStatus.PENDING,
        subtotal=subtotal,
        discount=order.discount,
        shipping_charged=order.shipping_charged,
        total=total,
        amount_paid=Decimal("0"),
        balance_due=balance_due,
        promised_dispatch_date=order.promised_dispatch_date,
        packing_requirements=order.packing_requirements,
        estimated_packing_minutes=order.estimated_packing_minutes,
        notes=order.notes,
        bulk_order_id=order.bulk_order_id,
    )
    db.add(db_order)
    db.flush()

    # Create order items and reserve stock
    for item_data in order_items_data:
        db_item = OrderItem(
            order_id=db_order.id,
            product_id=item_data["product"].id,
            quantity=item_data["quantity"],
            unit_price=item_data["unit_price"],
            total_price=item_data["total_price"],
        )
        db.add(db_item)

        # Reserve stock
        product = item_data["product"]
        if not product.is_preorder:
            if product.available_stock < item_data["quantity"]:
                raise HTTPException(
                    status_code=400,
                    detail=f"Insufficient stock for {product.name}. Available: {product.available_stock}, requested: {item_data['quantity']}"
                )
            product.available_stock -= item_data["quantity"]
            product.reserved_stock += item_data["quantity"]

            # Record stock movement
            movement = StockMovement(
                product_id=product.id,
                movement_type="reserve",
                quantity_change=-item_data["quantity"],
                reference=db_order.order_number,
                notes=f"Reserved for order {db_order.order_number}",
            )
            db.add(movement)

    # Record status history
    history = OrderStatusHistory(
        order_id=db_order.id,
        from_status=None,
        to_status=OrderStatus.PENDING,
        note="Order created",
    )
    db.add(history)

    db.commit()
    db.refresh(db_order)
    return db_order


@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.put("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    order_in: OrderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # Handle status transition
    if order_in.status and order_in.status != order.status:
        new_status = order_in.status
        valid_targets = VALID_TRANSITIONS.get(order.status, set())
        if new_status not in valid_targets:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid transition: {order.status.value} -> {new_status.value}. Valid: {[s.value for s in valid_targets]}"
            )

        # Validate transition gates
        if new_status == OrderStatus.PACKED and order.amount_paid < order.total:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot pack order with unpaid balance. Amount paid: {order.amount_paid}, total: {order.total}"
            )
        if new_status == OrderStatus.DISPATCHED and not order.tracking_number and not order_in.tracking_number:
            raise HTTPException(
                status_code=400,
                detail="Cannot dispatch order without tracking number. Set tracking_number first."
            )

        # Record status history
        history = OrderStatusHistory(
            order_id=order.id,
            from_status=order.status,
            to_status=new_status,
            note=f"Status changed from {order.status.value} to {new_status.value}",
        )
        db.add(history)
        order.status = new_status

        # Handle financial implications of status change
        if new_status == OrderStatus.PAID:
            # Record payment in finance
            if order.amount_paid < order.total:
                order.amount_paid = order.total
                order.balance_due = Decimal("0")
                fin_tx = FinanceTransaction(
                    user_id=current_user.id,
                    transaction_type="sale",
                    amount=order.total,
                    reference_type="order",
                    reference_id=order.id,
                    description=f"Payment received for order {order.order_number}",
                )
                db.add(fin_tx)

        elif new_status == OrderStatus.CANCELLED:
            # Release reserved stock
            for item in order.order_items:
                product = db.query(Product).filter(Product.id == item.product_id).first()
                if product:
                    product.reserved_stock = max(0, product.reserved_stock - item.quantity)
                    product.available_stock += item.quantity
                    movement = StockMovement(
                        product_id=product.id,
                        movement_type="adjust",
                        quantity_change=item.quantity,
                        reference=order.order_number,
                        notes=f"Stock released due to order cancellation",
                    )
                    db.add(movement)

            # Record refund if payment was made
            if order.amount_paid > 0:
                fin_tx = FinanceTransaction(
                    user_id=current_user.id,
                    transaction_type="refund",
                    amount=-order.amount_paid,
                    reference_type="order",
                    reference_id=order.id,
                    description=f"Refund for cancelled order {order.order_number}",
                )
                db.add(fin_tx)

        elif new_status == OrderStatus.DISPATCHED and not order.tracking_number:
            order.warnings = (order.warnings or "") + " Dispatched without tracking number."

    # Update other fields
    for field, value in order_in.model_dump(exclude_unset=True).items():
        if field == "status":
            continue  # Already handled
        setattr(order, field, value)

    # Recalculate balance
    if order_in.amount_paid is not None:
        order.balance_due = order.total - order.amount_paid

    db.commit()
    db.refresh(order)
    return order


@router.get("/{order_id}/history")
def get_order_history(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    order = db.query(Order).filter(
        Order.id == order_id,
        Order.user_id == current_user.id,
    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    history = db.query(OrderStatusHistory).filter(
        OrderStatusHistory.order_id == order_id
    ).order_by(OrderStatusHistory.changed_at.asc()).all()

    return [
        {
            "id": h.id,
            "from_status": h.from_status.value if h.from_status else None,
            "to_status": h.to_status.value,
            "note": h.note,
            "changed_at": h.changed_at.isoformat() if h.changed_at else None,
        }
        for h in history
    ]
