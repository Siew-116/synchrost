"""Finance router with proper realised vs estimated profit boundary."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from decimal import Decimal
from app.database import get_db
from app.models import FinanceTransaction, Order, OrderStatus, User
from app.schemas import FinanceSummary, FinanceTransactionResponse
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/finance", tags=["finance"])

# State sets for profit boundary (per business rules §7)
REALISED_STATES = {OrderStatus.DELIVERED}
ESTIMATED_STATES = {OrderStatus.PAID, OrderStatus.PACKED, OrderStatus.DISPATCHED}
OUTSTANDING_STATES = {OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PAID,
                      OrderStatus.PACKED, OrderStatus.DISPATCHED, OrderStatus.EXCEPTION}


@router.get("/transactions", response_model=List[FinanceTransactionResponse])
def list_transactions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(FinanceTransaction).filter(
        FinanceTransaction.user_id == current_user.id
    ).order_by(FinanceTransaction.transaction_date.desc()).all()


@router.get("/summary", response_model=FinanceSummary)
def get_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    orders = db.query(Order).filter(
        Order.user_id == current_user.id,
    ).all()

    # --- Realised (delivered orders only) ---
    realised_orders = [o for o in orders if o.status in REALISED_STATES]
    r_gross = sum((o.subtotal for o in realised_orders), Decimal("0"))
    r_discounts = sum((o.discount for o in realised_orders), Decimal("0"))
    r_shipping_charged = sum((o.shipping_charged for o in realised_orders), Decimal("0"))
    r_product_cost = Decimal("0")
    r_shipping_expenses = Decimal("0")
    for o in realised_orders:
        for item in o.order_items:
            if item.product and item.product.cost_price:
                r_product_cost += item.product.cost_price * item.quantity
        if o.shipping_cost:
            r_shipping_expenses += o.shipping_cost

    # Refunds (from cancelled orders that had payments)
    cancelled_with_payment = [o for o in orders if o.status == OrderStatus.CANCELLED and o.amount_paid > 0]
    refunds = sum((o.amount_paid for o in cancelled_with_payment), Decimal("0"))

    # --- Estimated (paid/packed/dispatched — payment certainty) ---
    estimated_orders = [o for o in orders if o.status in ESTIMATED_STATES]
    e_gross = sum((o.subtotal for o in estimated_orders), Decimal("0"))
    e_discounts = sum((o.discount for o in estimated_orders), Decimal("0"))
    e_product_cost = Decimal("0")
    e_shipping_charged = sum((o.shipping_charged for o in estimated_orders), Decimal("0"))
    e_shipping_expenses = Decimal("0")
    for o in estimated_orders:
        for item in o.order_items:
            if item.product and item.product.cost_price:
                e_product_cost += item.product.cost_price * item.quantity
        if o.shipping_cost:
            e_shipping_expenses += o.shipping_cost

    # --- Outstanding payments (orders with balance due, not cancelled/delivered) ---
    outstanding_orders = [o for o in orders if o.status in OUTSTANDING_STATES and o.balance_due and o.balance_due > 0]
    outstanding_payments = sum((o.balance_due for o in outstanding_orders), Decimal("0"))

    # --- Aggregates ---
    gross_sales = r_gross + e_gross
    discounts = r_discounts + e_discounts
    shipping_charged = r_shipping_charged + e_shipping_charged
    product_cost = r_product_cost + e_product_cost
    shipping_expenses = r_shipping_expenses + e_shipping_expenses

    net_sales = gross_sales - discounts - refunds

    # Realised profit: only from delivered orders
    realised_profit = (r_gross - r_discounts - refunds) + r_shipping_charged - r_product_cost - r_shipping_expenses

    # Estimated profit: realised + expected from in-progress orders
    estimated_profit = realised_profit + (e_gross - e_discounts) + e_shipping_charged - e_product_cost - e_shipping_expenses

    return FinanceSummary(
        gross_sales=gross_sales,
        discounts=discounts,
        refunds=refunds,
        net_sales=net_sales,
        product_cost=product_cost,
        shipping_charged=shipping_charged,
        shipping_expenses=shipping_expenses,
        other_expenses=Decimal("0"),
        realized_profit=realised_profit,
        estimated_profit=estimated_profit,
        outstanding_payments=outstanding_payments,
    )
