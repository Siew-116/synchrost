"""Dashboard router — aggregated view of today's priorities."""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from app.database import get_db
from app.models import (
    AcademicEvent, Order, OrderStatus, EventPriority, EventType, User,
    BusinessException, ExceptionStatus
)
from app.schemas import DashboardData
from app.utils.auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/", response_model=DashboardData)
def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    now = datetime.utcnow()
    today = now.date()
    week_end = today + timedelta(days=7)

    # Today's academic priorities
    academic_events = db.query(AcademicEvent).filter(
        AcademicEvent.user_id == current_user.id,
        AcademicEvent.is_completed == False,
    ).all()

    today_priorities = []
    for event in academic_events:
        if event.start_datetime and event.start_datetime.date() == today:
            today_priorities.append({
                "id": event.id,
                "type": "academic",
                "title": event.title,
                "event_type": event.event_type.value,
                "priority": event.priority.value,
                "start_time": event.start_datetime.strftime("%H:%M") if event.start_datetime else None,
                "is_fixed": event.is_fixed,
            })

    # Sort by priority
    priority_order = {EventPriority.CRITICAL: 0, EventPriority.HIGH: 1, EventPriority.MEDIUM: 2, EventPriority.LOW: 3}
    today_priorities.sort(key=lambda x: priority_order.get(EventPriority(x["priority"]), 99))

    # Upcoming exams
    upcoming_exams = []
    for event in academic_events:
        if event.event_type == EventType.EXAM and event.start_datetime:
            days_until = (event.start_datetime.date() - today).days
            if 0 <= days_until <= 14:
                upcoming_exams.append({
                    "id": event.id,
                    "title": event.title,
                    "date": event.start_datetime.date().isoformat(),
                    "days_until": days_until,
                    "course_code": event.course_code,
                })
    upcoming_exams.sort(key=lambda x: x["days_until"])

    # Due assignments
    due_assignments = []
    for event in academic_events:
        if event.event_type in [EventType.ASSIGNMENT, EventType.COURSEWORK] and event.due_date:
            days_until = (event.due_date - today).days
            if 0 <= days_until <= 7:
                due_assignments.append({
                    "id": event.id,
                    "title": event.title,
                    "due_date": event.due_date.isoformat(),
                    "days_until": days_until,
                })
    due_assignments.sort(key=lambda x: x["days_until"])

    # Orders needing attention
    orders = db.query(Order).filter(Order.user_id == current_user.id).all()
    orders_needing_attention = []
    pending_payments = []
    packing_queue = []
    shipping_deadlines = []

    for order in orders:
        if order.status == OrderStatus.PENDING:
            orders_needing_attention.append({
                "id": order.id, "order_number": order.order_number,
                "status": order.status.value, "total": str(order.total),
            })
        elif order.status == OrderStatus.CONFIRMED:
            pending_payments.append({
                "id": order.id, "order_number": order.order_number,
                "customer_id": order.customer_id, "balance_due": str(order.balance_due),
            })
        elif order.status == OrderStatus.PAID:
            packing_queue.append({
                "id": order.id, "order_number": order.order_number,
                "estimated_packing_minutes": order.estimated_packing_minutes,
                "promised_dispatch_date": order.promised_dispatch_date.isoformat() if order.promised_dispatch_date else None,
            })
        elif order.status == OrderStatus.PACKED:
            if order.promised_dispatch_date:
                days_until = (order.promised_dispatch_date - today).days
                shipping_deadlines.append({
                    "id": order.id, "order_number": order.order_number,
                    "promised_dispatch_date": order.promised_dispatch_date.isoformat(),
                    "days_until": days_until,
                    "tracking_number": order.tracking_number,
                })

    shipping_deadlines.sort(key=lambda x: x["days_until"])

    # Open exceptions
    open_exceptions = db.query(BusinessException).filter(
        BusinessException.user_id == current_user.id,
        BusinessException.status.in_([ExceptionStatus.OPEN, ExceptionStatus.IN_PROGRESS]),
    ).count()

    # Calendar warnings (overdue assignments, imminent dispatch deadlines)
    calendar_warnings = []
    for a in due_assignments:
        if a["days_until"] <= 1:
            calendar_warnings.append({"type": "assignment_due", **a})
    for s in shipping_deadlines:
        if s["days_until"] <= 1:
            calendar_warnings.append({"type": "shipping_deadline", **s})

    stats = {
        "total_orders": len(orders),
        "pending_orders": len([o for o in orders if o.status == OrderStatus.PENDING]),
        "paid_orders": len([o for o in orders if o.status == OrderStatus.PAID]),
        "packed_orders": len([o for o in orders if o.status == OrderStatus.PACKED]),
        "open_exceptions": open_exceptions,
        "today_events": len(today_priorities),
        "upcoming_exams": len(upcoming_exams),
    }

    return DashboardData(
        today_priorities=today_priorities,
        upcoming_exams=upcoming_exams,
        due_assignments=due_assignments,
        orders_needing_attention=orders_needing_attention,
        pending_payments=pending_payments,
        packing_queue=packing_queue,
        shipping_deadlines=shipping_deadlines,
        calendar_warnings=calendar_warnings,
        stats=stats,
    )
