"""Database models for StudyBiz AI."""
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Date, Time,
    ForeignKey, Numeric, JSON, Enum as SQLEnum, func, create_engine
)
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime
import enum


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Business profile
    business_name = Column(String(255))
    business_whatsapp = Column(String(20))
    business_instagram = Column(String(255))
    preferred_language = Column(String(10), default="en")  # en or ms
    working_hours_start = Column(String(5), default="09:00")
    working_hours_end = Column(String(5), default="21:00")
    campus_state = Column(String(50))  # Malaysian state for public holiday matching

    # Preferences
    study_time_preference = Column(String(5), default="20:00")
    min_rest_hours = Column(Integer, default=7)

    academic_events = relationship("AcademicEvent", back_populates="user", cascade="all, delete-orphan")
    customers = relationship("Customer", back_populates="user", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="user", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="user", cascade="all, delete-orphan")
    bulk_orders = relationship("BulkOrder", back_populates="user", cascade="all, delete-orphan")
    suppliers = relationship("Supplier", back_populates="user", cascade="all, delete-orphan")
    automation_jobs = relationship("AutomationJob", back_populates="user", cascade="all, delete-orphan")
    agent_logs = relationship("AgentLog", back_populates="user", cascade="all, delete-orphan")
    message_drafts = relationship("MessageDraft", back_populates="user", cascade="all, delete-orphan")
    approval_requests = relationship("ApprovalRequest", back_populates="user", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")


# --- Academic Models ---

class EventType(str, enum.Enum):
    CLASS = "class"
    EXAM = "exam"
    COURSEWORK = "coursework"
    ASSIGNMENT = "assignment"
    STUDY_SESSION = "study_session"
    PERSONAL = "personal"
    PACKING = "packing"
    POSTAGE = "postage"
    SUPPLIER_ARRIVAL = "supplier_arrival"


class EventPriority(str, enum.Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class AcademicEvent(Base):
    __tablename__ = "academic_events"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=False)
    event_type = Column(SQLEnum(EventType), nullable=False)
    priority = Column(SQLEnum(EventPriority), default=EventPriority.MEDIUM)

    # Scheduling
    start_datetime = Column(DateTime)
    end_datetime = Column(DateTime)
    due_date = Column(Date)
    estimated_duration_minutes = Column(Integer, default=60)

    # Flexibility
    is_fixed = Column(Boolean, default=False)  # Fixed events cannot be moved without permission

    # Status
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)

    # Recurrence
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(100))  # e.g., "weekly", "daily"

    # Metadata
    location = Column(String(255))
    notes = Column(Text)
    course_code = Column(String(50))

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="academic_events")


# --- Business Models ---

class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    whatsapp_number = Column(String(20))
    instagram_handle = Column(String(255))
    email = Column(String(255))
    address = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="customers")
    orders = relationship("Order", back_populates="customer")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(500), nullable=False)
    sku = Column(String(100))
    description = Column(Text)
    category = Column(String(100))

    # Pricing (MYR)
    selling_price = Column(Numeric(12, 2), nullable=False)
    cost_price = Column(Numeric(12, 2))

    # Inventory
    available_stock = Column(Integer, default=0)
    reserved_stock = Column(Integer, default=0)
    incoming_stock = Column(Integer, default=0)
    low_stock_threshold = Column(Integer, default=5)

    # Status
    is_active = Column(Boolean, default=True)
    is_preorder = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    stock_movements = relationship("StockMovement", back_populates="product")


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PAID = "paid"
    PACKED = "packed"
    DISPATCHED = "dispatched"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    EXCEPTION = "exception"


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    order_number = Column(String(50), nullable=False, unique=True)

    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)

    # Pricing (MYR)
    subtotal = Column(Numeric(12, 2), default=0)
    discount = Column(Numeric(12, 2), default=0)
    shipping_charged = Column(Numeric(12, 2), default=0)
    total = Column(Numeric(12, 2), default=0)
    amount_paid = Column(Numeric(12, 2), default=0)
    balance_due = Column(Numeric(12, 2), default=0)

    # Fulfillment
    promised_dispatch_date = Column(Date)
    tracking_number = Column(String(100))
    shipping_service = Column(String(100))
    shipping_cost = Column(Numeric(12, 2))

    # Packing
    packing_requirements = Column(Text)
    estimated_packing_minutes = Column(Integer, default=10)

    # Metadata
    notes = Column(Text)
    warnings = Column(Text)
    payment_evidence = Column(String(500))  # reference to payment proof

    # Group order link
    bulk_order_id = Column(Integer, ForeignKey("bulk_orders.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    bulk_order = relationship("BulkOrder", back_populates="orders")
    status_history = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    total_price = Column(Numeric(12, 2), nullable=False)

    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")


class OrderStatusHistory(Base):
    __tablename__ = "order_status_history"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    from_status = Column(SQLEnum(OrderStatus), nullable=True)
    to_status = Column(SQLEnum(OrderStatus), nullable=False)
    note = Column(String(500))
    changed_at = Column(DateTime, default=datetime.utcnow)

    order = relationship("Order", back_populates="status_history")


# --- Bulk/Group Orders ---

class BulkOrder(Base):
    __tablename__ = "bulk_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_identifier = Column(String(100), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=True)

    # Shared costs
    domestic_shipping_cost = Column(Numeric(12, 2), default=0)
    international_shipping_cost = Column(Numeric(12, 2), default=0)
    ems_fee = Column(Numeric(12, 2), default=0)
    other_shared_costs = Column(Numeric(12, 2), default=0)
    cost_allocation_method = Column(String(50), default="equal")  # equal, by_value, by_weight

    # Status
    purchase_status = Column(String(50), default="pending")  # pending, ordered, shipped, arrived, distributed
    arrival_status = Column(String(50), default="pending")
    estimated_arrival = Column(Date)
    actual_arrival = Column(Date)

    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bulk_orders")
    supplier = relationship("Supplier", back_populates="bulk_orders")
    orders = relationship("Order", back_populates="bulk_order")


# --- Inventory ---

class StockMovement(Base):
    __tablename__ = "stock_movements"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    movement_type = Column(String(50))  # purchase, sale, reserve, adjust, damage, loss
    quantity_change = Column(Integer, nullable=False)
    reference = Column(String(255))  # order number, purchase order, etc.
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", back_populates="stock_movements")


# --- Supplier Purchases ---

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    contact = Column(String(255))
    whatsapp = Column(String(20))
    location = Column(String(255))
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="suppliers")
    bulk_orders = relationship("BulkOrder", back_populates="supplier")
    purchase_orders = relationship("PurchaseOrder", back_populates="supplier")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)
    po_number = Column(String(50))
    status = Column(String(50), default="pending")  # pending, ordered, shipped, arrived

    total_cost = Column(Numeric(12, 2), default=0)
    purchase_proof = Column(String(500))  # reference to proof
    estimated_arrival = Column(Date)
    actual_arrival = Column(Date)
    tracking_number = Column(String(100))
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    supplier = relationship("Supplier", back_populates="purchase_orders")


# --- Packaging & Shipping ---

class PackagingBatch(Base):
    __tablename__ = "packaging_batches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    batch_name = Column(String(255))
    planned_date = Column(Date)
    total_orders = Column(Integer, default=0)
    estimated_total_minutes = Column(Integer, default=0)
    status = Column(String(50), default="pending")  # pending, in_progress, completed
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


class ShippingBatch(Base):
    __tablename__ = "shipping_batches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    batch_name = Column(String(255))
    planned_date = Column(Date)
    shipping_service = Column(String(100))
    total_cost = Column(Numeric(12, 2), default=0)
    status = Column(String(50), default="pending")  # pending, dispatched
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)


# --- Exceptions ---

class ExceptionType(str, enum.Enum):
    BLACKOUT = "blackout"
    CANCELLATION = "cancellation"
    SUPPLIER_DELAY = "supplier_delay"
    MISSING_ITEM = "missing_item"
    DEFECTIVE_ITEM = "defective_item"
    REFUND = "refund"
    REPLACEMENT = "replacement"
    DISPUTE = "dispute"


class ExceptionStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class BusinessException(Base):
    __tablename__ = "business_exceptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    exception_type = Column(SQLEnum(ExceptionType), nullable=False)
    status = Column(SQLEnum(ExceptionStatus), default=ExceptionStatus.OPEN)
    affected_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    resolution = Column(Text)
    amount_involved = Column(Numeric(12, 2), default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)


# --- Finance ---

class FinanceTransaction(Base):
    __tablename__ = "finance_transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    transaction_type = Column(String(50))  # sale, refund, product_cost, shipping_expense, other_expense
    amount = Column(Numeric(12, 2), nullable=False)
    reference_type = Column(String(50))  # order, bulk_order, purchase_order, manual
    reference_id = Column(Integer)
    description = Column(String(500))
    transaction_date = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)


# --- Agent Models ---

class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(100))

    # The agent cycle
    observation = Column(Text)
    analysis = Column(Text)
    plan = Column(Text)
    action_taken = Column(String(500))
    action_result = Column(Text)
    verified = Column(Boolean, default=False)

    # Action details
    tool_called = Column(String(200))
    tool_input = Column(Text)
    tool_output = Column(Text)
    success = Column(Boolean, default=False)
    error_message = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="agent_logs")


# --- Automation ---

class AutomationJob(Base):
    __tablename__ = "automation_jobs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(255), nullable=False)
    job_type = Column(String(100), nullable=False)
    schedule_cron = Column(String(100))  # cron expression
    is_enabled = Column(Boolean, default=True)

    # Status
    next_run = Column(DateTime)
    last_run = Column(DateTime)
    last_status = Column(String(50))  # success, failed, skipped
    last_error = Column(Text)

    # Idempotency
    last_run_key = Column(String(100))

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="automation_jobs")


class AutomationRun(Base):
    __tablename__ = "automation_runs"

    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(Integer, ForeignKey("automation_jobs.id"), nullable=False)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    status = Column(String(50))  # running, success, failed
    result = Column(Text)
    error = Column(Text)


# --- Customer Messages ---

class MessageStatus(str, enum.Enum):
    DRAFTED = "drafted"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    EXECUTED = "executed"
    FAILED = "failed"


class MessageDraft(Base):
    __tablename__ = "message_drafts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=True)

    template_type = Column(String(100), nullable=False)
    language = Column(String(10), default="en")  # en or ms
    subject = Column(String(500))
    body = Column(Text, nullable=False)

    status = Column(SQLEnum(MessageStatus), default=MessageStatus.DRAFTED)
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime)
    executed_at = Column(DateTime)

    user = relationship("User", back_populates="message_drafts")


# --- Approval Queue ---

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action_type = Column(String(100), nullable=False)  # send_message, refund, cancel_order, etc.
    description = Column(Text, nullable=False)
    payload = Column(Text)  # JSON string of action details

    status = Column(String(50), default="pending")  # pending, approved, rejected
    created_at = Column(DateTime, default=datetime.utcnow)
    resolved_at = Column(DateTime)
    resolved_by = Column(String(255))
    result = Column(Text)

    user = relationship("User", back_populates="approval_requests")


# --- Notifications ---

class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(500), nullable=False)
    message = Column(Text)
    category = Column(String(50))  # academic, business, agent, automation
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")
