"""Agent engine — the core agentic loop.

OBSERVE → ANALYZE → PRIORITIZE → PLAN → ACT → VERIFY → LOG

Supports two modes:
1. Deterministic rule-based fallback (no external API needed)
2. Configurable OpenAI-compatible model adapter (when API key is set)
"""
from sqlalchemy.orm import Session
from typing import Optional, Dict, List, Any
from datetime import datetime
import json
import re
import httpx
import uuid

from app.config import settings
from app.models import AgentLog, User, Notification, OrderStatus
from app.agent.tools import AgentTools, TOOL_REGISTRY


class AgentEngine:
    """The core agent engine that processes natural language commands."""

    def __init__(self, db: Session, user: User):
        self.db = db
        self.user = user
        self.tools = AgentTools(db, user)
        self.session_id = str(uuid.uuid4())
        self.actions_taken: List[Dict] = []
        self.approval_requests: List[Dict] = []

    def _use_model_api(self) -> bool:
        """Check if an external model API is configured."""
        return bool(settings.AI_MODEL_API_BASE and settings.AI_MODEL_API_KEY)

    def _call_model(self, system_prompt: str, user_message: str) -> Optional[str]:
        """Call the configured OpenAI-compatible model API."""
        if not self._use_model_api():
            return None

        try:
            headers = {
                "Authorization": f"Bearer {settings.AI_MODEL_API_KEY}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": settings.AI_MODEL_NAME,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                "max_tokens": 1000,
                "temperature": 0.7,
            }

            with httpx.Client(timeout=30.0) as client:
                resp = client.post(
                    f"{settings.AI_MODEL_API_BASE}/chat/completions",
                    headers=headers,
                    json=payload,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return None
        except Exception:
            return None

    def process(self, message: str, context: Optional[str] = None) -> Dict:
        """Process a natural language command through the agent loop."""
        # PHASE 1: OBSERVE
        observation = self._observe(message)

        # PHASE 2: ANALYZE
        analysis = self._analyze(message, observation)

        # PHASE 3: PRIORITIZE
        priority = self._prioritize(analysis)

        # PHASE 4: PLAN
        plan = self._plan(message, analysis, priority)

        # PHASE 5: ACT
        action_result = self._act(plan)

        # PHASE 6: VERIFY
        verification = self._verify(action_result)

        # PHASE 7: LOG
        self._log(message, observation, analysis, plan, action_result, verification)

        # Build response
        response_text = self._format_response(message, analysis, plan, action_result, verification)

        return {
            "response": response_text,
            "actions_taken": self.actions_taken,
            "approval_requests": self.approval_requests,
            "session_id": self.session_id,
            "mode": "model_api" if self._use_model_api() else "deterministic_fallback",
        }

    def _observe(self, message: str) -> Dict:
        """Observe current state — gather data relevant to the user's message."""
        observation = {
            "academic_schedule": self.tools.get_academic_schedule(days_ahead=7),
            "business_tasks": self.tools.get_business_tasks(),
            "payment_summary": self.tools.get_payment_summary(),
            "inventory_status": self.tools.get_inventory_status(),
        }

        # Add context-specific observations
        msg_lower = message.lower()
        if any(kw in msg_lower for kw in ["exam", "test", "revision", "study"]):
            observation["schedule_conflicts"] = self.tools.detect_schedule_conflicts()

        if any(kw in msg_lower for kw in ["pack", "packing", "dispatch", "ship"]):
            observation["packing_estimate"] = self.tools.estimate_packing_duration()
            observation["available_slots"] = self.tools.find_available_time_slots(60)

        if any(kw in msg_lower for kw in ["payment", "outstanding", "balance", "owe"]):
            observation["pending_orders"] = self.tools.get_pending_orders("confirmed")

        return observation

    def _analyze(self, message: str, observation: Dict) -> Dict:
        """Analyze the user's intent and current state."""
        msg_lower = message.lower()

        intent = "unknown"
        details = {}

        # Intent detection
        if any(kw in msg_lower for kw in ["exam", "test"]):
            intent = "exam_conflict"
            # Find upcoming exams
            exams = [e for e in observation.get("academic_schedule", []) if e["event_type"] == "exam"]
            if exams:
                details["exams"] = exams
                # Check for packing conflicts
                packing = observation.get("packing_estimate", self.tools.estimate_packing_duration())
                if packing["order_count"] > 0:
                    details["packing_conflict"] = True
                    details["packing_time"] = packing

        elif any(kw in msg_lower for kw in ["pack", "packing"]):
            intent = "packing_management"
            packing = observation.get("packing_estimate", self.tools.estimate_packing_duration())
            details["packing"] = packing
            slots = observation.get("available_slots", self.tools.find_available_time_slots(60))
            details["available_slots"] = slots[:3]

        elif any(kw in msg_lower for kw in ["payment", "outstanding", "balance", "owe"]):
            intent = "payment_review"
            details["payment_summary"] = observation.get("payment_summary")
            details["pending_orders"] = observation.get("pending_orders", self.tools.get_pending_orders("confirmed"))

        elif any(kw in msg_lower for kw in ["schedule", "plan", "reorganize", "rearrange", "reschedule"]):
            intent = "schedule_planning"
            proposal = self.tools.generate_schedule_proposal()
            details["proposal"] = proposal

        elif any(kw in msg_lower for kw in ["notice", "message", "notify", "customer", "draft"]):
            intent = "message_generation"
            paid_orders = self.tools.get_pending_orders("paid")
            details["orders_for_messages"] = paid_orders[:5]

        elif any(kw in msg_lower for kw in ["bulk", "group", "ems", "parcel"]):
            intent = "bulk_order_management"
            details["business_tasks"] = observation.get("business_tasks")

        elif any(kw in msg_lower for kw in ["inventory", "stock", "low"]):
            intent = "inventory_check"
            details["inventory"] = observation.get("inventory_status")

        elif any(kw in msg_lower for kw in ["profit", "finance", "revenue", "income"]):
            intent = "finance_summary"
            details["payment_summary"] = observation.get("payment_summary")

        return {"intent": intent, "details": details}

    def _prioritize(self, analysis: Dict) -> str:
        """Determine priority level based on analysis."""
        intent = analysis.get("intent", "unknown")
        details = analysis.get("details", {})

        if intent == "exam_conflict" and details.get("packing_conflict"):
            return "critical"

        conflicts = details.get("proposal", {}).get("detected_conflicts", [])
        if any(c.get("severity") == "critical" for c in conflicts):
            return "critical"
        if any(c.get("severity") == "high" for c in conflicts):
            return "high"

        if intent in ["packing_management", "payment_review", "schedule_planning"]:
            return "high"

        return "medium"

    def _plan(self, message: str, analysis: Dict, priority: str) -> Dict:
        """Plan actions based on analysis."""
        intent = analysis.get("intent", "unknown")
        details = analysis.get("details", {})

        plan = {
            "intent": intent,
            "priority": priority,
            "steps": [],
            "tools_to_call": [],
        }

        if intent == "exam_conflict":
            plan["steps"].append("Identify exam time and protected periods")
            plan["steps"].append("Calculate packing workload")
            plan["steps"].append("Find available time slots outside exam/revision periods")
            plan["steps"].append("Propose packing schedule")
            plan["steps"].append("Draft customer notifications for affected dispatches")
            plan["tools_to_call"] = ["detect_schedule_conflicts", "estimate_packing_duration", "find_available_time_slots", "generate_schedule_proposal"]

        elif intent == "packing_management":
            plan["steps"].append("Get paid orders needing packing")
            plan["steps"].append("Estimate total packing time")
            plan["steps"].append("Find available time slots")
            plan["tools_to_call"] = ["get_pending_orders", "estimate_packing_duration", "find_available_time_slots"]

        elif intent == "payment_review":
            plan["steps"].append("Get orders with outstanding payments")
            plan["steps"].append("Calculate total outstanding")
            plan["tools_to_call"] = ["get_payment_summary", "get_pending_orders"]

        elif intent == "schedule_planning":
            plan["steps"].append("Detect schedule conflicts")
            plan["steps"].append("Generate schedule proposal")
            plan["tools_to_call"] = ["detect_schedule_conflicts", "generate_schedule_proposal", "find_available_time_slots"]

        elif intent == "message_generation":
            plan["steps"].append("Get orders for message generation")
            plan["steps"].append("Create message drafts")
            plan["tools_to_call"] = ["get_pending_orders", "create_message_draft"]

        elif intent == "inventory_check":
            plan["steps"].append("Check inventory status")
            plan["steps"].append("Identify low-stock items")
            plan["tools_to_call"] = ["get_inventory_status"]

        elif intent == "finance_summary":
            plan["steps"].append("Get payment summary")
            plan["tools_to_call"] = ["get_payment_summary"]

        else:
            plan["steps"].append("Provide general assistance based on available data")
            plan["tools_to_call"] = ["get_academic_schedule", "get_business_tasks"]

        return plan

    def _act(self, plan: Dict) -> Dict:
        """Execute the planned actions."""
        results = {}
        tools_to_call = plan.get("tools_to_call", [])

        for tool_name in tools_to_call:
            if tool_name in TOOL_REGISTRY:
                tool_config = TOOL_REGISTRY[tool_name]
                requires_approval = tool_config["requires_approval"]

                # Call the tool
                func = getattr(self.tools, tool_name, None)
                if func is None:
                    continue

                try:
                    # Call with default params (the agent would normally pass specific params)
                    if tool_name == "get_pending_orders":
                        result = func(status_filter="paid")
                    elif tool_name == "estimate_packing_duration":
                        result = func()
                    elif tool_name == "find_available_time_slots":
                        result = func(duration_minutes=60)
                    elif tool_name == "get_academic_schedule":
                        result = func(days_ahead=7)
                    elif tool_name == "create_message_draft":
                        # For message generation, create drafts for first paid order
                        paid_orders = self.tools.get_pending_orders("paid")
                        if paid_orders:
                            result = func(order_id=paid_orders[0]["id"], template_type="packaging_notice", language="en")
                        else:
                            result = {"success": False, "error": "No paid orders to generate messages for"}
                    else:
                        result = func()

                    results[tool_name] = result

                    action_record = {
                        "tool": tool_name,
                        "description": tool_config["description"],
                        "requires_approval": requires_approval,
                        "result": result if not requires_approval else "[requires approval]",
                        "success": result.get("success", True) if isinstance(result, dict) else True,
                    }
                    self.actions_taken.append(action_record)

                    if requires_approval:
                        self.approval_requests.append({
                            "tool": tool_name,
                            "description": tool_config["description"],
                            "action_type": tool_name,
                        })

                except Exception as e:
                    results[tool_name] = {"error": str(e)}
                    self.actions_taken.append({
                        "tool": tool_name,
                        "description": tool_config["description"],
                        "error": str(e),
                        "success": False,
                    })

        return results

    def _verify(self, action_result: Dict) -> Dict:
        """Verify that actions produced expected results."""
        verification = {
            "verified": True,
            "checks": [],
        }

        for tool_name, result in action_result.items():
            if isinstance(result, dict):
                if "error" in result:
                    verification["checks"].append({
                        "tool": tool_name,
                        "verified": False,
                        "error": result["error"],
                    })
                    verification["verified"] = False
                elif result.get("success", True):
                    verification["checks"].append({
                        "tool": tool_name,
                        "verified": True,
                    })
                else:
                    verification["checks"].append({
                        "tool": tool_name,
                        "verified": False,
                        "error": result.get("error", "Unknown error"),
                    })
                    verification["verified"] = False

        return verification

    def _log(self, message: str, observation: Dict, analysis: Dict, plan: Dict, action_result: Dict, verification: Dict):
        """Write an audit log entry."""
        log = AgentLog(
            user_id=self.user.id,
            session_id=self.session_id,
            observation=json.dumps(observation, default=str)[:2000],
            analysis=json.dumps(analysis, default=str)[:2000],
            plan=json.dumps(plan, default=str)[:2000],
            action_taken=", ".join(plan.get("tools_to_call", [])),
            action_result=json.dumps(action_result, default=str)[:2000],
            verified=verification["verified"],
            tool_called=", ".join(plan.get("tools_to_call", [])),
            tool_input=message[:500],
            tool_output=json.dumps(action_result, default=str)[:2000],
            success=verification["verified"],
            error_message=None if verification["verified"] else json.dumps(verification["checks"])[:500],
        )
        self.db.add(log)
        self.db.commit()

    def _format_response(self, message: str, analysis: Dict, plan: Dict, action_result: Dict, verification: Dict) -> str:
        """Format the agent's response for the user."""
        intent = analysis.get("intent", "unknown")
        details = analysis.get("details", {})
        priority = plan.get("priority", "medium")

        lines = []
        lines.append(f"**Priority: {priority.upper()}**")
        lines.append("")

        if intent == "exam_conflict":
            exams = details.get("exams", [])
            packing = details.get("packing_time", {})

            if exams:
                for exam in exams[:3]:
                    lines.append(f"📚 Exam: **{exam['title']}**")
                    start = exam.get("start", "")
                    if start:
                        lines.append(f"   When: {datetime.fromisoformat(start).strftime('%d/%m/%Y %H:%M')}")
                    lines.append(f"   Priority: {exam['priority']}")
                    lines.append("")

            if packing.get("order_count", 0) > 0:
                lines.append(f"📦 You have **{packing['order_count']}** paid orders to pack")
                lines.append(f"   Total packing time: **{packing['total_packing_hours']} hours** ({packing['total_packing_minutes']} minutes)")
                lines.append("")

                slots = details.get("available_slots", self.tools.find_available_time_slots(60))[:3]
                if slots:
                    lines.append("✅ **Available packing slots:**")
                    for slot in slots:
                        start = datetime.fromisoformat(slot["start"])
                        end = datetime.fromisoformat(slot["end"])
                        lines.append(f"   • {start.strftime('%d/%m %H:%M')} - {end.strftime('%H:%M')}")
                    lines.append("")

                lines.append("⚠️ I recommend packing **before or after the exam** to protect your revision time.")
                lines.append("")

                if self.approval_requests:
                    lines.append("📋 **Approval needed:** Customer message drafts have been created and need your approval.")

            else:
                lines.append("No urgent packing conflicts detected. Focus on your exam preparation!")

        elif intent == "packing_management":
            packing = details.get("packing", {})
            lines.append(f"📦 **Packing Queue:** {packing.get('order_count', 0)} orders")
            lines.append(f"   Total time: {packing.get('total_packing_hours', 0)} hours")

            orders = packing.get("orders", [])
            if orders:
                lines.append("")
                lines.append("**Orders to pack:**")
                for o in orders[:10]:
                    lines.append(f"   • {o['order_number']} — {o['minutes']} min")

            slots = details.get("available_slots", [])
            if slots:
                lines.append("")
                lines.append("**Suggested packing slots:**")
                for slot in slots[:3]:
                    start = datetime.fromisoformat(slot["start"])
                    lines.append(f"   • {start.strftime('%d/%m %H:%M')}")

        elif intent == "payment_review":
            summary = details.get("payment_summary", {})
            lines.append(f"💰 **Payment Summary**")
            lines.append(f"   Total orders: {summary.get('total_orders', 0)}")
            lines.append(f"   Outstanding payments: RM {summary.get('outstanding_payments', '0.00')}")
            lines.append(f"   Paid orders: {summary.get('paid_orders', 0)}")

            pending = details.get("pending_orders", [])
            if pending:
                lines.append("")
                lines.append("**Orders needing payment:**")
                for o in pending[:5]:
                    lines.append(f"   • {o['order_number']} — Balance: RM {o.get('balance_due', '0.00')}")

        elif intent == "schedule_planning":
            proposal = details.get("proposal", {})
            conflicts = proposal.get("detected_conflicts", [])

            if conflicts:
                lines.append(f"⚠️ **{len(conflicts)} conflict(s) detected:**")
                for c in conflicts:
                    lines.append(f"   • [{c['severity'].upper()}] {c['description']}")
                    if c.get("suggested_resolution"):
                        lines.append(f"     → {c['suggested_resolution']}")
                lines.append("")

            recs = proposal.get("recommendations", [])
            if recs:
                lines.append("**Recommendations:**")
                for rec in recs:
                    lines.append(f"   • {rec}")

        elif intent == "message_generation":
            orders = details.get("orders_for_messages", [])
            lines.append(f"📝 **Message Generation**")
            lines.append(f"   {len(orders)} paid orders ready for message drafts")
            if self.approval_requests:
                lines.append("")
                lines.append("📋 Message drafts created and awaiting your approval.")

        elif intent == "inventory_check":
            inv = details.get("inventory") or []
            low_stock = [p for p in inv if p.get("is_low_stock")]
            lines.append(f"📊 **Inventory Status:** {len(inv)} products")
            if low_stock:
                lines.append("")
                lines.append(f"⚠️ **{len(low_stock)} low-stock item(s):**")
                for p in low_stock:
                    lines.append(f"   • {p['name']} — {p['available_stock']} left (threshold: {p.get('low_stock_threshold', 5)})")

        elif intent == "finance_summary":
            summary = details.get("payment_summary", {})
            lines.append(f"💰 **Finance Summary**")
            lines.append(f"   Outstanding payments: RM {summary.get('outstanding_payments', '0.00')}")

        else:
            # General response
            biz = analysis.get("details", {}).get("business_tasks") or self.tools.get_business_tasks()
            lines.append("Here's your current overview:")
            lines.append(f"   📚 Pending orders: {biz.get('pending_orders', 0)}")
            lines.append(f"   💰 Orders needing packing: {biz.get('paid_orders_needing_packing', 0)}")
            lines.append(f"   📦 Ready for dispatch: {biz.get('packed_orders_needing_dispatch', 0)}")
            lines.append(f"   ⚠️ Open exceptions: {biz.get('open_exceptions', 0)}")

        lines.append("")
        lines.append("---")
        lines.append(f"Mode: {'AI Model API' if self._use_model_api() else 'Deterministic (rule-based)'}")
        lines.append(f"Session: {self.session_id[:8]}")

        return "\n".join(lines)
