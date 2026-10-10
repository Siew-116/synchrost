# StudyBiz AI — Progress Tracker

**Last updated:** October 10, 2026

---

## Milestone Status

| Milestone | Description | Status | Completion |
|-----------|-------------|--------|------------|
| M1 | Application Foundation | Complete | 100% |
| M2 | Business Operations | Complete | 100% |
| M3 | Intelligent AI Agent | Complete | 100% |
| M4 | Automation & Communication | Complete | 100% |
| M5 | Deployment & Demo | Complete | 100% |

---

## Milestone 1: Application Foundation

### Completed
- [x] JWT authentication (register, login, token validation) with bcrypt
- [x] Academic events CRUD (exams, assignments, classes, study sessions)
- [x] Business basics: products, customers, orders
- [x] Order 8-state machine (PENDING->CONFIRMED->PAID->PACKED->DISPATCHED->DELIVERED + CANCELLED, EXCEPTION)
- [x] Calendar view (academic + business events)
- [x] Dashboard (stats, priorities, packing queue, exam warnings, calendar alerts)
- [x] Sidebar navigation (16 items)
- [x] Mobile-responsive layout with Tailwind CSS

### Frontend Pages Built
- [x] Login.tsx
- [x] Dashboard.tsx
- [x] Orders.tsx
- [x] Calendar.tsx
- [x] Academic.tsx
- [x] Products.tsx
- [x] Customers.tsx

---

## Milestone 2: Business Operations

### Completed
- [x] Order state machine with validated transitions (`VALID_TRANSITIONS` dict in `orders.py`)
- [x] PACKED gate (requires `amount_paid >= total`), DISPATCHED gate (requires `tracking_number`)
- [x] Stock reservation on order creation, stock release on cancellation
- [x] `OrderStatusHistory` append-only audit trail
- [x] Automatic `FinanceTransaction` recording on PAID transition
- [x] Bulk orders with two-phase cost allocation
  - [x] Phase 1: `compute_item_subtotals()` (method-independent)
  - [x] Phase 2: `allocate_shared_costs()` with methods A (equal), B (by_value), D (manual)
  - [x] Banker's rounding (`ROUND_HALF_EVEN`)
  - [x] Last-participant rounding residual
  - [x] Reconciliation invariant assertion (`Σ(shares) == shared_cost`)
- [x] Inventory management with stock movements (append-only `StockMovement` table)
- [x] Low-stock alerts (`available_stock <= low_stock_threshold`)
- [x] Suppliers and purchase orders
- [x] Business exceptions (8 types: blackout, cancellation, supplier_delay, missing_item, defective_item, refund, replacement, dispute)
- [x] Finance summary with realised vs estimated profit boundary (per business rules section 7.3)
- [x] Excel masterlist export (openpyxl)

### Frontend Pages Built
- [x] Finance.tsx (with MYR precision, realised/estimated boundary)
- [x] BulkOrders.tsx (with allocation display)
- [x] Suppliers.tsx (with PO tracking)
- [x] Exceptions.tsx (with resolve/close)

---

## Milestone 3: Intelligent AI Agent

### Completed
- [x] `AgentEngine` class with full 7-phase loop: OBSERVE -> ANALYZE -> PRIORITIZE -> PLAN -> ACT -> VERIFY -> LOG
- [x] `AgentTools` class with 14 structured tools:
  - [x] Observation (5): `get_academic_schedule`, `get_business_tasks`, `get_pending_orders`, `get_inventory_status`, `get_payment_summary`
  - [x] Analysis (4): `detect_schedule_conflicts`, `estimate_packing_duration`, `find_available_time_slots`, `generate_schedule_proposal`
  - [x] Action (4): `create_internal_task`, `update_flexible_task`, `create_message_draft`, `create_business_alert`
  - [x] Verification (2): `verify_agent_action`, `get_action_history`
- [x] `TOOL_REGISTRY` with descriptions, approval requirements, parameter specs
- [x] Deterministic fallback mode (keyword-based intent detection)
- [x] Configurable OpenAI-compatible model adapter via httpx
- [x] Intent detection for 8 categories (exam_conflict, packing_management, payment_review, schedule_planning, message_generation, bulk_order_management, inventory_check, finance_summary)
- [x] Formatted response with priority, actions, approval requests
- [x] Agent audit log (`AgentLog` model with full cycle data)

### Frontend Page Built
- [x] AIAssistant.tsx (chat interface, quick prompts, actions display, mode indicator)
- [x] AgentLogs.tsx (audit trail viewer)

---

## Milestone 4: Automation & Communication

### Completed
- [x] 10 default automation jobs:
  1. Daily Academic Briefing (7:00 daily)
  2. Daily Business Briefing (8:00 daily)
  3. Upcoming Exam Warning (6:00 daily)
  4. Assignment Deadline Warning (6:00 daily)
  5. Pending Payment Review (9:00 daily)
  6. Orders Ready to Package (9:00 daily)
  7. Shipping Cutoff Check (14:00 daily)
  8. Inventory Shortage Warning (10:00 daily)
  9. Supplier Arrival Follow-up (11:00 daily)
  10. Weekly Sales & Profit Summary (Monday 9:00)
- [x] Manual "Run Now" trigger
- [x] Run history tracking (`AutomationRun` table)
- [x] 16 bilingual (EN/MS) customer message templates designed
- [x] Message lifecycle: DRAFTED -> AWAITING_APPROVAL -> APPROVED -> EXECUTED
- [x] Approval queue with approve/reject (`ApprovalRequest` model)
- [x] In-app notifications with unread badge (`Notification` model)
- [x] Settings page for user profile and preferences

### Frontend Pages Built
- [x] Automation.tsx
- [x] Messages.tsx
- [x] Approvals.tsx
- [x] Settings.tsx

---

## Milestone 5: Deployment & Demo

### Completed
- [x] Backend Dockerfile (Python 3.13-slim, uvicorn on port 8000)
- [x] Frontend Dockerfile (Node 22 build stage + Nginx Alpine serve stage)
- [x] `docker-compose.yml` (backend + frontend + seed service with health checks)
- [x] `nginx.conf` (SPA routing, /api proxy to backend, static asset caching)
- [x] `railway.toml` (Railway deployment config with health check)
- [x] `.dockerignore`
- [x] `.env.example` with all environment variables documented
- [x] Health check endpoint (`GET /health`)
- [x] Docker Compose health check (30s interval, 3 retries)
- [x] Volume persistence for SQLite (`backend-data` volume)
- [x] Seed data script (`seed_data.py`) for demo data initialization

### Frontend Pages Built
- [x] All 17 pages complete

---

## Documentation

| Document | Status | Location |
|----------|--------|----------|
| BUSINESS_RULES.md | Complete (875+ lines) | `docs/BUSINESS_RULES.md` (project root) |
| ACADEMIC_RULES.md | Complete v1.2 (~895 lines) | `docs/ACADEMIC_RULES.md` (project root) |
| README.md | Complete | `studybiz-ai/README.md` |
| ARCHITECTURE.md | Complete | `studybiz-ai/docs/ARCHITECTURE.md` |
| DEPLOYMENT.md | Complete | `studybiz-ai/docs/DEPLOYMENT.md` |
| SECURITY.md | Complete | `studybiz-ai/docs/SECURITY.md` |
| DEMO_GUIDE.md | Complete | `studybiz-ai/docs/DEMO_GUIDE.md` |
| PROGRESS.md | Complete | `studybiz-ai/docs/PROGRESS.md` (this file) |

---

## Known Limitations

1. **Conflict detection families D and E** — Families D (DEADLINE_AT_RISK) and E (CROSS_MODULE) with `crossModule` flag and `resolutionLayer` routing are specified in ACADEMIC_RULES.md section 3.1 but the agent's `detect_schedule_conflicts()` implements Families A (OVERLAP), B (PREP_INSUFFICIENT), and C (OVERLOAD). Full D/E implementation requires the complete ConflictIssue schema.

2. **2026 Malaysian holiday table** — The `campus_state` field exists on the User model and ACADEMIC_RULES.md H9 specifies state-level holiday filtering, but the static 2026 holiday table is not yet implemented.

3. **Alembic migration configuration** — Alembic is in `requirements.txt` and the `alembic/` directory exists, but migration scripts are not yet generated. Table auto-creation via `Base.metadata.create_all()` works for initial setup.

4. **APScheduler cron runner** — Automation jobs are stored in the database with `schedule_cron` fields and can be triggered manually via "Run Now", but the background scheduler daemon is not yet wired to execute jobs on their cron schedule. The `apscheduler` package is installed.

5. **Model API tool dispatch** — The OpenAI-compatible model adapter is wired (httpx client, configurable via `AI_MODEL_API_BASE` + `AI_MODEL_API_KEY`), but tool dispatch always follows the deterministic plan. The model response is not used to select tools or parameters dynamically.

6. **No multi-turn agent context** — Each agent chat request is processed independently. There is no conversation history or session-based context window. The `session_id` is generated per request, not per conversation.

7. **Message template rendering** — The `create_message_draft` tool creates drafts with placeholder body text `"[Auto-generated draft -- please review]"`. Full bilingual template rendering with variable substitution is designed but not yet implemented.

8. **No courier tracking API integration** — Tracking numbers are stored and required for the PACKED -> DISPATCHED transition, but there is no live tracking API integration for status updates.

9. **Single-operator design** — The application is designed for a single student operator per account. There is no team/organization model or role-based access control.

10. **localStorage token storage** — JWT tokens are stored in `localStorage`, which is vulnerable to XSS. For production with higher security requirements, `httpOnly` cookies should be considered.

11. **No backup strategy** — The Docker volume provides persistence but there is no automated backup mechanism for the SQLite database.

12. **npm optional dependencies** — On Windows, npm optional dependencies (rollup, esbuild native binaries) required manual installation due to npm bug #4828.
