# Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                        Browser (React SPA)                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │Dashboard │ │AI Assist │ │ Orders   │ │ Academic │  ...   │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘       │
│       │             │            │             │              │
│  ┌────┴─────────────┴────────────┴─────────────┴──────┐    │
│  │              Axios API Service Layer                 │    │
│  │         (api.ts — 15 API modules)                   │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                           │ JWT Bearer Token                  │
└───────────────────────────┼─────────────────────────────────┘
                            │ HTTP /api/*
┌───────────────────────────┼─────────────────────────────────┐
│                      FastAPI Backend                          │
│  ┌─────────────────────────┼─────────────────────────────┐  │
│  │              CORS Middleware + Routers                  │  │
│  │  auth | academic | customers | products | orders |     │  │
│  │  bulk_orders | suppliers | exceptions | finance |      │  │
│  │  dashboard | agent | automation | messages |           │  │
│  │  approvals | notifications | export                   │  │
│  └─────────────────────────┬─────────────────────────────┘  │
│                            │                                  │
│  ┌──────────┐  ┌──────────┴──────────┐  ┌───────────────┐  │
│  │  Utils    │  │    Agent Engine     │  │   Pydantic    │  │
│  │  (auth)   │  │  OBSERVE→ANALYZE→  │  │   Schemas     │  │
│  │  JWT+bcrypt│  │  PRIORITIZE→PLAN→  │  │  (validation)  │  │
│  └──────────┘  │  ACT→VERIFY→LOG     │  └───────────────┘  │
│                │  + 14 Tools         │                      │
│                │  + Model Adapter    │                      │
│                └──────────┬──────────┘                      │
│  ┌───────────────────────┼──────────────────────────────┐  │
│  │              SQLAlchemy ORM (14 models)                │  │
│  └───────────────────────┼──────────────────────────────┘  │
│                           │                                  │
│              ┌────────────┴────────────┐                    │
│              │  SQLite (dev) / PG (prod)│                    │
│              └─────────────────────────┘                    │
└──────────────────────────────────────────────────────────────┘
```

---

## Backend Layers

### 1. Models (`app/models/__init__.py`)

14 SQLAlchemy ORM models covering all domain entities:

| Model | Table | Purpose |
|---|---|---|
| `User` | `users` | User profile, business info, preferences |
| `AcademicEvent` | `academic_events` | Classes, exams, assignments, study sessions, personal events |
| `Customer` | `customers` | Customer contacts (WhatsApp, IG, email) |
| `Product` | `products` | Products with pricing (MYR), stock buckets |
| `Order` | `orders` | Orders with 8-state lifecycle, pricing, fulfillment |
| `OrderItem` | `order_items` | Line items per order |
| `OrderStatusHistory` | `order_status_history` | Append-only state transition log |
| `BulkOrder` | `bulk_orders` | Group orders with shared costs |
| `StockMovement` | `stock_movements` | Append-only inventory movement log |
| `Supplier` | `suppliers` | Supplier records |
| `PurchaseOrder` | `purchase_orders` | POs placed with suppliers |
| `PackagingBatch` | `packaging_batches` | Packing session batches |
| `ShippingBatch` | `shipping_batches` | Dispatch batches |
| `BusinessException` | `business_exceptions` | Exception cases (8 types) |
| `FinanceTransaction` | `finance_transactions` | Financial ledger entries |
| `AgentLog` | `agent_logs` | Full agent cycle audit trail |
| `AutomationJob` | `automation_jobs` | Cron-based scheduled jobs |
| `AutomationRun` | `automation_runs` | Execution history per job |
| `MessageDraft` | `message_drafts` | Customer message drafts (5 states) |
| `ApprovalRequest` | `approval_requests` | Approval queue for gated actions |
| `Notification` | `notifications` | In-app notifications |

All monetary fields use `Numeric(12, 2)` — never floating point. All timestamps default to `datetime.utcnow`.

### 2. Schemas (`app/schemas/__init__.py`)

Pydantic v2 models for request validation and response serialization. Each model has a corresponding `Create`, `Update`, and `Response` schema. Key schemas include `AgentChatRequest`/`AgentChatResponse`, `FinanceSummary`, `DashboardData`, `ApprovalDecision`.

### 3. Routers (`app/routers/`)

16 API routers, each prefixed under `/api`. All routes require JWT authentication via `get_current_user` dependency. Every query is scoped by `user_id` for data isolation.

### 4. Agent (`app/agent/`)

The agent subsystem has two files:
- `engine.py` — The 7-phase loop and intent detection
- `tools.py` — 14 structured tools and the `TOOL_REGISTRY`

See [Agent Loop](#ai-agent-loop) below.

### 5. Utils (`app/utils/auth.py`)

JWT token creation/verification and bcrypt password hashing. The `get_current_user` dependency extracts the user from the JWT `sub` claim.

### 6. Config (`app/config.py`)

Pydantic Settings reads from environment variables and `.env` file. Key settings: `DATABASE_URL`, `SECRET_KEY`, `AI_MODEL_API_BASE`, `AI_MODEL_API_KEY`, `CORS_ORIGINS`, `TIMEZONE`.

---

## Frontend Layers

### 1. Pages (`src/pages/`)

17 page components mapped to routes in `App.tsx`:

| Page | Route | Purpose |
|---|---|---|
| Login | `/login` | Email + password login |
| Dashboard | `/` | Today's priorities, upcoming exams, packing queue |
| AIAssistant | `/assistant` | Chat with the agent |
| Orders | `/orders` | Order list with status filter |
| Calendar | `/calendar` | Calendar view of academic + business events |
| Academic | `/academic` | Academic event CRUD |
| Products | `/products` | Product + inventory management |
| Customers | `/customers` | Customer CRUD |
| Finance | `/finance` | Realised vs estimated profit, transactions |
| BulkOrders | `/bulk-orders` | Group orders + cost allocation |
| Exceptions | `/exceptions` | Business exception tracking |
| Messages | `/messages` | Message draft queue (DRAFT -> APPROVED -> SENT) |
| Automation | `/automation` | Automation jobs + manual trigger |
| Approvals | `/approvals` | Approval queue for gated actions |
| AgentLogs | `/agent-logs` | Agent audit trail |
| Settings | `/settings` | User profile + preferences |
| Suppliers | `/suppliers` | Supplier CRUD |

### 2. Components (`src/components/`)

`Layout.tsx` — The shared layout with sidebar navigation and header. All protected routes render inside `<Layout>`.

### 3. Services (`src/services/api.ts`)

Centralized Axios instance with:
- Request interceptor: attaches JWT Bearer token from `localStorage`
- Response interceptor: redirects to `/login` on 401
- 15 API module objects (`authAPI`, `academicAPI`, `orderAPI`, `agentAPI`, etc.)

### 4. Contexts (`src/contexts/AuthContext.tsx`)

`AuthProvider` manages auth state:
- On mount: checks `localStorage` for token, validates via `GET /auth/me`
- `login()`: calls login API, stores token + user
- `register()`: calls register API, stores token + user
- `logout()`: clears localStorage, sets user to null
- `useAuth()` hook: access user, loading, login, register, logout

---

## AI Agent Loop

The agent engine (`app/agent/engine.py`) processes natural language commands through a 7-phase loop:

```
User Message
     │
     ▼
┌─────────────┐
│  1. OBSERVE  │  Gather state: academic schedule, business tasks,
│              │  payment summary, inventory. Context-specific data
│              │  based on keywords (exam, pack, payment, schedule...).
└──────┬───────┘
       │
       ▼
┌─────────────┐
│  2. ANALYZE  │  Intent detection: exam_conflict, packing_management,
│              │  payment_review, schedule_planning, message_generation,
│              │  bulk_order_management, inventory_check, finance_summary.
└──────┬───────┘
       │
       ▼
┌──────────────┐
│ 3. PRIORITIZE │  critical | high | medium
│               │  Based on intent + detected conflicts.
└───────┬───────┘
        │
        ▼
┌──────────┐
│ 4. PLAN   │  Build step list + tool call sequence.
│           │  Each intent has a predefined plan template.
└────┬──────┘
     │
     ▼
┌──────────┐    ┌──────────────────────────────────┐
│ 5. ACT    │───▶│  Tool Registry (14 tools)          │
│           │    │  Observation: get_academic_schedule,│
│           │    │    get_business_tasks, get_pending_ │
│           │    │    orders, get_inventory_status,    │
│           │    │    get_payment_summary             │
│           │    │  Analysis: detect_schedule_conflicts│
│           │    │    estimate_packing_duration,      │
│           │    │    find_available_time_slots,       │
│           │    │    generate_schedule_proposal       │
│           │    │  Action: create_internal_task,      │
│           │    │    update_flexible_task,            │
│           │    │    create_message_draft*,           │
│           │    │    create_business_alert            │
│           │    │  Verification: verify_agent_action,│
│           │    │    get_action_history               │
│           │    │  (* requires approval)              │
└────┬──────┘    └──────────────────────────────────┘
     │
     ▼
┌─────────────┐
│  6. VERIFY   │  Check each tool result for errors.
│              │  Set verified=true/false. Log failures.
└──────┬───────┘
       │
       ▼
┌──────────┐
│ 7. LOG    │  Write AgentLog row: observation, analysis, plan,
│           │  action_taken, action_result, verified, tool_called,
│           │  tool_input, tool_output, success, error_message.
└──────────┘
     │
     ▼
  Response (formatted text + actions_taken + approval_requests + session_id + mode)
```

### Agent Modes

1. **Deterministic (default)** — Rule-based intent detection and tool dispatch. No external API required. Used when `AI_MODEL_API_BASE` and `AI_MODEL_API_KEY` are not set.
2. **Model API (optional)** — When an OpenAI-compatible API base URL and key are configured, the agent can call the model for enhanced natural language understanding. The deterministic path serves as fallback.

### Approval Gate

Tools marked `requires_approval: true` in the `TOOL_REGISTRY` (currently `create_message_draft`) do not execute directly. Instead, the agent:
1. Calls the tool to create a draft
2. Adds an entry to `approval_requests` 
3. The user must approve via the Approvals page before the action is executed

This implements the business rule: *"Automation drafts and alerts; the operator decides and confirms every outward action."*

---

## Order State Machine

8 states with guarded transitions. The state machine is enforced in `app/routers/orders.py` via the `VALID_TRANSITIONS` dict.

```
                        ┌─────────────┐
                        │   PENDING   │
                        └──────┬──────┘
                   T1          │          T2
             ┌─────────────────┘└─────────────────┐
             ▼                                    ▼
     ┌───────────────┐                   ┌───────────────┐
     │   CONFIRMED   │───T3──────────────▶│   CANCELLED   │
     └───────┬───────┘                   └───────┬───────┘
        T4    │    T5/T6                           │ T18 (reopen)
   ┌─────────┘└────────────────┐                  │
   ▼                             ▼                 ▼
┌──────────┐  T8        ┌──────────────┐
│   PAID   │───────────▶│  EXCEPTION   │
└────┬─────┘             └──────┬───────┘
  T7 │                          │ T14/T15/T16/T17
     ▼                          │ (resolve to PAID/PACKED/CANCELLED/DISPATCHED)
┌──────────┐
│  PACKED  │──T11───▶ EXCEPTION
└────┬─────┘
  T10│ (requires tracking_number)
     ▼
┌───────────────┐
│  DISPATCHED   │──T13───▶ EXCEPTION
└───────┬───────┘
  T12  │
       ▼
┌───────────────┐
│   DELIVERED   │  (terminal)
└───────────────┘
```

### Transition Rules

| ID | From | To | Gate / Condition |
|---|---|---|---|
| T1 | PENDING | CONFIRMED | Manual action |
| T2 | PENDING | CANCELLED | Before payment |
| T3 | CONFIRMED | PAID | Payment must equal total (RM 0.01 tolerance) |
| T4 | CONFIRMED | CANCELLED | Refund plan required if paid |
| T5 | CONFIRMED | EXCEPTION | Issue detected |
| T6 | PAID | PACKED | **Payment gate**: amount_paid >= total |
| T7 | PAID | EXCEPTION | Post-payment issue |
| T8 | PAID | CANCELLED | **Refund gate**: requires refund authorization |
| T9 | PACKED | DISPATCHED | **Tracking gate**: tracking_number required |
| T10 | PACKED | EXCEPTION | Post-packing issue |
| T11 | DISPATCHED | DELIVERED | Tracking shows delivered or customer ack |
| T12 | DISPATCHED | EXCEPTION | Shipping problem |
| T13-T16 | EXCEPTION | various | Resolve to PAID/PACKED/CANCELLED/DISPATCHED |
| T17 | DELIVERED | EXCEPTION | Post-delivery dispute |

**Terminal states:** `DELIVERED` (success), `CANCELLED` (terminated). `EXCEPTION` is non-terminal — always resolves to another state.

### Key Gates

1. **Payment gate** — `PAID -> PACKED` blocked if `amount_paid < total`
2. **Tracking gate** — `PACKED -> DISPATCHED` blocked if `tracking_number` is empty
3. **Refund gate** — Transition to `CANCELLED` from a paid state requires a refund record
4. **Idempotent transitions** — Re-applying the same trigger does not duplicate state transitions

---

## Two-Phase Bulk Order Cost Allocation

Implemented in `app/routers/bulk_orders.py`. The allocation runs in two independent phases:

### Phase 1: Item Subtotals (method-independent)

```python
for order in participant_orders:
    subtotal = sum(item.total_price for item in order.order_items)
    subtotals[order.customer_id] += quantize(subtotal)
```

Each participant's item subtotal is the sum of their line item totals. This is method-independent — the same subtotals feed all allocation methods.

### Phase 2: Shared Cost Allocation (method-specific)

Shared costs (domestic shipping, international shipping, EMS fee, other) are allocated to participants based on the chosen method:

| Method | Formula | Use Case |
|---|---|---|
| A (equal) | `shared_cost / N` | Flat split, simplest |
| B (by_value) | `(participant_subtotal / grand_subtotal) * shared_cost` | Proportional to item value |
| C (by_weight) | `(participant_qty / total_qty) * shared_cost` | Proportional to quantity |
| D (manual) | Operator enters each share explicitly | Fine-grained control |

### Rounding Residual Rule

Because division may not produce even sen values, the **last participant** in the list absorbs the rounding residual:

```python
for i, pid in enumerate(participants):
    if i == n - 1:  # last participant
        share = quantize(cost_amount - allocated_so_far)
    else:
        share = quantize(cost_amount * ratio)
        allocated_so_far += share
```

This guarantees `Σ(shares) == shared_cost` exactly, preventing 1-sen accumulated discrepancies.

### Reconciliation Invariant

After allocation, the system asserts:

```python
assert quantize(allocated_total) == total_shared
```

---

## Finance Profit Boundary

Implemented in `app/routers/finance.py`. The system strictly separates realised profit from estimated profit, per business rules section 7.3.

### State Classification

```python
REALISED_STATES = {OrderStatus.DELIVERED}           # only delivered orders
ESTIMATED_STATES = {OrderStatus.PAID, OrderStatus.PACKED, OrderStatus.DISPATCHED}  # in-progress
OUTSTANDING_STATES = {PENDING, CONFIRMED, PAID, PACKED, DISPATCHED, EXCEPTION}    # receivables
```

### Profit Calculation

| Metric | Formula |
|---|---|
| **Realised profit** | `(r_gross - r_discounts - refunds) + r_shipping_charged - r_product_cost - r_shipping_expenses` |
| **Estimated profit** | `realised_profit + (e_gross - e_discounts) + e_shipping_charged - e_product_cost - e_shipping_expenses` |

Where `r_*` = realised (DELIVERED orders only), `e_*` = estimated (PAID/PACKED/DISPATCHED orders).

**Critical rule:** Realised and estimated profit are never summed into a single "profit" figure without explicit labelling. The API returns both values separately in the `FinanceSummary` schema.

### Outstanding Payments

`balance_due = total - amount_paid` for all orders in `OUTSTANDING_STATES` with `balance_due > 0`. Excludes `CANCELLED` and `DELIVERED` orders.

---

## Conflict Detection Families

The agent's `detect_schedule_conflicts` tool (in `tools.py`) implements detection across the five conflict families defined in the academic rules spec:

### Family A — OVERLAP (Temporal Overlap)

Two events whose `[start, end)` intervals intersect:

```
A.start < B.end  AND  B.start < A.end
```

- FIXED vs FIXED overlap -> severity BLOCKER (cannot auto-resolve)
- FIXED vs FLEXIBLE overlap -> severity MAJOR (flexible item reschedules)
- FLEXIBLE vs FLEXIBLE overlap -> severity MINOR (lower-priority moves)
- EXAM vs anything -> always BLOCKER

### Family B — PREP_INSUFFICIENT (Insufficient Preparation Time)

An EXAM exists but cumulative scheduled STUDY_SESSION time is less than required:

```
requiredStudyMin(exam) - scheduledStudyMin(exam) > tolerance(10%)
AND exam.start - now < leadTimeWindow
```

Severity escalates as exam approaches: INFO (>14d) -> MINOR (7-14d) -> MAJOR (3-7d) -> BLOCKER (<=72h).

### Family C — OVERLOAD (Workload Overload)

Too many commitment-minutes in a sliding window:

```
sum(fixedEventMinutes + scheduledFlexibleMinutes) > capacityLimit(window)
```

| Window | Max committed hours |
|---|---|
| Single day | 14 h |
| 2 consecutive days | 26 h |
| 7-day rolling | 70 h |
| Exam-eve (day before) | 6 h study max |

Hard rule: No two consecutive days may each exceed 12 committed hours.

### Family D — DEADLINE_AT_RISK

Remaining effort cannot fit in available flexible slots before deadline:

```
effortRemainingMin > availableFlexibleMinutes(now, dueDate) * 0.8
```

Safety factor 0.8 reserves 20% buffer for fatigue/interruptions.

### Family E — CROSS_MODULE (Academic vs Business)

Detected when an academic event overlaps a business event (packing session, shipping cutoff, supplier run). Tagged with `crossModule: true` and a `resolutionLayer`:

| Scenario | resolutionLayer |
|---|---|
| EXAM overlaps SHIPPING_CUTOFF | `EXAM_WINDOW_OVERRIDE` (academic wins absolutely) |
| CLASS overlaps PACKING_SESSION | `ACADEMIC_PRECEDENCE` (packing moves) |
| STUDY_SESSION (>7d from exam) overlaps PACKING_SESSION | `BUSINESS_PRECEDENCE` or tie by deadline |
| Business event in exam-eve window (no overlap) | family=`CROSS_MODULE`, `ACADEMIC_PRECEDENCE` |

**Non-redundancy:** `crossModule=true` is the general flag for any conflict spanning both modules. `family=CROSS_MODULE` is reserved for the narrow case of a precedence-only conflict with no underlying overlap/overload/deadline primitive.

### Precedence Table (Academic vs Business)

| # | Condition | Winner |
|---|---|---|
| 1 | EXAM vs any business event | Academic |
| 2 | CLASS vs flexible business task | Academic |
| 3 | SHIPPING_CUTOFF vs flexible STUDY_SESSION (>7d from exam) | Business |
| 4 | STUDY_SESSION (<7d from exam) vs flexible business | Academic |
| 5 | STUDY_SESSION (>7d from exam) vs PACKING_SESSION | Tie (deadline proximity) |
| 6 | PERSONAL (medical) vs any business | Academic |
| 7 | PERSONAL (social) vs any business | Business |
