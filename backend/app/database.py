"""Database models and session management for StudyBiz AI."""
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, DateTime, Boolean,
    ForeignKey, Float, UniqueConstraint, Index
)
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def utcnow():
    return datetime.now(timezone.utc)


# -- Models --


class Campaign(Base):
    __tablename__ = "campaigns"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    status = Column(String, default="open")  # open, closing_soon, closed, completed
    opens_at = Column(DateTime, default=utcnow)
    closes_at = Column(DateTime, nullable=True)
    payment_instructions = Column(Text, default="Bank transfer to the account provided after order confirmation.")
    late_order_policy = Column(String, default="reject")  # reject, allow_with_approval
    cancellation_policy = Column(String, default="before_payment")  # before_payment, before_confirmation, none
    supplier_lead_time_days = Column(Integer, default=14)
    created_at = Column(DateTime, default=utcnow)

    products = relationship("Product", back_populates="campaign", cascade="all, delete-orphan")
    orders = relationship("Order", back_populates="campaign")


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, default="")
    price = Column(Float, nullable=False)
    stock_limit = Column(Integer, nullable=True)

    campaign = relationship("Campaign", back_populates="products")
    variants = relationship("ProductVariant", back_populates="product", cascade="all, delete-orphan")


class ProductVariant(Base):
    __tablename__ = "product_variants"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    attributes = Column(String, nullable=False)  # e.g. "Black / M"
    available_quantity = Column(Integer, nullable=True)

    product = relationship("Product", back_populates="variants")
    order_items = relationship("OrderItem", back_populates="variant")


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    display_name = Column(String, nullable=False)
    telegram_user_id = Column(String, nullable=True, index=True)
    telegram_username = Column(String, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    orders = relationship("Order", back_populates="customer")
    conversations = relationship("Conversation", back_populates="customer")


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    campaign_id = Column(Integer, ForeignKey("campaigns.id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    status = Column(String, default="draft")  # draft, pending_payment, confirmed, cancelled, completed
    payment_status = Column(String, default="unpaid")  # unpaid, payment_submitted, verifying, paid, rejected, refunded
    fulfilment_status = Column(String, default="not_ready")  # not_ready, preparing, ready, dispatched, collected
    total_amount = Column(Float, default=0.0)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)

    campaign = relationship("Campaign", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="order", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    product_variant_id = Column(Integer, ForeignKey("product_variants.id"), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

    order = relationship("Order", back_populates="items")
    variant = relationship("ProductVariant", back_populates="order_items")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    amount = Column(Float, nullable=False)
    status = Column(String, default="unpaid")  # unpaid, submitted, verifying, paid, rejected, refunded
    submitted_at = Column(DateTime, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verification_method = Column(String, default="manual")

    order = relationship("Order", back_populates="payments")


class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    platform = Column(String, default="telegram")
    conversation_reference = Column(String, default="")
    status = Column(String, default="open")  # open, resolved, escalated

    customer = relationship("Customer", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    platform_message_id = Column(String, nullable=True)
    sender_type = Column(String, nullable=False)  # customer, ai, admin
    content = Column(Text, nullable=False)
    intent = Column(String, nullable=True)  # product_question, new_order, order_change, payment_enquiry, order_status, cancellation, complaint, other
    created_at = Column(DateTime, default=utcnow)

    conversation = relationship("Conversation", back_populates="messages")
    order = relationship("Order", back_populates="messages")


class Exception_(Base):
    __tablename__ = "exceptions"

    id = Column(Integer, primary_key=True, index=True)
    type = Column(String, nullable=False)  # late_order, unverified_payment, cancellation_request, stock_mismatch, duplicate_submission, conflicting_info, refund_request
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    description = Column(Text, nullable=False)
    recommended_action = Column(Text, default="")
    status = Column(String, default="open")  # open, approved, rejected, more_info
    resolved_by = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)


class AutomationRule(Base):
    __tablename__ = "automation_rules"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    configuration = Column(Text, default="{}")  # JSON string
    enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class ActionLog(Base):
    __tablename__ = "action_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor_type = Column(String, nullable=False)  # ai, admin, system
    action_type = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    entity_id = Column(Integer, nullable=True)
    input_summary = Column(Text, default="")
    result = Column(Text, default="")
    timestamp = Column(DateTime, default=utcnow)


class ProcessedUpdate(Base):
    """Tracks processed Telegram update IDs to prevent duplicate processing."""
    __tablename__ = "processed_updates"

    id = Column(Integer, primary_key=True, index=True)
    update_id = Column(Integer, unique=True, nullable=False, index=True)
    processed_at = Column(DateTime, default=utcnow)


def init_db():
    Base.metadata.create_all(bind=engine)
