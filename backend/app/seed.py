"""Seed demo data for StudyBiz AI.

Creates a realistic campus hoodie group buy with interconnected data:
- 1 campaign with 1 product and 4 variants
- 8 customers
- 10 orders in various states
- Payment records in different statuses
- Customer conversations with messages
- Exceptions requiring admin attention
- Automation rules with safe defaults
"""
from datetime import datetime, timezone, timedelta
from app.database import SessionLocal, init_db, Campaign, Product, ProductVariant, Customer, Order, OrderItem, Payment, Conversation, Message, Exception_, AutomationRule, ActionLog


def seed():
    init_db()
    db = SessionLocal()

    # Check if already seeded
    if db.query(Campaign).count() > 0:
        print("Database already seeded. Skipping.")
        db.close()
        return

    now = datetime.now(timezone.utc)

    # -- Campaign --
    campaign = Campaign(
        name="Campus Hoodie Group Buy",
        description="Official university hoodie group buy. Premium cotton, embroidered logo. Available in Black and White, sizes M and L.",
        status="open",
        opens_at=now - timedelta(days=5),
        closes_at=now + timedelta(days=3),
        payment_instructions="Bank transfer to Maybank 1234567890123 (Student Enterprise). Include your order ID as reference.",
        late_order_policy="allow_with_approval",
        cancellation_policy="before_payment",
        supplier_lead_time_days=14,
    )
    db.add(campaign)
    db.flush()

    # -- Product and Variants --
    product = Product(
        campaign_id=campaign.id,
        name="Campus Hoodie",
        description="Premium cotton hoodie with embroidered university logo. Unisex fit.",
        price=45.00,
        stock_limit=100,
    )
    db.add(product)
    db.flush()

    variants = []
    for attrs in ["Black / M", "Black / L", "White / M", "White / L"]:
        v = ProductVariant(
            product_id=product.id,
            attributes=attrs,
            available_quantity=30,
        )
        db.add(v)
        variants.append(v)
    db.flush()

    # -- Customers --
    customers_data = [
        ("Aisyah Rahman", "1329964256", "aisyah_r"),
        ("Tan Wei Ming", "118877665", "tanwm88"),
        ("Lim Chee Keong", "132998877", "limck_sg"),
        ("Nurul Aina", "144556677", "nurulaina"),
        ("Daniel Tan", "155667788", "danielt"),
        ("Sarah Lim", "166778899", "slim99"),
        ("Mohd Faiz", "177889900", "faiz_m"),
        ("Wong Pei San", "188990011", "wps_san"),
    ]
    customers = []
    for name, tg_id, username in customers_data:
        c = Customer(display_name=name, telegram_user_id=tg_id, telegram_username=username)
        db.add(c)
        customers.append(c)
    db.flush()

    # -- Orders --
    orders_data = [
        # (customer_idx, variant_idx, qty, order_status, payment_status, fulfilment_status)
        (0, 0, 2, "pending_payment", "unpaid", "not_ready"),       # Aisyah - Black/M x2
        (1, 1, 1, "confirmed", "paid", "preparing"),                # Wei Ming - Black/L x1, paid
        (2, 2, 3, "pending_payment", "payment_submitted", "not_ready"),  # Chee Keong - White/M x3, payment submitted
        (3, 3, 1, "confirmed", "paid", "ready"),                     # Nurul - White/L x1, paid, ready
        (4, 0, 2, "pending_payment", "unpaid", "not_ready"),        # Daniel - Black/M x2
        (5, 1, 1, "cancelled", "rejected", "not_ready"),            # Sarah - Black/L x1, cancelled
        (6, 2, 4, "pending_payment", "verifying", "not_ready"),    # Faiz - White/M x4, verifying
        (7, 3, 1, "confirmed", "paid", "dispatched"),              # Pei San - White/L x1, dispatched
        (0, 1, 1, "draft", "unpaid", "not_ready"),                  # Aisyah - Black/L x1, draft
        (3, 0, 2, "completed", "paid", "collected"),               # Nurul - Black/M x2, completed
    ]

    orders = []
    for c_idx, v_idx, qty, o_status, p_status, f_status in orders_data:
        variant = variants[v_idx]
        total = variant.product.price * qty
        o = Order(
            campaign_id=campaign.id,
            customer_id=customers[c_idx].id,
            status=o_status,
            payment_status=p_status,
            fulfilment_status=f_status,
            total_amount=total,
        )
        db.add(o)
        db.flush()

        item = OrderItem(
            order_id=o.id,
            product_variant_id=variant.id,
            quantity=qty,
            unit_price=variant.product.price,
        )
        db.add(item)

        if p_status in ("paid", "payment_submitted", "verifying", "rejected"):
            pay = Payment(
                order_id=o.id,
                amount=total,
                status="paid" if p_status == "paid" else ("submitted" if p_status == "payment_submitted" else ("verifying" if p_status == "verifying" else "rejected")),
                submitted_at=now - timedelta(hours=2),
                verified_at=now - timedelta(hours=1) if p_status == "paid" else None,
                verification_method="manual",
            )
            db.add(pay)
        orders.append(o)
    db.flush()

    # -- Conversations and Messages --
    conv1 = Conversation(
        customer_id=customers[0].id,
        platform="telegram",
        conversation_reference="claw:sender:telegram:1329964256",
        status="open",
    )
    db.add(conv1)
    db.flush()

    msgs_data = [
        ("customer", "Hi admin, can I order two black hoodies in size M? I'll transfer the payment later.", "new_order", orders[0].id),
        ("ai", "Thank you, Aisyah. I found the Campus Hoodie group buy. Two Black/M hoodies at RM45 each, total RM90. Your order has been created with status PENDING_PAYMENT. Please transfer to Maybank 1234567890123 with your order ID as reference. You can pay anytime before the deadline.", "new_order", orders[0].id),
        ("customer", "I also want one Black/L, can add?", "order_change", orders[8].id),
        ("ai", "I have created a draft order for one Black/L hoodie (RM45). Would you like me to merge it with your existing order or keep it separate?", "order_change", orders[8].id),
    ]
    for sender, content, intent, order_id in msgs_data:
        m = Message(
            conversation_id=conv1.id,
            order_id=order_id,
            sender_type=sender,
            content=content,
            intent=intent,
        )
        db.add(m)

    conv2 = Conversation(
        customer_id=customers[6].id,
        platform="telegram",
        conversation_reference="claw:sender:telegram:177889900",
        status="open",
    )
    db.add(conv2)
    db.flush()

    for sender, content, intent, order_id in [
        ("customer", "Admin, I already transferred money for 4 white hoodies size M. Please check.", "payment_enquiry", orders[6].id),
        ("ai", "Thank you, Faiz. I can see your payment of RM180 for 4 x White/M hoodies. Your payment is currently being verified. I will notify you once it is confirmed. Please do not send multiple transfers for the same order.", "payment_enquiry", orders[6].id),
    ]:
        m = Message(
            conversation_id=conv2.id,
            order_id=order_id,
            sender_type=sender,
            content=content,
            intent=intent,
        )
        db.add(m)

    conv3 = Conversation(
        customer_id=customers[4].id,
        platform="telegram",
        conversation_reference="claw:sender:telegram:155667788",
        status="open",
    )
    db.add(conv3)
    db.flush()

    for sender, content, intent, order_id in [
        ("customer", "Is the hoodie group buy still open? Can I still order?", "product_question", None),
        ("ai", "Yes, Daniel. The Campus Hoodie group buy is open until " + (campaign.closes_at.strftime("%d %b %Y, %H:%M UTC") if campaign.closes_at else "further notice") + ". Available variants: Black/M, Black/L, White/M, White/L at RM45 each. What would you like to order?", "product_question", None),
        ("customer", "Two black hoodies size M please", "new_order", orders[4].id),
        ("ai", "Thank you, Daniel. Two Black/M hoodies at RM45 each, total RM90. Order created with status PENDING_PAYMENT. Please transfer to Maybank 1234567890123 with your order ID as reference.", "new_order", orders[4].id),
    ]:
        m = Message(
            conversation_id=conv3.id,
            order_id=order_id,
            sender_type=sender,
            content=content,
            intent=intent,
        )
        db.add(m)

    # -- Exceptions --
    exceptions_data = [
        ("late_order", None, "Customer requested to order after potential deadline closure. Late order policy is set to allow_with_approval. Admin needs to decide whether to accept the late order.", "Review the request. If acceptable, approve and create the order manually."),
        ("unverified_payment", orders[6].id, "Customer Faiz claims payment for 4 x White/M (RM180). Payment status is VERIFYING. Screenshot does not constitute proof of successful payment. Manual verification required.", "Verify the bank transfer in the Maybank account. If confirmed, mark payment as PAID. If not found, notify the customer."),
        ("cancellation_request", orders[0].id, "Customer Aisyah may want to change her order (added a draft for Black/L). This could be a cancellation or modification request. Current order is PENDING_PAYMENT.", "Clarify with the customer whether they want to modify or cancel the existing order."),
    ]
    for etype, order_id, desc, rec in exceptions_data:
        e = Exception_(
            type=etype,
            order_id=order_id,
            description=desc,
            recommended_action=rec,
            status="open",
        )
        db.add(e)

    # -- Automation Rules --
    rules_data = [
        ("business_hours", '{"open": "08:00", "close": "22:00", "timezone": "Asia/Kuala_Lumpur"}', True),
        ("late_order_handling", '{"policy": "allow_with_approval", "message": "Your order request is after the deadline. I have forwarded it to the admin for approval."}', True),
        ("payment_verification", '{"require_screenshot": true, "auto_verify": false, "message": "Please send your payment screenshot. I will forward it to the admin for verification."}', True),
        ("cancellation_rules", '{"allowed_before": "payment", "message": "Cancellations are allowed before payment is confirmed. Please confirm if you want to cancel."}', True),
        ("auto_reply_eligible", '{"intents": ["product_question", "order_status"], "exclude": ["complaint", "cancellation"]}', True),
        ("exam_mode", '{"enabled": false, "quiet_hours": "08:00-17:00", "urgent_categories": ["unverified_payment", "stock_mismatch"], "batch_notifications": true}', False),
        ("escalation_conditions", '{"late_order": true, "refund_request": true, "payment_dispute": true, "duplicate_submission": true}', True),
    ]
    for name, config, enabled in rules_data:
        r = AutomationRule(name=name, configuration=config, enabled=enabled)
        db.add(r)

    # -- Action Logs --
    logs_data = [
        ("ai", "create_pending_order", "order", orders[0].id, "Customer requested 2 x Black/M hoodies", "Order created with status pending_payment"),
        ("ai", "send_customer_message", "message", None, "Order confirmation and payment instructions", "Message sent successfully"),
        ("ai", "create_pending_order", "order", orders[4].id, "Customer requested 2 x Black/M hoodies", "Order created with status pending_payment"),
        ("ai", "send_customer_message", "message", None, "Order confirmation and payment instructions", "Message sent successfully"),
        ("ai", "create_exception", "exception", None, "Payment submitted but requires verification", "Exception created for unverified payment"),
        ("ai", "retrieve_approved_faq", "faq", None, "Customer asked about group buy availability", "FAQ response sent"),
        ("admin", "resolve_exception", "exception", None, "Reviewed late order request", "Exception approved, order created"),
    ]
    for actor, action, etype, eid, inp, result in logs_data:
        log = ActionLog(
            actor_type=actor,
            action_type=action,
            entity_type=etype,
            entity_id=eid,
            input_summary=inp,
            result=result,
        )
        db.add(log)

    db.commit()
    db.close()
    print("Seed data inserted successfully.")
