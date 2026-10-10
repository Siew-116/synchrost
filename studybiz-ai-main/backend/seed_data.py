"""Seed data script for StudyBiz AI demo.

Creates fictional Malaysian student entrepreneur data for demo and testing.
Run: python seed_data.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, date, timedelta
from decimal import Decimal
import json

from app.database import SessionLocal, engine, Base
from app.models import *
from app.utils.auth import get_password_hash

# Create tables
Base.metadata.create_all(bind=engine)

db = SessionLocal()

# Check if already seeded
existing = db.query(User).filter(User.email == "nurul@studybiz.my").first()
if existing:
    print("Database already seeded. Skipping.")
    db.close()
    exit(0)

print("Seeding StudyBiz AI demo data...")

# --- Demo User ---
user = User(
    email="nurul@studybiz.my",
    full_name="Nurul Aisyah Rahman",
    hashed_password=get_password_hash("demo123456"),
    business_name="Aisyah K-Pop Merch Store",
    business_whatsapp="+60123456789",
    business_instagram="@aisyah_kpop_merch",
    preferred_language="en",
    working_hours_start="09:00",
    working_hours_end="21:00",
    study_time_preference="20:00",
    min_rest_hours=7,
    campus_state="Selangor",
)
db.add(user)
db.commit()
db.refresh(user)
print(f"  Created user: {user.full_name} ({user.email})")

# --- Second Demo User ---
user2 = User(
    email="ariff@studybiz.my",
    full_name="Ariff Hakimi Yusof",
    hashed_password=get_password_hash("demo123456"),
    business_name="Ariff Sneaker Resell",
    business_whatsapp="+60198765432",
    business_instagram="@ariff_sneakers",
    preferred_language="ms",
    working_hours_start="10:00",
    working_hours_end="22:00",
    study_time_preference="21:00",
    min_rest_hours=6,
    campus_state="Kuala Lumpur",
)
db.add(user2)
db.commit()
db.refresh(user2)

# --- Academic Events (Nurul's schedule) ---
now = datetime.utcnow()
today = now.date()

academic_events = [
    # Classes (recurring)
    AcademicEvent(user_id=user.id, title="Database Systems Lecture", event_type=EventType.CLASS,
                  priority=EventPriority.HIGH, start_datetime=datetime.combine(today, datetime.strptime("09:00", "%H:%M").time()),
                  end_datetime=datetime.combine(today, datetime.strptime("11:00", "%H:%M").time()),
                  is_fixed=True, is_recurring=True, recurrence_pattern="weekly",
                  location="Room A-201", course_code="CSC3013"),
    AcademicEvent(user_id=user.id, title="Software Engineering Tutorial", event_type=EventType.CLASS,
                  priority=EventPriority.HIGH, start_datetime=datetime.combine(today + timedelta(days=1), datetime.strptime("14:00", "%H:%M").time()),
                  end_datetime=datetime.combine(today + timedelta(days=1), datetime.strptime("15:30", "%H:%M").time()),
                  is_fixed=True, is_recurring=True, recurrence_pattern="weekly",
                  location="Room B-105", course_code="SEC3201"),

    # EXAM TOMORROW (the key conflict scenario)
    AcademicEvent(user_id=user.id, title="Database Systems Final Exam", event_type=EventType.EXAM,
                  priority=EventPriority.CRITICAL,
                  start_datetime=datetime.combine(today + timedelta(days=1), datetime.strptime("09:00", "%H:%M").time()),
                  end_datetime=datetime.combine(today + timedelta(days=1), datetime.strptime("11:00", "%H:%M").time()),
                  is_fixed=True, location="Exam Hall 1", course_code="CSC3013",
                  notes="FINAL EXAM - 40% of grade. Must study!"),

    # Assignment due
    AcademicEvent(user_id=user.id, title="Software Engineering Group Project", event_type=EventType.ASSIGNMENT,
                  priority=EventPriority.HIGH, due_date=today + timedelta(days=3),
                  estimated_duration_minutes=180, is_fixed=False,
                  notes="Submit via Moodle. Group of 4.", course_code="SEC3201"),

    # Study session
    AcademicEvent(user_id=user.id, title="Database Revision Session", event_type=EventType.STUDY_SESSION,
                  priority=EventPriority.CRITICAL,
                  start_datetime=datetime.combine(today, datetime.strptime("20:00", "%H:%M").time()),
                  end_datetime=datetime.combine(today, datetime.strptime("22:00", "%H:%M").time()),
                  is_fixed=False, estimated_duration_minutes=120,
                  notes="Final revision before exam tomorrow"),

    # Personal
    AcademicEvent(user_id=user.id, title="Family Dinner", event_type=EventType.PERSONAL,
                  priority=EventPriority.MEDIUM,
                  start_datetime=datetime.combine(today + timedelta(days=2), datetime.strptime("18:00", "%H:%M").time()),
                  end_datetime=datetime.combine(today + timedelta(days=2), datetime.strptime("20:00", "%H:%M").time()),
                  is_fixed=True),
]
for e in academic_events:
    db.add(e)
db.commit()
print(f"  Created {len(academic_events)} academic events")

# --- Products ---
products_data = [
    {"name": "BTS BT21 Pillow Plush", "sku": "BT21-PIL-001", "category": "Plush", "selling_price": Decimal("45.00"), "cost_price": Decimal("22.00"), "available_stock": 15, "low_stock_threshold": 5},
    {"name": "BLACKPINK Lightstick v2", "sku": "BP-LS-002", "category": "Lightstick", "selling_price": Decimal("120.00"), "cost_price": Decimal("65.00"), "available_stock": 8, "low_stock_threshold": 3},
    {"name": "EXO Photocard Set", "sku": "EXO-PC-003", "category": "Photocard", "selling_price": Decimal("35.00"), "cost_price": Decimal("15.00"), "available_stock": 3, "low_stock_threshold": 5},
    {"name": "TWICE Album - Eyes Wide Open", "sku": "TW-AL-004", "category": "Album", "selling_price": Decimal("75.00"), "cost_price": Decimal("40.00"), "available_stock": 12, "low_stock_threshold": 3},
    {"name": "Stray Kids Hoodie", "sku": "SK-HD-005", "category": "Apparel", "selling_price": Decimal("95.00"), "cost_price": Decimal("50.00"), "available_stock": 6, "low_stock_threshold": 2},
    {"name": "aespa Keyring Set", "sku": "AE-KR-006", "category": "Accessories", "selling_price": Decimal("25.00"), "cost_price": Decimal("10.00"), "available_stock": 20, "low_stock_threshold": 5},
    {"name": "SEVENTEEN Poster A", "sku": "SV-PS-007", "category": "Poster", "selling_price": Decimal("15.00"), "cost_price": Decimal("5.00"), "available_stock": 30, "low_stock_threshold": 10},
    {"name": "ITZY Sticker Pack", "sku": "IZ-ST-008", "category": "Stationery", "selling_price": Decimal("12.00"), "cost_price": Decimal("4.00"), "available_stock": 2, "low_stock_threshold": 5},
    {"name": "ENHYPEN Photobook", "sku": "EN-PB-009", "category": "Photobook", "selling_price": Decimal("85.00"), "cost_price": Decimal("45.00"), "available_stock": 0, "low_stock_threshold": 3, "is_preorder": True},
    {"name": "NCT 127 Tumbler", "sku": "NC-TB-010", "category": "Merch", "selling_price": Decimal("38.00"), "cost_price": Decimal("18.00"), "available_stock": 10, "low_stock_threshold": 3},
    {"name": "LE SSERAFIM Badge Set", "sku": "LS-BG-011", "category": "Accessories", "selling_price": Decimal("18.00"), "cost_price": Decimal("7.00"), "available_stock": 14, "low_stock_threshold": 4},
    {"name": "NewJeans Tote Bag", "sku": "NJ-TB-012", "category": "Apparel", "selling_price": Decimal("42.00"), "cost_price": Decimal("20.00"), "available_stock": 7, "low_stock_threshold": 3},
]

products = []
for p_data in products_data:
    p = Product(user_id=user.id, **p_data)
    db.add(p)
    db.flush()
    products.append(p)
    # Record initial stock movement
    if p.available_stock > 0:
        db.add(StockMovement(product_id=p.id, movement_type="initial", quantity_change=p.available_stock, reference="Initial stock", notes="Seed data"))
db.commit()
print(f"  Created {len(products)} products")

# --- Customers ---
names = [
    "Siti Nurhaliza", "Ahmad Faizal", "Lim Wei Jie", "Priya Sharma", "Tan Mei Ling",
    "Muhammad Irfan", "Chong Kar Yan", "Nurul Huda", "Rajesh Kumar", "Sarah Lim",
    "Hafiz Abdullah", "Wong Ka Kit", "Nabila Aziz", "Daniel Lee", "Farah Ain",
    "Jason Tan", "Kavitha Raj", "Zul Azlan", "Crystal Ong", "Faisal Mansor",
    "Amirah Yusof", "Kenneth Mah", "Suhaila Ramli", "Vincent Chong", "Diana Wong",
    "Imran Salleh", "Joanne Lee", "Syafiq Nazri", "Beatrice Tan", "Hassan Ali",
]
customers = []
for name in names:
    c = Customer(
        user_id=user.id, name=name,
        whatsapp_number=f"+6012{abs(hash(name)) % 10000000:07d}",
        instagram_handle=f"@{name.lower().replace(' ', '_')}",
    )
    db.add(c)
    db.flush()
    customers.append(c)
db.commit()
print(f"  Created {len(customers)} customers")

# --- Suppliers ---
supplier1 = Supplier(user_id=user.id, name="K-Pop Hub Korea", contact="Mr. Kim",
                     whatsapp="+821012345678", location="Seoul, South Korea",
                     notes="Main supplier for albums and official merch")
supplier2 = Supplier(user_id=user.id, name="Shenzhen Merch Co", contact="Ms. Chen",
                     whatsapp="+8613812345678", location="Shenzhen, China",
                     notes="Custom merch and accessories")
db.add_all([supplier1, supplier2])
db.commit()
db.refresh(supplier1)
db.refresh(supplier2)
print(f"  Created 2 suppliers")

# --- Bulk/Group Orders ---
bulk1 = BulkOrder(
    user_id=user.id, group_identifier="GO-2026-001", supplier_id=supplier1.id,
    domestic_shipping_cost=Decimal("15.00"), international_shipping_cost=Decimal("45.00"),
    ems_fee=Decimal("30.00"), other_shared_costs=Decimal("5.00"),
    cost_allocation_method="equal", purchase_status="arrived", arrival_status="distributed",
    estimated_arrival=today - timedelta(days=5), actual_arrival=today - timedelta(days=3),
    notes="BTS & BLACKPINK group order",
)
bulk2 = BulkOrder(
    user_id=user.id, group_identifier="GO-2026-002", supplier_id=supplier2.id,
    domestic_shipping_cost=Decimal("20.00"), international_shipping_cost=Decimal("60.00"),
    ems_fee=Decimal("40.00"), other_shared_costs=Decimal("0.00"),
    cost_allocation_method="by_value", purchase_status="shipped", arrival_status="pending",
    estimated_arrival=today + timedelta(days=7),
    notes="Custom hoodies and tumblers - DELAYED",
)
db.add_all([bulk1, bulk2])
db.commit()
print(f"  Created 2 bulk orders")

# --- Orders (30 orders with various statuses) ---
import random
random.seed(42)

statuses_cycle = [
    OrderStatus.PENDING, OrderStatus.CONFIRMED, OrderStatus.PAID, OrderStatus.PAID,
    OrderStatus.PAID, OrderStatus.PACKED, OrderStatus.PACKED, OrderStatus.DISPATCHED,
    OrderStatus.DELIVERED, OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.EXCEPTION,
]

orders_created = 0
for i in range(30):
    customer = customers[i % len(customers)]
    product = products[i % len(products)]
    qty = random.randint(1, 3)
    unit_price = product.selling_price
    subtotal = unit_price * qty
    discount = Decimal("0")
    shipping_charged = Decimal("8.00") if i % 3 != 0 else Decimal("0")
    total = subtotal - discount + shipping_charged
    status = statuses_cycle[i % len(statuses_cycle)]

    amount_paid = Decimal("0")
    if status in [OrderStatus.PAID, OrderStatus.PACKED, OrderStatus.DISPATCHED, OrderStatus.DELIVERED]:
        amount_paid = total
    elif status == OrderStatus.CANCELLED and i % 7 == 0:
        amount_paid = total  # Was paid then cancelled

    balance = total - amount_paid

    dispatch_date = today + timedelta(days=random.randint(1, 7))
    if status in [OrderStatus.PENDING, OrderStatus.CONFIRMED]:
        dispatch_date = today + timedelta(days=random.randint(3, 10))

    # Link some orders to bulk orders
    bulk_id = None
    if i < 5:
        bulk_id = bulk1.id
    elif i < 8:
        bulk_id = bulk2.id

    order = Order(
        user_id=user.id, customer_id=customer.id,
        order_number=f"SB-{today.strftime('%Y%m%d')}-{i+1:04d}",
        status=status, subtotal=subtotal, discount=discount,
        shipping_charged=shipping_charged, total=total,
        amount_paid=amount_paid, balance_due=balance,
        promised_dispatch_date=dispatch_date,
        estimated_packing_minutes=random.choice([5, 8, 10, 12, 15]),
        bulk_order_id=bulk_id,
        packing_requirements="Bubble wrap + thank you card" if i % 2 == 0 else "Standard packaging",
    )
    db.add(order)
    db.flush()

    # Create order item
    item = OrderItem(
        order_id=order.id, product_id=product.id,
        quantity=qty, unit_price=unit_price, total_price=subtotal,
    )
    db.add(item)

    # Record status history
    db.add(OrderStatusHistory(order_id=order.id, from_status=None, to_status=OrderStatus.PENDING, note="Order created"))

    if status != OrderStatus.PENDING:
        db.add(OrderStatusHistory(order_id=order.id, from_status=OrderStatus.PENDING, to_status=OrderStatus.CONFIRMED, note="Confirmed"))
    if status in [OrderStatus.PAID, OrderStatus.PACKED, OrderStatus.DISPATCHED, OrderStatus.DELIVERED]:
        db.add(OrderStatusHistory(order_id=order.id, from_status=OrderStatus.CONFIRMED, to_status=OrderStatus.PAID, note="Payment received"))
        # Record finance transaction
        db.add(FinanceTransaction(user_id=user.id, transaction_type="sale", amount=total, reference_type="order", reference_id=order.id, description=f"Payment for {order.order_number}"))
    if status in [OrderStatus.PACKED, OrderStatus.DISPATCHED, OrderStatus.DELIVERED]:
        db.add(OrderStatusHistory(order_id=order.id, from_status=OrderStatus.PAID, to_status=OrderStatus.PACKED, note="Packed"))
    if status in [OrderStatus.DISPATCHED, OrderStatus.DELIVERED]:
        order.tracking_number = f"MY{abs(hash(order.order_number)) % 10000000:07d}"
        order.shipping_service = "PosLaju" if i % 2 == 0 else "J&T Express"
        order.shipping_cost = Decimal("8.50")
        db.add(OrderStatusHistory(order_id=order.id, from_status=OrderStatus.PACKED, to_status=OrderStatus.DISPATCHED, note="Dispatched"))
    if status == OrderStatus.DELIVERED:
        db.add(OrderStatusHistory(order_id=order.id, from_status=OrderStatus.DISPATCHED, to_status=OrderStatus.DELIVERED, note="Delivered"))
    if status == OrderStatus.CANCELLED:
        db.add(OrderStatusHistory(order_id=order.id, from_status=OrderStatus.CONFIRMED if amount_paid == 0 else OrderStatus.PAID, to_status=OrderStatus.CANCELLED, note="Customer cancelled"))
        if amount_paid > 0:
            db.add(FinanceTransaction(user_id=user.id, transaction_type="refund", amount=-amount_paid, reference_type="order", reference_id=order.id, description=f"Refund for cancelled {order.order_number}"))
    if status == OrderStatus.EXCEPTION:
        db.add(OrderStatusHistory(order_id=order.id, from_status=OrderStatus.PAID, to_status=OrderStatus.EXCEPTION, note="Item missing from supplier"))

    orders_created += 1

db.commit()
print(f"  Created {orders_created} orders with status history")

# --- Exceptions ---
exceptions = [
    BusinessException(user_id=user.id, exception_type=ExceptionType.SUPPLIER_DELAY,
                      status=ExceptionStatus.OPEN, title="GO-2026-002 Shipment Delayed",
                      description="Shenzhen Merch Co shipment delayed by 5 days. Affects 3 orders.",
                      amount_involved=Decimal("0.00")),
    BusinessException(user_id=user.id, exception_type=ExceptionType.CANCELLATION,
                      status=ExceptionStatus.RESOLVED, title="Customer cancelled order SB-...-0007",
                      description="Customer changed mind. Full refund processed.",
                      amount_involved=Decimal("83.00"), resolved_at=now - timedelta(days=2)),
    BusinessException(user_id=user.id, exception_type=ExceptionType.MISSING_ITEM,
                      status=ExceptionStatus.OPEN, title="Missing EXO Photocard from GO-2026-001",
                      description="2 EXO photocard sets missing from supplier parcel.",
                      amount_involved=Decimal("70.00")),
    BusinessException(user_id=user.id, exception_type=ExceptionType.DEFECTIVE_ITEM,
                      status=ExceptionStatus.IN_PROGRESS, title="Defective BTS Pillow",
                      description="BTS BT21 pillow has stitching defect. Customer requesting replacement.",
                      amount_involved=Decimal("45.00")),
    BusinessException(user_id=user.id, exception_type=ExceptionType.BLACKOUT,
                      status=ExceptionStatus.OPEN, title="Exam Week Blackout",
                      description=f"No shipping from {today + timedelta(days=1)} to {today + timedelta(days=5)} due to final exams.",
                      amount_involved=Decimal("0.00")),
]
for e in exceptions:
    db.add(e)
db.commit()
print(f"  Created {len(exceptions)} business exceptions")

# --- Purchase Orders ---
po1 = PurchaseOrder(
    user_id=user.id, supplier_id=supplier1.id, po_number="PO-001",
    status="arrived", total_cost=Decimal("450.00"),
    estimated_arrival=today - timedelta(days=5), actual_arrival=today - timedelta(days=3),
    tracking_number="KR123456789", notes="BTS & BLACKPINK items",
)
po2 = PurchaseOrder(
    user_id=user.id, supplier_id=supplier2.id, po_number="PO-002",
    status="shipped", total_cost=Decimal("380.00"),
    estimated_arrival=today + timedelta(days=7),
    tracking_number="CN987654321", notes="Hoodies and tumblers - DELAYED",
)
db.add_all([po1, po2])
db.commit()
print(f"  Created 2 purchase orders")

# --- Notifications ---
notifications = [
    Notification(user_id=user.id, title="Exam Tomorrow!", message="Your Database Systems Final Exam is tomorrow at 9 AM.", category="academic", is_read=False),
    Notification(user_id=user.id, title="15 Orders Need Packing", message="You have 15 paid orders waiting to be packed.", category="business", is_read=False),
    Notification(user_id=user.id, title="Low Stock Alert", message="EXO Photocard Set and ITZY Sticker Pack are low on stock.", category="business", is_read=False),
    Notification(user_id=user.id, title="Shipping Cutoff Tomorrow", message="5 orders have dispatch deadlines tomorrow.", category="business", is_read=False),
    Notification(user_id=user.id, title="Supplier Delay", message="GO-2026-002 shipment from Shenzhen Merch Co is delayed.", category="business", is_read=True),
]
for n in notifications:
    db.add(n)
db.commit()
print(f"  Created {len(notifications)} notifications")

# --- Message Drafts (sample) ---
sample_msg = MessageDraft(
    user_id=user.id, template_type="payment_reminder", language="en",
    subject="Payment Reminder - SB-...-0002",
    body="Hi Siti Nurhaliza, this is a friendly reminder that your order SB-...-0002 has a balance of RM 53.00. Please complete payment to proceed.",
    status=MessageStatus.DRAFTED,
)
db.add(sample_msg)
db.commit()
print(f"  Created 1 sample message draft")

# --- Agent Log (sample) ---
sample_log = AgentLog(
    user_id=user.id, session_id="seed-session",
    observation="Detected exam tomorrow + 15 paid orders needing packing",
    analysis="Intent: exam_conflict. Priority: critical. Packing time needed: ~150 min.",
    plan="Find packing slots outside exam window. Draft customer notifications.",
    action_taken="detect_schedule_conflicts, estimate_packing_duration, find_available_time_slots",
    action_result="Found 3 available slots. 2 conflicts detected.",
    verified=True, tool_called="detect_schedule_conflicts",
    tool_input="exam conflict check",
    tool_output="2 conflicts found",
    success=True,
)
db.add(sample_log)
db.commit()
print(f"  Created 1 sample agent log")

db.close()
print("\n✅ Seed data complete!")
print(f"   Demo user: nurul@studybiz.my / demo123456")
print(f"   Second user: ariff@studybiz.my / demo123456")
print(f"   Products: {len(products)}")
print(f"   Customers: {len(customers)}")
print(f"   Orders: 30 (various statuses)")
print(f"   Bulk orders: 2")
print(f"   Exceptions: 5 (supplier delay, cancellation, missing, defective, blackout)")
print(f"   Academic events: {len(academic_events)} (including exam tomorrow)")
