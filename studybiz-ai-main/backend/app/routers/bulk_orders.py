"""Bulk/Group orders router with two-phase cost allocation."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from decimal import Decimal, ROUND_HALF_EVEN
from app.database import get_db
from app.models import BulkOrder, Order, User, Supplier
from app.schemas import (
    BulkOrderCreate, BulkOrderUpdate, BulkOrderResponse
)
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/bulk-orders", tags=["bulk-orders"])


def quantize(amount: Decimal) -> Decimal:
    """Quantize to 2 decimal places (MYR sen)."""
    return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)


def compute_item_subtotals(participant_orders: List[Order]) -> Dict[int, Decimal]:
    """
    Phase 1: Compute each participant's item subtotal (method-independent).
    Returns dict mapping participant identifier (customer_id) to subtotal.
    """
    subtotals: Dict[int, Decimal] = {}
    for order in participant_orders:
        key = order.customer_id
        subtotal = sum(
            (item.total_price for item in order.order_items),
            Decimal("0")
        )
        subtotals[key] = subtotals.get(key, Decimal("0")) + quantize(subtotal)
    return subtotals


def allocate_shared_costs(
    subtotals: Dict[int, Decimal],
    domestic_shipping: Decimal,
    international_shipping: Decimal,
    ems_fee: Decimal,
    other_shared: Decimal,
    method: str = "equal",
    manual_overrides: Optional[Dict[int, Dict[str, Decimal]]] = None,
) -> Dict[int, Dict[str, Decimal]]:
    """
    Phase 2: Allocate shared costs to participants (method-specific).

    Methods:
    - A (equal): Split equally across all participants
    - B (by_value): Split proportionally to item subtotal
    - C (by_weight): Split proportionally to item quantity (not implemented — needs weight data)
    - D (manual): Use manual_overrides dict

    Returns dict mapping participant_id -> {domestic, international, ems, other, shared_total}
    """
    participants = sorted(subtotals.keys())
    n = len(participants)
    if n == 0:
        return {}

    shared_costs = {
        "domestic": quantize(domestic_shipping),
        "international": quantize(international_shipping),
        "ems": quantize(ems_fee),
        "other": quantize(other_shared),
    }
    total_shared = sum(shared_costs.values())

    result: Dict[int, Dict[str, Decimal]] = {}

    if method == "D" and manual_overrides:
        # Manual allocation — use provided values directly
        for pid in participants:
            overrides = manual_overrides.get(pid, {})
            result[pid] = {
                "domestic": quantize(overrides.get("domestic", Decimal("0"))),
                "international": quantize(overrides.get("international", Decimal("0"))),
                "ems": quantize(overrides.get("ems", Decimal("0"))),
                "other": quantize(overrides.get("other", Decimal("0"))),
            }
            result[pid]["shared_total"] = quantize(sum(result[pid].values()))

        # Method D validation: warn if manual overrides diverge from expected total
        manual_allocated = sum((r["shared_total"] for r in result.values()), Decimal("0"))
        manual_balance_check = quantize(total_shared - manual_allocated)
        if manual_balance_check != 0:
            # Emit warning but do not block — operator may intentionally absorb difference
            result["_manual_balance_check"] = {
                "status": "warning",
                "message": f"Manual overrides diverge by RM {manual_balance_check}. "
                           f"Expected: {total_shared}, allocated: {manual_allocated}.",
                "expected_total": str(total_shared),
                "allocated_total": str(manual_allocated),
                "difference": str(manual_balance_check),
            }

    elif method == "B":
        # By value — proportional to subtotal
        grand_subtotal = sum(subtotals.values())
        if grand_subtotal == 0:
            # Fallback to equal if all subtotals are zero
            method = "equal"
        else:
            for cost_name, cost_amount in shared_costs.items():
                allocated_so_far = Decimal("0")
                for i, pid in enumerate(participants):
                    if i == n - 1:
                        # Last participant gets residual
                        share = quantize(cost_amount - allocated_so_far)
                    else:
                        ratio = subtotals[pid] / grand_subtotal
                        share = quantize(cost_amount * ratio)
                        allocated_so_far += share

                    if pid not in result:
                        result[pid] = {"domestic": Decimal("0"), "international": Decimal("0"),
                                       "ems": Decimal("0"), "other": Decimal("0")}
                    result[pid][cost_name] = share

            for pid in participants:
                result[pid]["shared_total"] = quantize(
                    result[pid]["domestic"] + result[pid]["international"] +
                    result[pid]["ems"] + result[pid]["other"]
                )

    if method == "equal" or not result:
        # Equal split
        for cost_name, cost_amount in shared_costs.items():
            allocated_so_far = Decimal("0")
            for i, pid in enumerate(participants):
                if i == n - 1:
                    share = quantize(cost_amount - allocated_so_far)
                else:
                    share = quantize(cost_amount / n)
                    allocated_so_far += share

                if pid not in result:
                    result[pid] = {"domestic": Decimal("0"), "international": Decimal("0"),
                                   "ems": Decimal("0"), "other": Decimal("0")}
                result[pid][cost_name] = share

        for pid in participants:
            result[pid]["shared_total"] = quantize(
                result[pid]["domestic"] + result[pid]["international"] +
                result[pid]["ems"] + result[pid]["other"]
            )

    # Reconciliation invariant: Σ(shared_totals) == total_shared
    allocated_total = sum((r["shared_total"] for r in result.values()), Decimal("0"))
    assert quantize(allocated_total) == total_shared, \
        f"Allocation reconciliation failed: {allocated_total} != {total_shared}"

    return result


@router.get("/", response_model=List[BulkOrderResponse])
def list_bulk_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return db.query(BulkOrder).filter(BulkOrder.user_id == current_user.id).order_by(
        BulkOrder.created_at.desc()
    ).all()


@router.post("/", response_model=BulkOrderResponse)
def create_bulk_order(
    bulk: BulkOrderCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    db_bulk = BulkOrder(**bulk.model_dump(), user_id=current_user.id)
    db.add(db_bulk)
    db.commit()
    db.refresh(db_bulk)
    return db_bulk


@router.get("/{bulk_id}", response_model=BulkOrderResponse)
def get_bulk_order(
    bulk_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bulk = db.query(BulkOrder).filter(
        BulkOrder.id == bulk_id,
        BulkOrder.user_id == current_user.id,
    ).first()
    if not bulk:
        raise HTTPException(status_code=404, detail="Bulk order not found")
    return bulk


@router.put("/{bulk_id}", response_model=BulkOrderResponse)
def update_bulk_order(
    bulk_id: int,
    bulk_in: BulkOrderUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bulk = db.query(BulkOrder).filter(
        BulkOrder.id == bulk_id,
        BulkOrder.user_id == current_user.id,
    ).first()
    if not bulk:
        raise HTTPException(status_code=404, detail="Bulk order not found")

    for field, value in bulk_in.model_dump(exclude_unset=True).items():
        setattr(bulk, field, value)

    db.commit()
    db.refresh(bulk)
    return bulk


@router.get("/{bulk_id}/allocations")
def get_allocations(
    bulk_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Calculate and return cost allocations for a bulk order's participants."""
    bulk = db.query(BulkOrder).filter(
        BulkOrder.id == bulk_id,
        BulkOrder.user_id == current_user.id,
    ).first()
    if not bulk:
        raise HTTPException(status_code=404, detail="Bulk order not found")

    # Get all orders linked to this bulk order
    participant_orders = db.query(Order).filter(
        Order.bulk_order_id == bulk_id,
        Order.user_id == current_user.id,
    ).all()

    if not participant_orders:
        return {"participants": [], "grand_subtotal": "0.00", "total_shared": "0.00"}

    # Phase 1: Item subtotals
    subtotals = compute_item_subtotals(participant_orders)

    # Phase 2: Shared cost allocation
    allocations = allocate_shared_costs(
        subtotals=subtotals,
        domestic_shipping=bulk.domestic_shipping_cost,
        international_shipping=bulk.international_shipping_cost,
        ems_fee=bulk.ems_fee,
        other_shared=bulk.other_shared_costs,
        method=bulk.cost_allocation_method,
    )

    # Build response
    participants = []
    for customer_id, subtotal in subtotals.items():
        alloc = allocations.get(customer_id, {})
        total_owed = quantize(subtotal + alloc.get("shared_total", Decimal("0")))
        participants.append({
            "customer_id": customer_id,
            "item_subtotal": str(subtotal),
            "domestic_share": str(alloc.get("domestic", Decimal("0"))),
            "international_share": str(alloc.get("international", Decimal("0"))),
            "ems_share": str(alloc.get("ems", Decimal("0"))),
            "other_share": str(alloc.get("other", Decimal("0"))),
            "shared_total": str(alloc.get("shared_total", Decimal("0"))),
            "total_owed": str(total_owed),
        })

    grand_subtotal = sum(subtotals.values())
    total_shared = (
        bulk.domestic_shipping_cost + bulk.international_shipping_cost +
        bulk.ems_fee + bulk.other_shared_costs
    )

    return {
        "participants": participants,
        "grand_subtotal": str(quantize(grand_subtotal)),
        "total_shared": str(quantize(total_shared)),
        "grand_total": str(quantize(grand_subtotal + total_shared)),
        "method": bulk.cost_allocation_method,
    }


@router.delete("/{bulk_id}")
def delete_bulk_order(
    bulk_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    bulk = db.query(BulkOrder).filter(
        BulkOrder.id == bulk_id,
        BulkOrder.user_id == current_user.id,
    ).first()
    if not bulk:
        raise HTTPException(status_code=404, detail="Bulk order not found")
    db.delete(bulk)
    db.commit()
    return {"detail": "Bulk order deleted"}
