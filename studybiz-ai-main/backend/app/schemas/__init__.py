"""Pydantic schemas for API request/response validation."""
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from datetime import datetime, date, time
from typing import Optional, List
from decimal import Decimal
from app.models import (
    EventType, EventPriority, OrderStatus, ExceptionType, ExceptionStatus,
    MessageStatus
)


# --- Auth Schemas ---

class UserRegister(BaseModel):
    email: EmailStr
    full_name: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=6, max_length=128)
    business_name: Optional[str] = None
    preferred_language: str = "en"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    business_name: Optional[str]
    business_whatsapp: Optional[str]
    business_instagram: Optional[str]
    preferred_language: str
    working_hours_start: str
    working_hours_end: str
    study_time_preference: str
    min_rest_hours: int
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    business_name: Optional[str] = None
    business_whatsapp: Optional[str] = None
    business_instagram: Optional[str] = None
    preferred_language: Optional[str] = None
    working_hours_start: Optional[str] = None
    working_hours_end: Optional[str] = None
    study_time_preference: Optional[str] = None
    min_rest_hours: Optional[int] = None


# --- Academic Schemas ---

class AcademicEventBase(BaseModel):
    title: str
    event_type: EventType
    priority: EventPriority = EventPriority.MEDIUM
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    due_date: Optional[date] = None
    estimated_duration_minutes: int = 60
    is_fixed: bool = False
    is_completed: bool = False
    is_recurring: bool = False
    recurrence_pattern: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    course_code: Optional[str] = None

class AcademicEventCreate(AcademicEventBase):
    pass

class AcademicEventUpdate(BaseModel):
    title: Optional[str] = None
    event_type: Optional[EventType] = None
    priority: Optional[EventPriority] = None
    start_datetime: Optional[datetime] = None
    end_datetime: Optional[datetime] = None
    due_date: Optional[date] = None
    estimated_duration_minutes: Optional[int] = None
    is_fixed: Optional[bool] = None
    is_completed: Optional[bool] = None
    is_recurring: Optional[bool] = None
    recurrence_pattern: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None
    course_code: Optional[str] = None

class AcademicEventResponse(AcademicEventBase):
    id: int
    completed_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Customer Schemas ---

class CustomerBase(BaseModel):
    name: str
    whatsapp_number: Optional[str] = None
    instagram_handle: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(CustomerBase):
    pass

class CustomerResponse(CustomerBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Product Schemas ---

class ProductBase(BaseModel):
    name: str
    sku: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    selling_price: Decimal
    cost_price: Optional[Decimal] = None
    available_stock: int = 0
    low_stock_threshold: int = 5
    is_active: bool = True
    is_preorder: bool = False

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    selling_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    available_stock: Optional[int] = None
    low_stock_threshold: Optional[int] = None
    is_active: Optional[bool] = None
    is_preorder: Optional[bool] = None

class ProductResponse(ProductBase):
    id: int
    reserved_stock: int
    incoming_stock: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Order Schemas ---

class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)
    unit_price: Optional[Decimal] = None  # Auto-filled from product if not provided

class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: Decimal
    total_price: Decimal
    model_config = ConfigDict(from_attributes=True)

class OrderBase(BaseModel):
    customer_id: int
    order_items: List[OrderItemCreate]
    discount: Decimal = Decimal("0")
    shipping_charged: Decimal = Decimal("0")
    promised_dispatch_date: Optional[date] = None
    packing_requirements: Optional[str] = None
    estimated_packing_minutes: int = 10
    notes: Optional[str] = None
    bulk_order_id: Optional[int] = None

class OrderCreate(OrderBase):
    pass

class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    discount: Optional[Decimal] = None
    shipping_charged: Optional[Decimal] = None
    amount_paid: Optional[Decimal] = None
    promised_dispatch_date: Optional[date] = None
    tracking_number: Optional[str] = None
    shipping_service: Optional[str] = None
    shipping_cost: Optional[Decimal] = None
    packing_requirements: Optional[str] = None
    estimated_packing_minutes: Optional[int] = None
    notes: Optional[str] = None
    payment_evidence: Optional[str] = None
    bulk_order_id: Optional[int] = None

class OrderResponse(BaseModel):
    id: int
    order_number: str
    customer_id: int
    status: OrderStatus
    subtotal: Decimal
    discount: Decimal
    shipping_charged: Decimal
    total: Decimal
    amount_paid: Decimal
    balance_due: Decimal
    promised_dispatch_date: Optional[date]
    tracking_number: Optional[str]
    shipping_service: Optional[str]
    shipping_cost: Optional[Decimal]
    packing_requirements: Optional[str]
    estimated_packing_minutes: int
    notes: Optional[str]
    warnings: Optional[str]
    payment_evidence: Optional[str]
    bulk_order_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    order_items: List[OrderItemResponse] = []
    model_config = ConfigDict(from_attributes=True)


# --- Bulk Order Schemas ---

class BulkOrderBase(BaseModel):
    group_identifier: str
    supplier_id: Optional[int] = None
    domestic_shipping_cost: Decimal = Decimal("0")
    international_shipping_cost: Decimal = Decimal("0")
    ems_fee: Decimal = Decimal("0")
    other_shared_costs: Decimal = Decimal("0")
    cost_allocation_method: str = "equal"
    estimated_arrival: Optional[date] = None
    notes: Optional[str] = None

class BulkOrderCreate(BulkOrderBase):
    pass

class BulkOrderUpdate(BaseModel):
    group_identifier: Optional[str] = None
    supplier_id: Optional[int] = None
    domestic_shipping_cost: Optional[Decimal] = None
    international_shipping_cost: Optional[Decimal] = None
    ems_fee: Optional[Decimal] = None
    other_shared_costs: Optional[Decimal] = None
    cost_allocation_method: Optional[str] = None
    purchase_status: Optional[str] = None
    arrival_status: Optional[str] = None
    estimated_arrival: Optional[date] = None
    actual_arrival: Optional[date] = None
    notes: Optional[str] = None

class BulkOrderResponse(BulkOrderBase):
    id: int
    purchase_status: str
    arrival_status: str
    actual_arrival: Optional[date]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Supplier Schemas ---

class SupplierBase(BaseModel):
    name: str
    contact: Optional[str] = None
    whatsapp: Optional[str] = None
    location: Optional[str] = None
    notes: Optional[str] = None

class SupplierCreate(SupplierBase):
    pass

class SupplierResponse(SupplierBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Exception Schemas ---

class ExceptionBase(BaseModel):
    exception_type: ExceptionType
    affected_order_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    amount_involved: Decimal = Decimal("0")

class ExceptionCreate(ExceptionBase):
    pass

class ExceptionUpdate(BaseModel):
    status: Optional[ExceptionStatus] = None
    resolution: Optional[str] = None
    amount_involved: Optional[Decimal] = None

class ExceptionResponse(ExceptionBase):
    id: int
    status: ExceptionStatus
    resolution: Optional[str]
    created_at: datetime
    resolved_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


# --- Finance Schemas ---

class FinanceTransactionResponse(BaseModel):
    id: int
    transaction_type: str
    amount: Decimal
    reference_type: Optional[str]
    reference_id: Optional[int]
    description: Optional[str]
    transaction_date: datetime
    model_config = ConfigDict(from_attributes=True)

class FinanceSummary(BaseModel):
    gross_sales: Decimal
    discounts: Decimal
    refunds: Decimal
    net_sales: Decimal
    product_cost: Decimal
    shipping_charged: Decimal
    shipping_expenses: Decimal
    other_expenses: Decimal
    realized_profit: Decimal
    estimated_profit: Decimal
    outstanding_payments: Decimal


# --- Agent Schemas ---

class AgentChatRequest(BaseModel):
    message: str
    context: Optional[str] = None

class AgentActionInfo(BaseModel):
    tool: str
    description: str
    requires_approval: bool

class AgentChatResponse(BaseModel):
    response: str
    actions_taken: List[dict] = []
    approval_requests: List[dict] = []
    session_id: str

class AgentLogResponse(BaseModel):
    id: int
    observation: Optional[str]
    analysis: Optional[str]
    plan: Optional[str]
    action_taken: Optional[str]
    action_result: Optional[str]
    verified: bool
    tool_called: Optional[str]
    tool_input: Optional[str]
    tool_output: Optional[str]
    success: bool
    error_message: Optional[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Automation Schemas ---

class AutomationJobResponse(BaseModel):
    id: int
    name: str
    job_type: str
    schedule_cron: Optional[str]
    is_enabled: bool
    next_run: Optional[datetime]
    last_run: Optional[datetime]
    last_status: Optional[str]
    last_error: Optional[str]
    model_config = ConfigDict(from_attributes=True)

class AutomationJobUpdate(BaseModel):
    is_enabled: Optional[bool] = None
    schedule_cron: Optional[str] = None


# --- Message Schemas ---

class MessageDraftCreate(BaseModel):
    order_id: Optional[int] = None
    customer_id: Optional[int] = None
    template_type: str
    language: str = "en"

class MessageDraftResponse(BaseModel):
    id: int
    order_id: Optional[int]
    customer_id: Optional[int]
    template_type: str
    language: str
    subject: Optional[str]
    body: str
    status: MessageStatus
    created_at: datetime
    approved_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)


# --- Approval Schemas ---

class ApprovalRequestResponse(BaseModel):
    id: int
    action_type: str
    description: str
    payload: Optional[str]
    status: str
    created_at: datetime
    resolved_at: Optional[datetime]
    result: Optional[str]
    model_config = ConfigDict(from_attributes=True)

class ApprovalDecision(BaseModel):
    approved: bool
    note: Optional[str] = None


# --- Notification Schemas ---

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: Optional[str]
    category: Optional[str]
    is_read: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# --- Dashboard Schemas ---

class DashboardData(BaseModel):
    today_priorities: List[dict] = []
    upcoming_exams: List[dict] = []
    due_assignments: List[dict] = []
    orders_needing_attention: List[dict] = []
    pending_payments: List[dict] = []
    packing_queue: List[dict] = []
    shipping_deadlines: List[dict] = []
    calendar_warnings: List[dict] = []
    stats: dict = {}
