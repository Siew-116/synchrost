"""Structured agent tools for StudyBiz AI.

Each tool is a validated internal function that enforces user permissions
and input validation. The agent calls these tools to observe, act, and verify.
"""
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any
from datetime import datetime, date, timedelta
from decimal import Decimal
from app.models import (
    AcademicEvent, Order, OrderStatus, Product, Customer, BulkOrder,
    Supplier, BusinessException, FinanceTransaction, AgentLog,
    MessageDraft, MessageStatus, Notification, EventType, EventPriority,
    User
)
import json


class AgentTools:
    """Collection of structured tools the AI agent can invoke."""

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user

    # --- Observation Tools (read-only, safe) ---

    def get_academic_schedule(self, days_ahead: int = 7) -> List[Dict]:
        """Retrieve academic events for the next N days."""
        now = datetime.utcnow()
        end = now + timedelta(days=days_ahead)
        events = self.db.query(AcademicEvent).filter(
            AcademicEvent.user_id == self.user.id,
            AcademicEvent.start_datetime >= now,
            AcademicEvent.start_datetime <= end,
        ).order_by(AcademicEvent.start_datetime.asc()).all()

        return [{
            "id": e.id,
            "title": e.title,
            "event_type": e.event_type.value,
            "priority": e.priority.value,
            "start": e.start_datetime.isoformat() if e.start_datetime else None,
            "end": e.end_datetime.isoformat() if e.end_datetime else None,
            "due_date": e.due_date.isoformat() if e.due_date else None,
            "is_fixed": e.is_fixed,
            "is_completed": e.is_completed,
            "estimated_duration_minutes": e.estimated_duration_minutes,
            "course_code": e.course_code,
            "location": e.location,
        } for e in events]

    def get_business_tasks(self) -> Dict:
        """Retrieve current business workload."""
        orders = self.db.query(Order).filter(Order.user_id == self.user.id).all()
        return {
            "pending_orders": len([o for o in orders if o.status == OrderStatus.PENDING]),
            "confirmed_orders": len([o for o in orders if o.status == OrderStatus.CONFIRMED]),
            "paid_orders_needing_packing": len([o for o in orders if o.status == OrderStatus.PAID]),
            "packed_orders_needing_dispatch": len([o for o in orders if o.status == OrderStatus.PACKED]),
            "open_exceptions": self.db.query(BusinessException).filter(
                BusinessException.user_id == self.user.id,
                BusinessException.status.in_(["open", "in_progress"]),
            ).count(),
        }

    def get_pending_orders(self, status_filter: str = "paid") -> List[Dict]:
        """Get orders in a specific status."""
        try:
            status_enum = OrderStatus(status_filter)
        except ValueError:
            return []
        orders = self.db.query(Order).filter(
            Order.user_id == self.user.id,
            Order.status == status_enum,
        ).order_by(Order.created_at.asc()).all()

        return [{
            "id": o.id,
            "order_number": o.order_number,
            "customer_id": o.customer_id,
            "total": str(o.total),
            "amount_paid": str(o.amount_paid),
            "estimated_packing_minutes": o.estimated_packing_minutes,
            "promised_dispatch_date": o.promised_dispatch_date.isoformat() if o.promised_dispatch_date else None,
        } for o in orders]

    def get_inventory_status(self) -> List[Dict]:
        """Get inventory status including low-stock alerts."""
        products = self.db.query(Product).filter(
            Product.user_id == self.user.id,
            Product.is_active == True,
        ).all()
        return [{
            "id": p.id,
            "name": p.name,
            "available_stock": p.available_stock,
            "reserved_stock": p.reserved_stock,
            "incoming_stock": p.incoming_stock,
            "is_low_stock": p.available_stock <= p.low_stock_threshold,
        } for p in products]

    def get_payment_summary(self) -> Dict:
        """Get payment summary."""
        orders = self.db.query(Order).filter(Order.user_id == self.user.id).all()
        total_outstanding = sum(
            (o.balance_due for o in orders if o.balance_due and o.balance_due > 0
             and o.status not in [OrderStatus.CANCELLED, OrderStatus.DELIVERED]),
            Decimal("0")
        )
        return {
            "total_orders": len(orders),
            "outstanding_payments": str(total_outstanding),
            "paid_orders": len([o for o in orders if o.status in [OrderStatus.PAID, OrderStatus.PACKED, OrderStatus.DISPATCHED]]),
        }

    # --- Analysis Tools (read-only computation) ---

    def detect_schedule_conflicts(self) -> List[Dict]:
        """Detect conflicts between academic and business events."""
        conflicts = []
        now = datetime.utcnow()
        week_end = now + timedelta(days=7)

        events = self.db.query(AcademicEvent).filter(
            AcademicEvent.user_id == self.user.id,
            AcademicEvent.is_completed == False,
            AcademicEvent.start_datetime >= now,
            AcademicEvent.start_datetime <= week_end,
        ).order_by(AcademicEvent.start_datetime.asc()).all()

        paid_orders = self.db.query(Order).filter(
            Order.user_id == self.user.id,
            Order.status == OrderStatus.PAID,
        ).all()

        total_packing_time = sum((o.estimated_packing_minutes for o in paid_orders), 0)

        # Check for exam conflicts with business tasks
        for event in events:
            if event.event_type == EventType.EXAM:
                # Check if there are packing tasks near the exam
                exam_start = event.start_datetime
                exam_end = event.end_datetime or (exam_start + timedelta(hours=2))
                conflicts.append({
                    "type": "exam_vs_business",
                    "severity": "critical",
                    "description": f"Exam '{event.title}' on {exam_start.strftime('%d/%m/%Y %H:%M')}. "
                                   f"{len(paid_orders)} orders need packing ({total_packing_time} min total).",
                    "exam_id": event.id,
                    "affected_orders": len(paid_orders),
                    "packing_time_minutes": total_packing_time,
                    "suggested_resolution": "Reschedule packing to before/after exam. Protect revision time.",
                })

        # Check for overlapping events
        for i, e1 in enumerate(events):
            for e2 in events[i+1:]:
                if e1.start_datetime and e2.start_datetime and e1.end_datetime and e2.end_datetime:
                    if e1.start_datetime < e2.end_datetime and e2.start_datetime < e1.end_datetime:
                        if e1.is_fixed and e2.is_fixed:
                            conflicts.append({
                                "type": "double_booking",
                                "severity": "critical",
                                "description": f"'{e1.title}' overlaps with '{e2.title}'",
                                "event_ids": [e1.id, e2.id],
                                "suggested_resolution": "One fixed event must be moved with permission.",
                            })

        # Check for workload overload (more than 4 hours of tasks in a window)
        # Simplified: check if total estimated duration in a day exceeds 10 hours
        day_groups: Dict[date, int] = {}
        for event in events:
            if event.start_datetime:
                day = event.start_datetime.date()
                day_groups[day] = day_groups.get(day, 0) + event.estimated_duration_minutes

        for day, total_minutes in day_groups.items():
            if total_minutes > 600:  # 10 hours
                conflicts.append({
                    "type": "workload_overload",
                    "severity": "high",
                    "description": f"Total estimated task time on {day.strftime('%d/%m/%Y')}: {total_minutes} min ({total_minutes/60:.1f}h). Exceeds 10h limit.",
                    "day": day.isoformat(),
                    "total_minutes": total_minutes,
                    "suggested_resolution": "Redistribute flexible tasks to other days.",
                })

        return conflicts

    def estimate_packing_duration(self, order_ids: Optional[List[int]] = None) -> Dict:
        """Estimate packing time for orders."""
        q = self.db.query(Order).filter(
            Order.user_id == self.user.id,
            Order.status == OrderStatus.PAID,
        )
        if order_ids:
            q = q.filter(Order.id.in_(order_ids))

        orders = q.all()
        total_minutes = sum((o.estimated_packing_minutes for o in orders), 0)
        return {
            "order_count": len(orders),
            "total_packing_minutes": total_minutes,
            "total_packing_hours": round(total_minutes / 60, 1),
            "orders": [{"id": o.id, "order_number": o.order_number, "minutes": o.estimated_packing_minutes} for o in orders],
        }

    def find_available_time_slots(
        self, duration_minutes: int, search_days: int = 7
    ) -> List[Dict]:
        """Find available time slots of the given duration."""
        now = datetime.utcnow()
        end = now + timedelta(days=search_days)

        # Get all scheduled events
        events = self.db.query(AcademicEvent).filter(
            AcademicEvent.user_id == self.user.id,
            AcademicEvent.start_datetime >= now,
            AcademicEvent.start_datetime <= end,
        ).order_by(AcademicEvent.start_datetime.asc()).all()

        # Working hours
        work_start = int(self.user.working_hours_start.split(":")[0])
        work_end = int(self.user.working_hours_end.split(":")[0])

        slots = []
        current = now.replace(minute=0, second=0, microsecond=0)
        if current.hour < work_start:
            current = current.replace(hour=work_start)
        if current.hour >= work_end:
            current = current + timedelta(days=1)
            current = current.replace(hour=work_start)

        while current < end:
            slot_end = current + timedelta(minutes=duration_minutes)

            # Check if slot is within working hours
            if slot_end.hour > work_end or (slot_end.hour == work_end and slot_end.minute > 0):
                current = current + timedelta(days=1)
                current = current.replace(hour=work_start)
                continue

            # Check for conflicts with existing events
            is_free = True
            for event in events:
                if event.start_datetime and event.end_datetime:
                    if current < event.end_datetime and event.start_datetime < slot_end:
                        is_free = False
                        break

            if is_free:
                slots.append({
                    "start": current.isoformat(),
                    "end": slot_end.isoformat(),
                    "duration_minutes": duration_minutes,
                })
                if len(slots) >= 10:  # Limit results
                    break

            current = current + timedelta(minutes=30)

        return slots

    # --- Action Tools (require verification) ---

    def create_internal_task(
        self, title: str, event_type: str, start_datetime: str,
        duration_minutes: int = 60, priority: str = "medium",
        notes: Optional[str] = None
    ) -> Dict:
        """Create an internal task (e.g., packing session)."""
        try:
            etype = EventType(event_type)
            epriority = EventPriority(priority)
            start = datetime.fromisoformat(start_datetime)
            end = start + timedelta(minutes=duration_minutes)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        event = AcademicEvent(
            user_id=self.user.id,
            title=title,
            event_type=etype,
            priority=epriority,
            start_datetime=start,
            end_datetime=end,
            estimated_duration_minutes=duration_minutes,
            is_fixed=False,
            notes=notes or "Created by AI Agent",
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)

        return {
            "success": True,
            "id": event.id,
            "title": event.title,
            "start": event.start_datetime.isoformat(),
        }

    def update_flexible_task(self, event_id: int, new_start: str) -> Dict:
        """Move a flexible task to a new time slot."""
        event = self.db.query(AcademicEvent).filter(
            AcademicEvent.id == event_id,
            AcademicEvent.user_id == self.user.id,
        ).first()
        if not event:
            return {"success": False, "error": "Event not found"}
        if event.is_fixed:
            return {"success": False, "error": "Cannot move fixed event without permission"}

        try:
            start = datetime.fromisoformat(new_start)
        except ValueError as e:
            return {"success": False, "error": str(e)}

        old_start = event.start_datetime
        duration = event.estimated_duration_minutes
        event.start_datetime = start
        event.end_datetime = start + timedelta(minutes=duration)
        self.db.commit()

        return {
            "success": True,
            "id": event.id,
            "old_start": old_start.isoformat() if old_start else None,
            "new_start": start.isoformat(),
        }

    def create_message_draft(
        self, order_id: int, template_type: str, language: str = "en"
    ) -> Dict:
        """Create a customer message draft (requires approval to send)."""
        order = self.db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == self.user.id,
        ).first()
        if not order:
            return {"success": False, "error": "Order not found"}

        # This creates a draft — actual sending requires approval
        msg = MessageDraft(
            user_id=self.user.id,
            order_id=order_id,
            customer_id=order.customer_id,
            template_type=template_type,
            language=language,
            subject=f"{template_type.replace('_', ' ').title()} - {order.order_number}",
            body="[Auto-generated draft — please review]",
            status=MessageStatus.DRAFTED,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)

        return {
            "success": True,
            "message_id": msg.id,
            "status": msg.status.value,
            "note": "Draft created. Requires approval before sending.",
        }

    def create_business_alert(
        self, title: str, message: str, category: str = "business"
    ) -> Dict:
        """Create an in-app notification/alert."""
        notif = Notification(
            user_id=self.user.id,
            title=title,
            message=message,
            category=category,
            is_read=False,
        )
        self.db.add(notif)
        self.db.commit()
        self.db.refresh(notif)
        return {"success": True, "notification_id": notif.id}

    def verify_agent_action(self, action_id: str, expected_state: Dict) -> Dict:
        """Verify that an action produced the expected state."""
        # Generic verification — check if the expected record exists
        if "event_id" in expected_state:
            event = self.db.query(AcademicEvent).filter(
                AcademicEvent.id == expected_state["event_id"],
                AcademicEvent.user_id == self.user.id,
            ).first()
            if event:
                return {
                    "verified": True,
                    "actual_state": {
                        "id": event.id,
                        "title": event.title,
                        "start": event.start_datetime.isoformat() if event.start_datetime else None,
                        "is_completed": event.is_completed,
                    },
                }
            return {"verified": False, "error": "Event not found after action"}

        return {"verified": False, "error": "No verification criteria provided"}

    def get_action_history(self, limit: int = 20) -> List[Dict]:
        """Get recent agent action history."""
        logs = self.db.query(AgentLog).filter(
            AgentLog.user_id == self.user.id,
        ).order_by(AgentLog.created_at.desc()).limit(limit).all()

        return [{
            "id": log.id,
            "action": log.action_taken,
            "tool": log.tool_called,
            "success": log.success,
            "verified": log.verified,
            "created_at": log.created_at.isoformat(),
        } for log in logs]

    def generate_schedule_proposal(
        self, constraint: str = "default"
    ) -> Dict:
        """Generate a proposed schedule balancing academic and business tasks."""
        conflicts = self.detect_schedule_conflicts()
        packing = self.estimate_packing_duration()
        slots = self.find_available_time_slots(
            max(packing["total_packing_minutes"], 60) if packing["total_packing_minutes"] > 0 else 60
        )

        proposal = {
            "packing_workload": packing,
            "detected_conflicts": conflicts,
            "available_slots": slots[:5],
            "recommendations": [],
        }

        if packing["order_count"] > 0:
            proposal["recommendations"].append(
                f"You have {packing['order_count']} orders to pack ({packing['total_packing_hours']}h). "
                f"Suggested: split into 2-3 sessions of ~1h each."
            )

        for conflict in conflicts:
            if conflict["type"] == "exam_vs_business":
                proposal["recommendations"].append(
                    f"CRITICAL: {conflict['description']} Move packing before/after the exam."
                )
            elif conflict["type"] == "workload_overload":
                proposal["recommendations"].append(
                    f"OVERLOAD: {conflict['description']} Redistribute tasks."
                )

        if not conflicts and packing["order_count"] == 0:
            proposal["recommendations"].append("No urgent conflicts detected. Schedule looks manageable.")

        return proposal


# Tool registry for the agent
TOOL_REGISTRY = {
    "get_academic_schedule": {
        "func": "get_academic_schedule",
        "description": "Retrieve academic events for the next N days",
        "requires_approval": False,
        "params": {"days_ahead": "int (default 7)"},
    },
    "get_business_tasks": {
        "func": "get_business_tasks",
        "description": "Get current business workload summary",
        "requires_approval": False,
        "params": {},
    },
    "get_pending_orders": {
        "func": "get_pending_orders",
        "description": "Get orders in a specific status",
        "requires_approval": False,
        "params": {"status_filter": "str (default 'paid')"},
    },
    "get_inventory_status": {
        "func": "get_inventory_status",
        "description": "Check inventory including low-stock alerts",
        "requires_approval": False,
        "params": {},
    },
    "get_payment_summary": {
        "func": "get_payment_summary",
        "description": "Get payment and outstanding balance summary",
        "requires_approval": False,
        "params": {},
    },
    "detect_schedule_conflicts": {
        "func": "detect_schedule_conflicts",
        "description": "Detect conflicts between academic and business events",
        "requires_approval": False,
        "params": {},
    },
    "estimate_packing_duration": {
        "func": "estimate_packing_duration",
        "description": "Estimate packing time for paid orders",
        "requires_approval": False,
        "params": {"order_ids": "list[int] (optional)"},
    },
    "find_available_time_slots": {
        "func": "find_available_time_slots",
        "description": "Find available time slots for a given duration",
        "requires_approval": False,
        "params": {"duration_minutes": "int", "search_days": "int (default 7)"},
    },
    "create_internal_task": {
        "func": "create_internal_task",
        "description": "Create an internal task (e.g., packing session)",
        "requires_approval": False,
        "params": {"title": "str", "event_type": "str", "start_datetime": "str", "duration_minutes": "int", "priority": "str", "notes": "str"},
    },
    "update_flexible_task": {
        "func": "update_flexible_task",
        "description": "Move a flexible task to a new time",
        "requires_approval": False,
        "params": {"event_id": "int", "new_start": "str"},
    },
    "create_message_draft": {
        "func": "create_message_draft",
        "description": "Create a customer message draft",
        "requires_approval": True,
        "params": {"order_id": "int", "template_type": "str", "language": "str"},
    },
    "create_business_alert": {
        "func": "create_business_alert",
        "description": "Create an in-app alert",
        "requires_approval": False,
        "params": {"title": "str", "message": "str", "category": "str"},
    },
    "generate_schedule_proposal": {
        "func": "generate_schedule_proposal",
        "description": "Generate a proposed schedule balancing academic and business",
        "requires_approval": False,
        "params": {"constraint": "str"},
    },
    "get_action_history": {
        "func": "get_action_history",
        "description": "Get recent agent action history",
        "requires_approval": False,
        "params": {"limit": "int (default 20)"},
    },
    "verify_agent_action": {
        "func": "verify_agent_action",
        "description": "Verify that an action produced expected state",
        "requires_approval": False,
        "params": {"action_id": "str", "expected_state": "dict"},
    },
}
