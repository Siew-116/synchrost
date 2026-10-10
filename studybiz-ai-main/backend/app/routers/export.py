"""Excel masterlist export router."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List
from io import BytesIO
from app.database import get_db
from app.models import (
    Order, Customer, Product, BulkOrder, Supplier,
    BusinessException, FinanceTransaction, User, OrderStatus,
    PackagingBatch, ShippingBatch, PurchaseOrder
)
from app.utils.auth import get_current_user
from fastapi.responses import StreamingResponse
from openpyxl import Workbook
from openpyxl.utils import get_column_letter
from decimal import Decimal
from datetime import datetime

router = APIRouter(prefix="/api/export", tags=["export"])


@router.get("/masterlist")
def export_masterlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Generate a downloadable Excel masterlist with all business data."""
    wb = Workbook()

    # Remove default sheet
    wb.remove(wb.active)

    # --- Orders Sheet ---
    ws_orders = wb.create_sheet("Orders")
    orders = db.query(Order).filter(Order.user_id == current_user.id).all()
    headers = ["Order #", "Customer", "Status", "Subtotal", "Discount", "Shipping", "Total", "Paid", "Balance", "Dispatch Date", "Tracking #"]
    ws_orders.append(headers)
    for o in orders:
        customer = db.query(Customer).filter(Customer.id == o.customer_id).first()
        ws_orders.append([
            o.order_number,
            customer.name if customer else "",
            o.status.value,
            float(o.subtotal),
            float(o.discount),
            float(o.shipping_charged),
            float(o.total),
            float(o.amount_paid),
            float(o.balance_due),
            o.promised_dispatch_date.isoformat() if o.promised_dispatch_date else "",
            o.tracking_number or "",
        ])
    _auto_width(ws_orders)

    # --- Customers Sheet ---
    ws_cust = wb.create_sheet("Customers")
    customers = db.query(Customer).filter(Customer.user_id == current_user.id).all()
    ws_cust.append(["Name", "WhatsApp", "Instagram", "Email", "Address", "Notes", "Orders Count"])
    for c in customers:
        order_count = db.query(Order).filter(Order.customer_id == c.id).count()
        ws_cust.append([
            c.name, c.whatsapp_number or "", c.instagram_handle or "",
            c.email or "", c.address or "", c.notes or "", order_count
        ])
    _auto_width(ws_cust)

    # --- Payments Sheet ---
    ws_pay = wb.create_sheet("Payments")
    ws_pay.append(["Order #", "Customer", "Total", "Paid", "Balance", "Status"])
    for o in orders:
        customer = db.query(Customer).filter(Customer.id == o.customer_id).first()
        ws_pay.append([
            o.order_number, customer.name if customer else "",
            float(o.total), float(o.amount_paid), float(o.balance_due), o.status.value
        ])
    _auto_width(ws_pay)

    # --- Inventory Sheet ---
    ws_inv = wb.create_sheet("Inventory")
    products = db.query(Product).filter(Product.user_id == current_user.id).all()
    ws_inv.append(["Product", "SKU", "Category", "Selling Price", "Cost Price", "Available", "Reserved", "Incoming", "Low Stock"])
    for p in products:
        ws_inv.append([
            p.name, p.sku or "", p.category or "",
            float(p.selling_price), float(p.cost_price or 0),
            p.available_stock, p.reserved_stock, p.incoming_stock,
            "YES" if p.available_stock <= p.low_stock_threshold else "NO"
        ])
    _auto_width(ws_inv)

    # --- Bulk Orders Sheet ---
    ws_bulk = wb.create_sheet("Bulk Orders")
    bulk_orders = db.query(BulkOrder).filter(BulkOrder.user_id == current_user.id).all()
    ws_bulk.append(["Group ID", "Supplier", "Domestic Ship", "Intl Ship", "EMS Fee", "Other Costs", "Method", "Purchase Status", "Arrival Status", "Est. Arrival"])
    for b in bulk_orders:
        supplier = db.query(Supplier).filter(Supplier.id == b.supplier_id).first() if b.supplier_id else None
        ws_bulk.append([
            b.group_identifier, supplier.name if supplier else "",
            float(b.domestic_shipping_cost), float(b.international_shipping_cost),
            float(b.ems_fee), float(b.other_shared_costs),
            b.cost_allocation_method, b.purchase_status, b.arrival_status,
            b.estimated_arrival.isoformat() if b.estimated_arrival else ""
        ])
    _auto_width(ws_bulk)

    # --- Supplier Purchases Sheet ---
    ws_po = wb.create_sheet("Supplier Purchases")
    purchase_orders = db.query(PurchaseOrder).filter(PurchaseOrder.user_id == current_user.id).all()
    ws_po.append(["PO #", "Supplier", "Status", "Total Cost", "Est. Arrival", "Actual Arrival", "Tracking #"])
    for po in purchase_orders:
        supplier = db.query(Supplier).filter(Supplier.id == po.supplier_id).first()
        ws_po.append([
            po.po_number or "", supplier.name if supplier else "",
            po.status, float(po.total_cost),
            po.estimated_arrival.isoformat() if po.estimated_arrival else "",
            po.actual_arrival.isoformat() if po.actual_arrival else "",
            po.tracking_number or ""
        ])
    _auto_width(ws_po)

    # --- Shipping Sheet ---
    ws_ship = wb.create_sheet("Shipping")
    shipped_orders = [o for o in orders if o.tracking_number]
    ws_ship.append(["Order #", "Customer", "Dispatch Date", "Tracking #", "Shipping Service", "Shipping Cost"])
    for o in shipped_orders:
        customer = db.query(Customer).filter(Customer.id == o.customer_id).first()
        ws_ship.append([
            o.order_number, customer.name if customer else "",
            o.promised_dispatch_date.isoformat() if o.promised_dispatch_date else "",
            o.tracking_number or "", o.shipping_service or "",
            float(o.shipping_cost or 0)
        ])
    _auto_width(ws_ship)

    # --- Exceptions Sheet ---
    ws_exc = wb.create_sheet("Exceptions")
    exceptions = db.query(BusinessException).filter(BusinessException.user_id == current_user.id).all()
    ws_exc.append(["Type", "Status", "Title", "Description", "Amount", "Resolution", "Created"])
    for e in exceptions:
        ws_exc.append([
            e.exception_type.value, e.status.value, e.title,
            e.description or "", float(e.amount_involved),
            e.resolution or "",
            e.created_at.isoformat() if e.created_at else ""
        ])
    _auto_width(ws_exc)

    # --- Financial Summary Sheet ---
    ws_fin = wb.create_sheet("Financial Summary")
    from app.routers.finance import REALISED_STATES, ESTIMATED_STATES, OUTSTANDING_STATES
    realised_orders = [o for o in orders if o.status in REALISED_STATES]
    estimated_orders = [o for o in orders if o.status in ESTIMATED_STATES]

    r_gross = sum((o.subtotal for o in realised_orders), Decimal("0"))
    e_gross = sum((o.subtotal for o in estimated_orders), Decimal("0"))
    cancelled = [o for o in orders if o.status == OrderStatus.CANCELLED and o.amount_paid > 0]
    refunds = sum((o.amount_paid for o in cancelled), Decimal("0"))

    r_discounts = sum((o.discount for o in realised_orders), Decimal("0"))
    e_discounts = sum((o.discount for o in estimated_orders), Decimal("0"))
    r_shipping = sum((o.shipping_charged for o in realised_orders), Decimal("0"))
    e_shipping = sum((o.shipping_charged for o in estimated_orders), Decimal("0"))

    r_product_cost = Decimal("0")
    e_product_cost = Decimal("0")
    r_shipping_exp = Decimal("0")
    e_shipping_exp = Decimal("0")
    for o in realised_orders:
        for item in o.order_items:
            if item.product and item.product.cost_price:
                r_product_cost += item.product.cost_price * item.quantity
        if o.shipping_cost:
            r_shipping_exp += o.shipping_cost
    for o in estimated_orders:
        for item in o.order_items:
            if item.product and item.product.cost_price:
                e_product_cost += item.product.cost_price * item.quantity
        if o.shipping_cost:
            e_shipping_exp += o.shipping_cost

    outstanding = sum((o.balance_due for o in orders if o.status in OUTSTANDING_STATES and o.balance_due and o.balance_due > 0), Decimal("0"))

    ws_fin.append(["Metric", "Realised (Delivered)", "Estimated (In-Progress)", "Total"])
    ws_fin.append(["Gross Sales", float(r_gross), float(e_gross), float(r_gross + e_gross)])
    ws_fin.append(["Discounts", float(r_discounts), float(e_discounts), float(r_discounts + e_discounts)])
    ws_fin.append(["Refunds", float(refunds), 0, float(refunds)])
    ws_fin.append(["Net Sales", float(r_gross - r_discounts - refunds), float(e_gross - e_discounts), float(r_gross + e_gross - r_discounts - e_discounts - refunds)])
    ws_fin.append(["Shipping Charged", float(r_shipping), float(e_shipping), float(r_shipping + e_shipping)])
    ws_fin.append(["Product Cost", float(r_product_cost), float(e_product_cost), float(r_product_cost + e_product_cost)])
    ws_fin.append(["Shipping Expenses", float(r_shipping_exp), float(e_shipping_exp), float(r_shipping_exp + e_shipping_exp)])
    r_profit = (r_gross - r_discounts - refunds) + r_shipping - r_product_cost - r_shipping_exp
    e_profit = r_profit + (e_gross - e_discounts) + e_shipping - e_product_cost - e_shipping_exp
    ws_fin.append(["Profit", float(r_profit), float(e_profit), float(e_profit)])
    ws_fin.append([])
    ws_fin.append(["Outstanding Payments", "", "", float(outstanding)])
    _auto_width(ws_fin)

    # Save to buffer
    buf = BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"studybiz_masterlist_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


def _auto_width(ws):
    """Auto-adjust column widths based on content."""
    for column in ws.columns:
        max_length = 0
        column_letter_str = get_column_letter(column[0].column)
        for cell in column:
            try:
                if cell.value:
                    max_length = max(max_length, len(str(cell.value)))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column_letter_str].width = adjusted_width
