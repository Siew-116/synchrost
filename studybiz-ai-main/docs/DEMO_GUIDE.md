# Demo Guide

## Demo Scenario: "Exam Tomorrow + 9 Orders to Pack + Shipping Cutoff"

This scenario demonstrates the core value proposition of StudyBiz AI: the agent detects a conflict between an imminent exam and a backlog of orders that need packing, proposes available time slots, and drafts customer messages — all behind approval gates.

---

## Setup

1. Start the application (Docker Compose or local dev):
   ```bash
   # Docker
   docker compose up --build

   # Or local
   # Terminal 1:
   cd backend && source venv/bin/activate && python -m uvicorn app.main:app --reload --port 8000
   # Terminal 2:
   cd frontend && npm run dev
   ```

2. Seed the database (if not already seeded):
   ```bash
   cd backend && python seed_data.py
   ```

3. Open `http://localhost:5173` and log in:
   - Email: `nurul@studybiz.my`
   - Password: `demo123456`

---

## Walkthrough

### Step 1: Dashboard Overview

**Action:** Navigate to `/` (Dashboard).

**What you see:** The dashboard shows:
- **Today's priorities** — academic events scheduled for today, sorted by priority (CRITICAL first)
- **Upcoming exams** — exams within 14 days, with day countdown
- **Due assignments** — assignments due within 7 days
- **Packing queue** — orders in PAID status, waiting to be packed, with estimated packing minutes
- **Shipping deadlines** — packed orders with promised dispatch dates, sorted by urgency
- **Calendar warnings** — overdue assignments or imminent dispatch deadlines
- **Stats** — total orders, pending, paid, packed, open exceptions, today's events

**Key API call:**
```
GET /api/dashboard/
```

This endpoint aggregates data from multiple tables (academic_events, orders, business_exceptions) in a single query, scoped to the current user.

---

### Step 2: Academic Calendar — See the Exam

**Action:** Navigate to `/academic`.

**What you see:** The academic events list. The seed data includes an exam scheduled for tomorrow (e.g., "STIW3024 Software Engineering Final"). The exam is marked as `FIXED` and `CRITICAL` priority.

**Key API call:**
```
GET /api/academic/
```

---

### Step 3: Orders — See the Packing Backlog

**Action:** Navigate to `/orders`. Filter by status "paid" if needed.

**What you see:** 9 orders in `PAID` status, each with an `estimated_packing_minutes` value. The total packing time exceeds what can reasonably be done the night before an exam.

**Key API call:**
```
GET /api/orders/?status_filter=paid
```

The orders router enforces the state machine. Each order's status history is available:
```
GET /api/orders/{id}/history
```

---

### Step 4: AI Assistant — Ask the Agent

**Action:** Navigate to `/assistant` (AI Assistant page).

**Type this message:**
```
I have an exam tomorrow and 9 orders to pack. When can I pack them?
```

**What happens:** The agent runs its 7-phase loop:

1. **OBSERVE** — Gathers:
   - Academic schedule (finds the exam tomorrow)
   - Business tasks (counts 9 paid orders)
   - Packing estimate (sums `estimated_packing_minutes` across paid orders)
   - Available time slots (finds free windows in the user's working hours)

2. **ANALYZE** — Detects intent: `exam_conflict`. Identifies:
   - The exam details (title, time, priority)
   - Packing conflict: `order_count > 0` with an exam within 48h
   - Total packing time in minutes/hours

3. **PRIORITIZE** — Sets priority to `CRITICAL` (exam conflict with packing backlog).

4. **PLAN** — Plans to:
   - Identify exam time and protected periods
   - Calculate packing workload
   - Find available time slots outside exam/revision periods
   - Propose packing schedule
   - Draft customer notifications for affected dispatches

5. **ACT** — Calls tools:
   - `detect_schedule_conflicts()` — Returns the exam-vs-packing conflict
   - `estimate_packing_duration()` — Returns total packing time
   - `find_available_time_slots(60)` — Returns free 60-min slots
   - `generate_schedule_proposal()` — Returns conflicts + recommendations

6. **VERIFY** — Checks each tool result for errors.

7. **LOG** — Writes an `AgentLog` row with the full cycle.

**Expected agent response (formatted):**

```
**Priority: CRITICAL**

Exam: STIW3024 Software Engineering Final
   When: 11/10/2025 09:00
   Priority: critical

You have 9 paid orders to pack
   Total packing time: 1.5 hours (90 minutes)

Available packing slots:
   - 10/10 20:00 - 21:00
   - 10/10 21:00 - 22:00
   - 10/10 14:00 - 15:00

I recommend packing before or after the exam to protect your revision time.

Approval needed: Customer message drafts have been created and need your approval.

---
Mode: Deterministic (rule-based)
Session: a1b2c3d4
```

**Key API call:**
```
POST /api/agent/chat
Body: { "message": "I have an exam tomorrow and 9 orders to pack. When can I pack them?" }
```

---

### Step 5: Agent Logs — Audit Trail

**Action:** Navigate to `/agent-logs`.

**What you see:** A list of agent log entries showing the full cycle: observation data, analysis, plan, tools called, action results, verification status. Each entry has a timestamp and session ID.

**Key API call:**
```
GET /api/agent/logs?limit=50
```

---

### Step 6: Approvals — Review Drafted Messages

**Action:** Navigate to `/approvals`.

**What you see:** If the agent created message drafts (for customers affected by delayed dispatch), they appear here as pending approval requests. Each shows the action type, description, and payload.

**Action:** Click "Approve" or "Reject" on a draft.

**Key API calls:**
```
GET /api/approvals/?status_filter=pending
PUT /api/approvals/{id}/decide
Body: { "approved": true, "note": "Looks good" }
```

---

### Step 7: Messages — Review Drafts

**Action:** Navigate to `/messages`.

**What you see:** Message drafts created by the agent. Each draft has:
- Template type (e.g., "packaging_notice")
- Language (en or ms)
- Subject and body
- Status: DRAFTED -> AWAITING_APPROVAL -> APPROVED -> EXECUTED

**Action:** Review a draft, then approve and mark as sent.

**Key API calls:**
```
GET /api/messages/
PUT /api/messages/{id}/approve
PUT /api/messages/{id}/mark-sent
```

---

### Step 8: Finance — Realised vs Estimated Profit

**Action:** Navigate to `/finance`.

**What you see:** The finance summary showing:
- **Gross sales** — total across all orders
- **Discounts** — total discounts given
- **Refunds** — total refunds issued (from cancelled paid orders)
- **Net sales** — gross - discounts - refunds
- **Product cost (COGS)** — from delivered orders
- **Realised profit** — only from DELIVERED orders
- **Estimated profit** — realised + projected from PAID/PACKED/DISPATCHED orders
- **Outstanding payments** — total balance due from non-cancelled, non-delivered orders

The two profit figures are shown separately and clearly labelled. They are never summed into a single number without explicit labelling.

**Key API call:**
```
GET /api/finance/summary
```

---

### Step 9: Bulk Orders — Cost Allocation

**Action:** Navigate to `/bulk-orders`. Select a bulk order and view its allocations.

**What you see:** The two-phase cost allocation:
- Phase 1: Each participant's item subtotal
- Phase 2: Shared costs (domestic shipping, international shipping, EMS, other) allocated by the chosen method

The last participant absorbs the rounding residual, guaranteeing `Σ(shares) == shared_cost` exactly.

**Key API call:**
```
GET /api/bulk-orders/{id}/allocations
```

---

### Step 10: Automation — Trigger a Job

**Action:** Navigate to `/automation`.

**What you see:** 10 default automation jobs (daily academic briefing, daily business briefing, exam warning, payment review, inventory alert, weekly summary, etc.).

**Action:** Click "Run Now" on "Daily Business Briefing".

**What happens:** The job executes, generates an in-app notification with the current business status, and updates the job's last-run timestamp.

**Key API calls:**
```
GET /api/automation/                           # List jobs
POST /api/automation/{id}/run-now              # Manual trigger
GET /api/automation/{id}/runs                   # Run history
```

---

## Summary of Key API Calls

| Step | Method | Endpoint | Purpose |
|---|---|---|---|
| 1 | GET | `/api/dashboard/` | Aggregated dashboard data |
| 2 | GET | `/api/academic/` | Academic events list |
| 3 | GET | `/api/orders/?status_filter=paid` | Orders in PAID status |
| 3 | GET | `/api/orders/{id}/history` | Order status transition history |
| 4 | POST | `/api/agent/chat` | Send message to AI agent |
| 5 | GET | `/api/agent/logs` | Agent audit trail |
| 6 | GET | `/api/approvals/` | Pending approval requests |
| 6 | PUT | `/api/approvals/{id}/decide` | Approve/reject a request |
| 7 | GET | `/api/messages/` | Message draft queue |
| 7 | PUT | `/api/messages/{id}/approve` | Approve a draft |
| 8 | GET | `/api/finance/summary` | Realised vs estimated profit |
| 9 | GET | `/api/bulk-orders/{id}/allocations` | Two-phase cost allocation |
| 10 | GET | `/api/automation/` | List automation jobs |
| 10 | POST | `/api/automation/{id}/run-now` | Manually trigger a job |

---

## Additional Demos

### Order State Machine Demo

1. Create an order at `POST /api/orders/` with status `PENDING`
2. Transition to `CONFIRMED` at `PUT /api/orders/{id}` with `{ "status": "confirmed" }`
3. Transition to `PAID` — the system records a finance transaction automatically
4. Try to transition to `PACKED` without full payment -> **400 error** (payment gate)
5. Set `amount_paid` to full total, then transition to `PACKED`
6. Try to transition to `DISPATCHED` without `tracking_number` -> **400 error** (tracking gate)
7. Set `tracking_number`, then transition to `DISPATCHED` -> `DELIVERED`

### Exception Handling Demo

1. Create a blackout exception: `POST /api/exceptions/` with type `BLACKOUT`
2. The dashboard shows open exceptions in the stats
3. Orders affected by the blackout can be transitioned to `EXCEPTION`

### Inventory Demo

1. Navigate to `/products` to see stock levels
2. Low-stock products trigger alerts when `available_stock <= low_stock_threshold`
3. Stock movements are logged in an append-only table
