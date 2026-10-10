"""AI Agent service for StudyBiz AI.

This module implements a tool-using AI agent that:
1. Understands customer messages
2. Extracts order information
3. Validates against business rules
4. Executes permitted actions via tools
5. Generates responses

In demo mode (no LLM key), it uses deterministic intent matching.
With an LLM key, it calls the LLM with tool definitions.
"""
import json
import re
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.database import (
    Campaign, Product, ProductVariant, Customer, Order, OrderItem,
    Payment, Conversation, Message, Exception_, ActionLog, AutomationRule
)


class AgentTools:
    """Business operation tools available to the AI agent.

    Each method validates inputs and enforces business rules.
    The backend, not the LLM, enforces permissions, valid state
    transitions, stock limits, deadlines, and approval requirements.
    """

    def __init__(self, db: Session):
        self.db = db

    def log_action(self, actor_type, action_type, entity_type, entity_id, input_summary, result):
        log = ActionLog(
            actor_type=actor_type,
            action_type=action_type,
            entity_type=entity_type,
            entity_id=entity_id,
            input_summary=input_summary,
            result=result,
        )
        self.db.add(log)
        self.db.commit()
        return log.id

    def get_campaign(self, campaign_id=None):
        if campaign_id:
            c = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        else:
            c = self.db.query(Campaign).filter(Campaign.status == "open").first()
        if not c:
            return None
        return {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "status": c.status,
            "opens_at": c.opens_at.isoformat() if c.opens_at else None,
            "closes_at": c.closes_at.isoformat() if c.closes_at else None,
            "payment_instructions": c.payment_instructions,
            "late_order_policy": c.late_order_policy,
        }

    def get_product_availability(self, campaign_id):
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return None
        products = self.db.query(Product).filter(Product.campaign_id == campaign_id).all()
        result = []
        for p in products:
            variants = self.db.query(ProductVariant).filter(ProductVariant.product_id == p.id).all()
            for v in variants:
                ordered_qty = self.db.query(OrderItem).filter(
                    OrderItem.product_variant_id == v.id,
                    OrderItem.order.has(Order.status.in_(["pending_payment", "confirmed", "completed"]))
                )
                ordered_qty = sum(item.quantity for item in ordered_qty)
                available = (v.available_quantity or 0) - ordered_qty
                result.append({
                    "variant_id": v.id,
                    "product_name": p.name,
                    "attributes": v.attributes,
                    "price": p.price,
                    "available": max(0, available),
                    "stock_limit": v.available_quantity,
                })
        return result

    def get_customer_orders(self, customer_id):
        orders = self.db.query(Order).filter(Order.customer_id == customer_id).all()
        return [{
            "id": o.id,
            "status": o.status,
            "payment_status": o.payment_status,
            "fulfilment_status": o.fulfilment_status,
            "total_amount": o.total_amount,
            "items": [{"variant": v.attributes, "quantity": oi.quantity, "unit_price": oi.unit_price}
                      for oi in o.items for v in [oi.variant]],
        } for o in orders]

    
    def find_or_create_customer(
        self,
        display_name,
        telegram_user_id=None,
        telegram_username=None,
    ):
        """Find an existing Telegram customer or create one."""
    
        # A stable Telegram ID is required for reliable customer matching.
        if telegram_user_id is None or not str(telegram_user_id).strip():
            raise ValueError(
                "telegram_user_id is required to identify a Telegram customer."
            )
    
        telegram_user_id = str(telegram_user_id).strip()
    
        customer = (
            self.db.query(Customer)
            .filter(Customer.telegram_user_id == telegram_user_id)
            .first()
        )
    
        if customer:
            customer.display_name = display_name or customer.display_name
    
            if telegram_username is not None:
                customer.telegram_username = telegram_username
    
            self.db.commit()
            self.db.refresh(customer)
            print(
                f"[CUSTOMER DEBUG] Reused customer_id={customer.id}, "
                f"telegram_user_id={telegram_user_id}"
            )
            return customer
    
        customer = Customer(
            display_name=display_name or "Telegram Customer",
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
        )
    
        self.db.add(customer)
        self.db.commit()
        self.db.refresh(customer)
    
        print(
            f"[CUSTOMER DEBUG] Created customer_id={customer.id}, "
            f"telegram_user_id={telegram_user_id}"
        )
    
        return customer


    def create_pending_order(self, campaign_id, customer_id, variant_id, quantity):
        """Create a pending order. Validates campaign status, variant, and capacity."""
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return {"success": False, "error": "Campaign not found"}

        now = datetime.now(timezone.utc)

        # Check deadline
        if campaign.closes_at:
            closes_at = campaign.closes_at
        
            # Treat timezone-naive database timestamps as UTC
            if closes_at.tzinfo is None:
                closes_at = closes_at.replace(tzinfo=timezone.utc)
            else:
                closes_at = closes_at.astimezone(timezone.utc)
            if now > closes_at:
                # Make the current time timezone-aware in UTC
                if now.tzinfo is None:
                    now = now.replace(tzinfo=timezone.utc)
                else:
                    now = now.astimezone(timezone.utc)
                if campaign.late_order_policy == "reject":
                    return {"success": False, "error": "Order deadline has passed. Late orders are not accepted."}
                elif campaign.late_order_policy == "allow_with_approval":
                    # Create exception for approval
                    order = Order(
                        campaign_id=campaign_id,
                        customer_id=customer_id,
                        status="draft",
                        payment_status="unpaid",
                        fulfilment_status="not_ready",
                        total_amount=0,
                    )
                    self.db.add(order)
                    self.db.flush()
    
                    variant = self.db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
                    if variant:
                        item = OrderItem(
                            order_id=order.id,
                            product_variant_id=variant_id,
                            quantity=quantity,
                            unit_price=variant.product.price,
                        )
                        self.db.add(item)
                        order.total_amount = variant.product.price * quantity
    
                    exc = Exception_(
                        type="late_order",
                        order_id=order.id,
                        description=f"Customer requested order after deadline. Campaign: {campaign.name}. Late order policy: allow_with_approval.",
                        recommended_action="Review and approve or reject the late order request.",
                        status="open",
                    )
                    self.db.add(exc)
                    self.db.commit()
    
                    self.log_action("ai", "create_exception", "exception", exc.id,
                                    "Late order after deadline", "Exception created for approval")
                    return {
                        "success": False,
                        "error": "Order deadline has passed. Your request has been forwarded to the admin for approval.",
                        "exception_id": exc.id,
                        "order_id": order.id,
                    }

        variant = self.db.query(ProductVariant).filter(ProductVariant.id == variant_id).first()
        if not variant:
            return {"success": False, "error": "Product variant not found"}

        # Check available capacity
        ordered_qty = sum(item.quantity for item in self.db.query(OrderItem).filter(
            OrderItem.product_variant_id == variant_id,
            OrderItem.order.has(Order.status.in_(["pending_payment", "confirmed", "completed"]))
        ))
        available = (variant.available_quantity or 0) - ordered_qty
        if quantity > available:
            return {
                "success": False,
                "error": f"Insufficient stock. Requested {quantity}, available {available}.",
            }

        # Create order
        total = variant.product.price * quantity
        order = Order(
            campaign_id=campaign_id,
            customer_id=customer_id,
            status="pending_payment",
            payment_status="unpaid",
            fulfilment_status="not_ready",
            total_amount=total,
        )
        self.db.add(order)
        self.db.flush()

        item = OrderItem(
            order_id=order.id,
            product_variant_id=variant_id,
            quantity=quantity,
            unit_price=variant.product.price,
        )
        self.db.add(item)
        self.db.commit()
        self.db.refresh(order)

        self.log_action("ai", "create_pending_order", "order", order.id,
                        f"Created order for variant {variant.attributes}, qty {quantity}",
                        f"Order {order.id} created with status pending_payment")
        return {
            "success": True,
            "order_id": order.id,
            "status": "pending_payment",
            "total_amount": total,
            "payment_instructions": campaign.payment_instructions,
        }

    def update_order(self, order_id, changes):
        """Update an order. Enforces state transition rules."""
        order = self.db.query(Order).filter(Order.id == order_id).first()
        if not order:
            return {"success": False, "error": "Order not found"}

        if "status" in changes:
            valid_transitions = {
                "draft": ["pending_payment", "cancelled"],
                "pending_payment": ["confirmed", "cancelled"],
                "confirmed": ["completed", "cancelled"],
                "completed": [],
                "cancelled": [],
            }
            current = order.status
            target = changes["status"]
            if target not in valid_transitions.get(current, []):
                return {"success": False, "error": f"Cannot transition from {current} to {target}"}
            order.status = target

        if "payment_status" in changes:
            order.payment_status = changes["payment_status"]

        if "fulfilment_status" in changes:
            order.fulfilment_status = changes["fulfilment_status"]

        order.updated_at = datetime.now(timezone.utc)
        self.db.commit()

        self.log_action("ai", "update_order", "order", order.id,
                        f"Updated order {order_id}", f"Changes applied: {changes}")
        return {"success": True, "order_id": order.id}

    def request_cancellation(self, order_id, customer_id):
        """Create a cancellation request. Does not immediately cancel."""
        order = self.db.query(Order).filter(Order.id == order_id, Order.customer_id == customer_id).first()
        if not order:
            return {"success": False, "error": "Order not found"}

        if order.payment_status == "paid":
            # Cancellation of paid order requires approval
            exc = Exception_(
                type="cancellation_request",
                order_id=order.id,
                description=f"Customer requested cancellation of a paid order (RM{order.total_amount}). Refund policy applies.",
                recommended_action="Review cancellation and refund policy. Approve or reject.",
                status="open",
            )
            self.db.add(exc)
            self.db.commit()
            self.log_action("ai", "create_exception", "exception", exc.id,
                            "Cancellation request for paid order", "Exception created")
            return {
                "success": False,
                "error": "This order has been paid. Cancellation requires admin approval. Your request has been forwarded.",
                "exception_id": exc.id,
            }

        # Cancellation before payment - allowed by default policy
        order.status = "cancelled"
        order.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.log_action("ai", "request_cancellation", "order", order.id,
                        "Cancellation of unpaid order", "Order cancelled")
        return {"success": True, "order_id": order.id, "status": "cancelled"}

    def calculate_group_buy_totals(self, campaign_id):
        """Calculate total quantities by variant from eligible orders."""
        orders = self.db.query(Order).filter(
            Order.campaign_id == campaign_id,
            Order.status.in_(["pending_payment", "confirmed", "completed"]),
        ).all()

        totals = {}
        excluded = 0
        for order in orders:
            for item in order.items:
                variant = item.variant
                key = variant.attributes
                if key not in totals:
                    totals[key] = 0
                totals[key] += item.quantity

        cancelled = self.db.query(Order).filter(
            Order.campaign_id == campaign_id,
            Order.status == "cancelled",
        ).count()

        unresolved_exceptions = self.db.query(Exception_).filter(
            Exception_.status == "open",
            Exception_.order_id.isnot(None),
        ).join(Order, Exception_.order_id == Order.id).filter(
            Order.campaign_id == campaign_id
        ).count()

        return {
            "campaign_id": campaign_id,
            "totals_by_variant": totals,
            "total_units": sum(totals.values()),
            "excluded_cancelled": cancelled,
            "unresolved_exceptions": unresolved_exceptions,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def generate_supplier_summary(self, campaign_id):
        """Generate a supplier-ready summary."""
        totals = self.calculate_group_buy_totals(campaign_id)
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()

        is_final = campaign.status == "closed" and totals["unresolved_exceptions"] == 0

        return {
            "campaign_name": campaign.name if campaign else "Unknown",
            "variants": totals["totals_by_variant"],
            "total_units": totals["total_units"],
            "excluded_cancelled": totals["excluded_cancelled"],
            "unresolved_exceptions": totals["unresolved_exceptions"],
            "is_final": is_final,
            "generated_at": totals["generated_at"],
        }

    def create_exception(self, etype, order_id, description, recommended_action):
        exc = Exception_(
            type=etype,
            order_id=order_id,
            description=description,
            recommended_action=recommended_action,
            status="open",
        )
        self.db.add(exc)
        self.db.commit()
        self.log_action("ai", "create_exception", "exception", exc.id,
                        f"Exception: {etype}", "Exception created")
        return {"success": True, "exception_id": exc.id}

    def retrieve_approved_faq(self, campaign_id, question):
        """Answer common questions using approved product information."""
        campaign = self.db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            return "I could not find an active group buy."

        q_lower = question.lower()

        # Check common questions
        if any(w in q_lower for w in ["price", "how much", "cost", "rm"]):
            products = self.db.query(Product).filter(Product.campaign_id == campaign_id).all()
            prices = ", ".join([f"{p.name}: RM{p.price:.2f}" for p in products])
            return f"Prices: {prices}."

        if any(w in q_lower for w in ["size", "variant", "color", "colour", "available"]):
            availability = self.get_product_availability(campaign_id)
            variants = ", ".join([f"{a['attributes']} ({a['available']} left)" for a in availability])
            return f"Available variants: {variants}."

        if any(w in q_lower for w in ["deadline", "close", "end", "last day"]):
            if campaign.closes_at:
                return f"The group buy closes on {campaign.closes_at.strftime('%d %b %Y, %H:%M UTC')}."
            return "No closing date has been set yet."

        if any(w in q_lower for w in ["payment", "pay", "transfer", "bank"]):
            return f"Payment instructions: {campaign.payment_instructions}"

        if any(w in q_lower for w in ["open", "still", "active", "available"]):
            if campaign.status == "open":
                return f"Yes, {campaign.name} is currently open."
            return f"The group buy is currently {campaign.status}."

        return f"{campaign.description}"

    def draft_customer_message(self, content):
        """Draft a customer message without sending it."""
        return {"draft": content, "status": "drafted"}

    def send_customer_message(self, conversation_id, content, order_id=None):
        """Send a message to a customer conversation."""
        msg = Message(
            conversation_id=conversation_id,
            order_id=order_id,
            sender_type="ai",
            content=content,
            intent="response",
        )
        self.db.add(msg)
        self.db.commit()
        self.log_action("ai", "send_customer_message", "message", msg.id,
                        f"Sent: {content[:50]}...", "Message sent")
        return {"success": True, "message_id": msg.id}

    def get_dashboard_metrics(self):
        """Calculate dashboard metrics from actual database records."""
        active_campaigns = self.db.query(Campaign).filter(Campaign.status == "open").count()
        total_orders = self.db.query(Order).count()
        pending_payment = self.db.query(Order).filter(Order.status == "pending_payment").count()
        verifying_payments = self.db.query(Order).filter(Order.payment_status == "verifying").count()
        admin_attention = self.db.query(Order).filter(Order.status.in_(["draft", "pending_payment"])).count()
        unresolved_enquiries = self.db.query(Conversation).filter(Conversation.status == "open").count()
        open_exceptions = self.db.query(Exception_).filter(Exception_.status == "open").count()
        automated_actions = self.db.query(ActionLog).filter(ActionLog.actor_type == "ai").count()

        return {
            "active_group_buys": active_campaigns,
            "total_orders": total_orders,
            "orders_awaiting_payment": pending_payment,
            "payments_awaiting_verification": verifying_payments,
            "orders_requiring_admin_attention": admin_attention,
            "unresolved_customer_enquiries": unresolved_enquiries,
            "open_exceptions": open_exceptions,
            "automated_actions_completed": automated_actions,
        }


class AIAgent:
    """Main AI agent that processes customer messages and admin queries.

    In demo mode, uses deterministic intent matching.
    With an LLM key, calls the LLM with tool definitions.
    """

    # Keywords for intent classification
    INTENT_KEYWORDS = {
        "new_order": [
            "order", "buy", "want", "get", "purchase",
            "book", "i want", "i would like"
        ],
        "order_change": [
            "change", "add", "modify", "switch", "swap", "instead"
        ],
        "payment_enquiry": [
            "paid", "transfer", "payment", "money",
            "bank", "receipt", "screenshot"
        ],
        "order_status": [
            "status", "track", "where", "when",
            "arrive", "deliver", "dispatch"
        ],
        "cancellation": [
            "cancel", "refund", "withdraw", "stop"
        ],
        "complaint": [
            "complaint", "wrong", "bad", "broken",
            "issue", "problem", "angry"
        ],
        "product_question": [
            "product", "products", "what products",
            "what do you sell", "available", "availability",
            "price", "size", "colour", "color",
            "how much", "deadline", "close", "open",
            "what items", "catalogue", "catalog"
        ]
    }

    def __init__(self, db: Session, llm_api_key: str = "", demo_mode: bool = True):
        self.db = db
        self.tools = AgentTools(db)
        self.llm_api_key = llm_api_key
        self.demo_mode = demo_mode or not llm_api_key

    
    def find_variant(self, campaign_id, color, size):
        """Find an available product variant matching colour and size."""
    
        availability = self.tools.get_product_availability(campaign_id)
    
        color = color.lower().strip()
        size = size.upper().strip()
    
        for variant in availability:
            attributes = str(variant.get("attributes", "")).lower()
    
            # Match both colour and size in the variant attributes.
            if color in attributes and size in attributes.upper():
                return variant
    
        return None

    def classify_intent(self, text):
        text_lower = text.lower().strip()
    
        # Recognise replies containing order details.
        order_info = self.extract_order_info(text)
    
        if (
            order_info["quantity"] is not None
            and order_info["color"] is not None
            and order_info["size"] is not None
        ):
            return "new_order"
    
        # Keep your existing keyword-counting logic below.
        scores = {}
    
        for intent, keywords in self.INTENT_KEYWORDS.items():
            scores[intent] = sum(
                1 for keyword in keywords
                if keyword in text_lower
            )
    
        best_intent = max(scores, key=scores.get)
    
        if scores[best_intent] == 0:
            return "other"
    
        return best_intent

    
    def extract_order_info(self, text):
        """Extract quantity, colour, and size from order-related text."""
        text_lower = text.lower()
    
        # Remove numeric sizes before extracting quantity.
        quantity_text = re.sub(
            r"\bsize\s*\d+\b",
            " ",
            text_lower,
        )
    
        # Extract numeric quantity.
        qty_match = re.search(r"\b(\d+)\b", quantity_text)
        quantity = int(qty_match.group(1)) if qty_match else None
    
        # Extract quantity written as a word.
        if quantity is None:
            word_nums = {
                "one": 1,
                "two": 2,
                "three": 3,
                "four": 4,
                "five": 5,
                "six": 6,
                "seven": 7,
                "eight": 8,
                "nine": 9,
                "ten": 10,
            }
    
            for word, number in word_nums.items():
                if re.search(rf"\b{word}\b", quantity_text):
                    quantity = number
                    break
    
        # Extract colour.
        colors = [
            "black", "white", "red", "blue", "green", "yellow",
            "pink", "purple", "orange", "brown", "grey", "gray",
            "beige",
        ]
    
        color = next(
            (
                c for c in colors
                if re.search(rf"\b{c}\b", text_lower)
            ),
            None,
        )
    
        # Extract size, including replies such as "M" or "Size M".
        size_match = re.search(
            r"\b(?:size\s*)?(XXXL|XXL|XL|XS|S|M|L)\b",
            text,
            re.IGNORECASE,
        )
        size = size_match.group(1).upper() if size_match else None
    
        return {
            "quantity": quantity,
            "color": color,
            "size": size,
        }


    
    def process_customer_message(
        self,
        customer_id,
        display_name,
        text,
        telegram_user_id=None,
        telegram_username=None,
        conversation_id=None,
    ):
        """Process a customer message and continue incomplete orders."""
    
        # Find or create the customer.
        customer = self.tools.find_or_create_customer(
            display_name=display_name,
            telegram_user_id=telegram_user_id,
            telegram_username=telegram_username,
        )
    
        # Find or create the customer's open Telegram conversation.
        if not conversation_id:
            conversation_reference = (
                f"claw:sender:telegram:{telegram_user_id}"
            )
    
            conv = (
                self.db.query(Conversation)
                .filter(
                    Conversation.customer_id == customer.id,
                    Conversation.platform == "telegram",
                    Conversation.status == "open",
                    Conversation.conversation_reference
                    == conversation_reference,
                )
                .order_by(Conversation.id.desc())
                .first()
            )
    
            if conv is None:
                conv = Conversation(
                    customer_id=customer.id,
                    platform="telegram",
                    conversation_reference=conversation_reference,
                    status="open",
                )
                self.db.add(conv)
                self.db.commit()
                self.db.refresh(conv)
    
                print(
                    f"[CONVERSATION DEBUG] Created "
                    f"conversation_id={conv.id}"
                )
            else:
                print(
                    f"[CONVERSATION DEBUG] Reused "
                    f"conversation_id={conv.id}"
                )
    
            conversation_id = conv.id
    
        # Read the existing conversation BEFORE saving the new message.
        previous_messages = (
            self.db.query(Message)
            .filter(Message.conversation_id == conversation_id)
            .order_by(Message.id.asc())
            .all()
        )
    
        pending_order = False
        order_text = text
    
        # The last AI message indicates an incomplete order if it asks
        # the customer to supply missing order information.
        if (
            previous_messages
            and previous_messages[-1].sender_type == "ai"
            and "I need the following:"
            in previous_messages[-1].content
        ):
            pending_order = True
            previous_customer_messages = []
    
            # Walk backward through the incomplete-order conversation.
            # Continue across repeated missing-information prompts.
            for previous in reversed(previous_messages[:-1]):
                if previous.sender_type == "customer":
                    previous_customer_messages.append(previous.content)
    
                elif previous.sender_type == "ai":
                    if "I need the following:" in previous.content:
                        continue
    
                    # Stop at the AI response that came before this order.
                    break
    
            previous_customer_messages.reverse()
    
            # Combine all previous order details with the latest reply.
            order_text = " ".join(
                previous_customer_messages + [text]
            )
    
            print(
                "[ORDER DEBUG] Continuing incomplete order. "
                f"Combined text={order_text!r}"
            )
    
        # A reply to an incomplete order must remain a new-order intent,
        # even if the reply only says "M", "Size M", or "2".
        intent = (
            "new_order"
            if pending_order
            else self.classify_intent(text)
        )
    
        # Save the customer's message with its effective intent.
        msg = Message(
            conversation_id=conversation_id,
            sender_type="customer",
            content=text,
            intent=intent,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
    
        # Get the active campaign.
        campaign = (
            self.db.query(Campaign)
            .filter(Campaign.status == "open")
            .first()
        )
    
        if not campaign:
            response = (
                "Sorry, there are no active group buys at the moment."
            )
            self.tools.send_customer_message(
                conversation_id,
                response,
            )
            return {
                "response": response,
                "intent": intent,
                "order_id": None,
                "exception": False,
            }
    
        # Handle the effective intent.
        if intent == "new_order":
            return self._handle_new_order(
                campaign,
                customer,
                conversation_id,
                order_text,
            )
    
        elif intent == "payment_enquiry":
            return self._handle_payment_enquiry(
                campaign, customer, conversation_id, text
            )
    
        elif intent == "order_status":
            return self._handle_order_status(
                campaign, customer, conversation_id, text
            )
    
        elif intent == "cancellation":
            return self._handle_cancellation(
                campaign, customer, conversation_id, text
            )
    
        elif intent == "product_question":
            return self._handle_product_question(
                campaign, customer, conversation_id, text
            )
    
        elif intent == "complaint":
            return self._handle_complaint(
                campaign, customer, conversation_id, text
            )
    
        response = (
            "I understand you have a question. Could you provide more "
            "details? I can help with ordering, checking order status, "
            "payment enquiries, and product information."
        )
    
        self.tools.send_customer_message(
            conversation_id,
            response,
        )
    
        return {
            "response": response,
            "intent": intent,
            "order_id": None,
            "exception": False,
        }

    
    def _handle_new_order(self, campaign, customer, conversation_id, text):
        """Handle a new order or continue an incomplete order."""
    
        info = self.extract_order_info(text)
    
        missing = []
    
        if not info["quantity"]:
            missing.append("quantity")
    
        if not info["color"]:
            missing.append("colour")
    
        if not info["size"]:
            missing.append("size")
    
        if missing:
            missing_str = " and ".join(missing)
    
            response = (
                "I would like to help you order. "
                f"However, I need the following: {missing_str}. "
                "Could you provide the missing information?"
            )
    
            self.tools.send_customer_message(
                conversation_id,
                response,
            )
    
            return {
                "response": response,
                "intent": "new_order",
                "order_id": None,
                "exception": False,
                "missing": missing,
            }
    
        variant = self.find_variant(
            campaign.id,
            info["color"],
            info["size"],
        )
    
        if not variant:
            availability = self.tools.get_product_availability(
                campaign.id
            )
    
            available_str = ", ".join(
                v["attributes"] for v in availability
            )
    
            response = (
                f"I could not find a variant matching "
                f"{info['color']} / {info['size']}. "
                f"Available variants: {available_str}."
            )
    
            self.tools.send_customer_message(
                conversation_id,
                response,
            )
    
            return {
                "response": response,
                "intent": "new_order",
                "order_id": None,
                "exception": False,
            }
    
        result = self.tools.create_pending_order(
            campaign.id,
            customer.id,
            variant["variant_id"],
            info["quantity"],
        )
    
        if result.get("success"):
            response = (
                f"Thank you, {customer.display_name}. "
                f"Order created: {info['quantity']} x "
                f"{variant['attributes']} at "
                f"RM{variant['price']:.2f} each. "
                f"Total: RM{result['total_amount']:.2f}. "
                f"Order ID: {result['order_id']}. "
                "Status: PENDING_PAYMENT. "
                f"Payment instructions: "
                f"{result['payment_instructions']}"
            )
    
            self.tools.send_customer_message(
                conversation_id,
                response,
                result["order_id"],
            )
    
            return {
                "response": response,
                "intent": "new_order",
                "order_id": result["order_id"],
                "exception": False,
            }
    
        if result.get("exception_id"):
            response = result["error"]
    
            self.tools.send_customer_message(
                conversation_id,
                response,
                result.get("order_id"),
            )
    
            return {
                "response": response,
                "intent": "new_order",
                "order_id": result.get("order_id"),
                "exception": True,
            }
    
        response = result["error"]
    
        self.tools.send_customer_message(
            conversation_id,
            response,
        )
    
        return {
            "response": response,
            "intent": "new_order",
            "order_id": None,
            "exception": False,
        }

    def _handle_payment_enquiry(self, campaign, customer, conversation_id, text):
        """Handle payment-related enquiries. Never marks payment as paid without verification."""
        orders = self.db.query(Order).filter(Order.customer_id == customer.id).all()

        if not orders:
            response = "I could not find any orders for your account. If you have placed an order, please provide your order ID."
            self.tools.send_customer_message(conversation_id, response)
            return {"response": response, "intent": "payment_enquiry"}

        # Find the most relevant order
        relevant_order = None
        for o in orders:
            if o.payment_status in ("unpaid", "payment_submitted", "verifying"):
                relevant_order = o
                break
        if not relevant_order:
            relevant_order = orders[-1]

        if relevant_order.payment_status == "paid":
            response = f"Your order #{relevant_order.id} has been PAID. Payment verified. No further action needed."
        elif relevant_order.payment_status == "verifying":
            response = (
                f"Your payment for order #{relevant_order.id} (RM{relevant_order.total_amount:.2f}) is currently being VERIFIED. "
                f"Please note that a transfer screenshot is not proof of successful payment. "
                f"The admin will verify the bank transfer and confirm once done."
            )
        elif relevant_order.payment_status == "payment_submitted":
            response = (
                f"I can see that payment has been submitted for order #{relevant_order.id}. "
                f"It is pending verification. Please wait for the admin to confirm."
            )
        else:
            response = (
                f"Order #{relevant_order.id} (RM{relevant_order.total_amount:.2f}) has not been paid yet. "
                f"Payment instructions: {campaign.payment_instructions}"
            )

        self.tools.send_customer_message(conversation_id, response, relevant_order.id)
        return {"response": response, "intent": "payment_enquiry", "order_id": relevant_order.id}

    def _handle_order_status(self, campaign, customer, conversation_id, text):
        """Handle order status enquiries."""
        orders = self.db.query(Order).filter(Order.customer_id == customer.id).all()
        if not orders:
            response = "I could not find any orders for your account."
            self.tools.send_customer_message(conversation_id, response)
            return {"response": response, "intent": "order_status"}

        latest = orders[-1]
        items_str = ", ".join([f"{oi.quantity} x {oi.variant.attributes}" for oi in latest.items])
        response = (
            f"Your latest order #{latest.id}: {items_str}. "
            f"Order status: {latest.status.upper()}. "
            f"Payment status: {latest.payment_status.upper()}. "
            f"Fulfilment status: {latest.fulfilment_status.upper()}."
        )
        self.tools.send_customer_message(conversation_id, response, latest.id)
        return {"response": response, "intent": "order_status", "order_id": latest.id}

    def _handle_cancellation(self, campaign, customer, conversation_id, text):
        """Handle cancellation requests. Creates a request, does not immediately cancel."""
        orders = self.db.query(Order).filter(
            Order.customer_id == customer.id,
            Order.status.in_(["pending_payment", "confirmed"]),
        ).all()

        if not orders:
            response = "I could not find any active orders to cancel."
            self.tools.send_customer_message(conversation_id, response)
            return {"response": response, "intent": "cancellation"}

        latest = orders[-1]
        result = self.tools.request_cancellation(latest.id, customer.id)

        if result.get("success"):
            response = f"Your order #{latest.id} has been cancelled. If you paid already, a refund will be processed according to the refund policy."
        else:
            response = result["error"]

        self.tools.send_customer_message(conversation_id, response, latest.id)
        return {"response": response, "intent": "cancellation", "order_id": latest.id, "exception": not result.get("success")}

    def _handle_product_question(self, campaign, customer, conversation_id, text):
        """Answer product questions using approved information."""
        answer = self.tools.retrieve_approved_faq(campaign.id, text)
        self.tools.send_customer_message(conversation_id, answer)
        return {"response": answer, "intent": "product_question"}

    def _handle_complaint(self, campaign, customer, conversation_id, text):
        """Escalate complaints to the admin."""
        exc = self.tools.create_exception(
            "complaint",
            None,
            f"Customer complaint: {text}",
            "Review the complaint and respond personally.",
        )
        response = "I am sorry to hear about your issue. I have forwarded your complaint to the admin, who will address it personally. Thank you for your patience."
        self.tools.send_customer_message(conversation_id, response)
        return {"response": response, "intent": "complaint", "exception": True, "exception_id": exc.get("exception_id")}

    def process_admin_query(self, query):
        """Process an admin query through the AI co-admin interface."""
        q_lower = query.lower()

        if "how many" in q_lower and "order" in q_lower:
            metrics = self.tools.get_dashboard_metrics()
            return f"There are {metrics['total_orders']} total orders. {metrics['orders_awaiting_payment']} are awaiting payment."

        if "incomplete" in q_lower or "pending" in q_lower:
            pending = self.db.query(Order).filter(Order.status == "pending_payment").all()
            if not pending:
                return "No incomplete orders."
            lines = [f"Order #{o.id}: {o.customer.display_name}, RM{o.total_amount:.2f}" for o in pending]
            return f"Orders awaiting payment:\n" + "\n".join(lines)

        if "supplier" in q_lower and ("summary" in q_lower or "list" in q_lower or "quantity" in q_lower):
            campaign = self.db.query(Campaign).filter(Campaign.status == "open").first()
            if not campaign:
                return "No active campaign found."
            summary = self.tools.generate_supplier_summary(campaign.id)
            lines = [f"{variant}: {qty}" for variant, qty in summary["variants"].items()]
            status_note = "This is a FINAL summary." if summary["is_final"] else "This is NOT final - the campaign is still open or has unresolved exceptions."
            return f"Supplier Summary for {summary['campaign_name']}:\n" + "\n".join(lines) + f"\nTotal units: {summary['total_units']}\nExcluded (cancelled): {summary['excluded_cancelled']}\nUnresolved exceptions: {summary['unresolved_exceptions']}\n{status_note}"

        if "not completed" in q_lower or "not paid" in q_lower or "haven't paid" in q_lower:
            unpaid = self.db.query(Order).filter(Order.payment_status == "unpaid", Order.status == "pending_payment").all()
            if not unpaid:
                return "All pending orders have payment submitted or verifying."
            lines = [f"#{o.id}: {o.customer.display_name}, RM{o.total_amount:.2f}" for o in unpaid]
            return "Customers who have not completed payment:\n" + "\n".join(lines)

        if "announcement" in q_lower or "close" in q_lower and "tonight" in q_lower:
            campaign = self.db.query(Campaign).filter(Campaign.status == "open").first()
            if not campaign:
                return "No active campaign."
            deadline = campaign.closes_at.strftime("%d %b %Y, %H:%M UTC") if campaign.closes_at else "soon"
            return f"Draft announcement: Ordering for {campaign.name} closes tonight at {deadline}. Please complete your orders and payments before the deadline. Late orders will be forwarded to admin for approval."

        if "escalat" in q_lower or "exception" in q_lower:
            excs = self.db.query(Exception_).filter(Exception_.status == "open").all()
            if not excs:
                return "No open exceptions."
            lines = [f"Exception #{e.id} [{e.type}]: {e.description[:80]}..." for e in excs]
            return "Open exceptions:\n" + "\n".join(lines)

        if "summar" in q_lower and ("studying" in q_lower or "while" in q_lower or "happened" in q_lower):
            metrics = self.tools.get_dashboard_metrics()
            return (
                f"While you were studying: {metrics['automated_actions_completed']} automated actions were completed. "
                f"{metrics['orders_awaiting_payment']} orders are awaiting payment. "
                f"{metrics['open_exceptions']} exceptions need your attention. "
                f"{metrics['unresolved_customer_enquiries']} customer enquiries are unresolved."
            )

        return "I can help with: order counts, incomplete orders, supplier summaries, unpaid customers, announcements, exceptions, and activity summaries. What would you like to know?"
