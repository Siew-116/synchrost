# StudyBiz AI

**Academic & Business Operations Agent for Malaysian Student Entrepreneurs**

StudyBiz AI is a full-stack web application that helps Malaysian university students balance their online business operations (reselling, preorders, group orders) with their academic schedule. It features an AI agent that detects conflicts between exams and packing/shipping deadlines, proposes rescheduled tasks, drafts bilingual customer messages, and manages the full order lifecycle — all behind approval gates so the student stays in control.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI 0.115 + SQLAlchemy 2.0 + Pydantic 2.10 + Python 3.13 |
| Database | SQLite (development) / PostgreSQL (production-ready) |
| Frontend | React 18 + TypeScript 5.7 + Vite 6 + Tailwind CSS 3.4 |
| Data Fetching | TanStack React Query 5 + Axios |
| Auth | JWT (python-jose) + bcrypt password hashing |
| AI Agent | Deterministic rule-based engine with optional OpenAI-compatible model adapter |
| Scheduling | APScheduler (cron-based automation jobs) |
| Deployment | Docker Compose / Railway |
| Localization | MYR currency, Asia/Kuala_Lumpur timezone, DD/MM/YYYY dates, English + Bahasa Melayu |

---

## Quick Start

### Prerequisites

- Python 3.13+
- Node.js 22+
- npm

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Run the server (tables auto-create on startup)
python -m uvicorn app.main:app --reload --port 8000
```

The API will be available at `http://127.0.0.1:8000`. Interactive docs at `http://127.0.0.1:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`. The Vite dev server proxies `/api` requests to the backend on port 8000.

### Seed Data (Optional)

To populate the database with demo data (demo user, products, orders, academic events):

```bash
cd backend
python seed_data.py
```

---

## Demo Credentials

After seeding, log in with:

| Field | Value |
|---|---|
| Email | `nurul@studybiz.my` |
| Password | `demo123456` |

---

## API Overview

All endpoints are under `/api` and require JWT authentication (except `/api/auth/login` and `/api/auth/register`).

| Router | Prefix | Key Operations |
|---|---|---|
| Auth | `/api/auth` | Register, login, get/update profile |
| Academic | `/api/academic` | CRUD academic events (classes, exams, assignments, study sessions) |
| Customers | `/api/customers` | CRUD customer records |
| Products | `/api/products` | CRUD products, stock movements, low-stock alerts |
| Orders | `/api/orders` | CRUD orders with state machine, status history |
| Bulk Orders | `/api/bulk-orders` | CRUD group orders, two-phase cost allocation |
| Suppliers | `/api/suppliers` | CRUD supplier records |
| Exceptions | `/api/exceptions` | CRUD business exceptions (blackouts, delays, disputes) |
| Finance | `/api/finance` | Summary (realised vs estimated profit), transactions |
| Dashboard | `/api/dashboard` | Aggregated today view (priorities, packing queue, deadlines) |
| Agent | `/api/agent` | Chat endpoint, agent logs, tool registry |
| Automation | `/api/automation` | List/update automation jobs, manual trigger, run history |
| Messages | `/api/messages` | Draft CRUD, approve, mark-sent |
| Approvals | `/api/approvals` | List/decide approval requests |
| Notifications | `/api/notifications` | List, mark-read, mark-all-read |
| Export | `/api/export` | Masterlist export (Excel via openpyxl) |

Interactive Swagger UI: `http://localhost:8000/docs`

---

## Project Structure

```
studybiz-ai/
├── README.md
├── docker-compose.yml
├── railway.toml
├── .dockerignore
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   ├── DEMO_GUIDE.md
│   ├── SECURITY.md
│   └── PROGRESS.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── .env.example
│   ├── seed_data.py
│   ├── alembic/                  # Database migrations
│   ├── studybiz.db               # SQLite (dev)
│   ├── app/
│   │   ├── main.py               # FastAPI entry point
│   │   ├── config.py             # Pydantic Settings
│   │   ├── database.py           # SQLAlchemy engine + session
│   │   ├── models/
│   │   │   └── __init__.py       # All ORM models (14 tables)
│   │   ├── schemas/
│   │   │   └── __init__.py       # Pydantic request/response schemas
│   │   ├── routers/
│   │   │   ├── auth.py           # JWT auth
│   │   │   ├── academic.py       # Academic events
│   │   │   ├── customers.py
│   │   │   ├── products.py
│   │   │   ├── orders.py         # Order state machine
│   │   │   ├── bulk_orders.py    # Two-phase cost allocation
│   │   │   ├── suppliers.py
│   │   │   ├── exceptions.py     # Business exceptions
│   │   │   ├── finance.py        # Realised vs estimated profit
│   │   │   ├── dashboard.py      # Aggregated dashboard
│   │   │   ├── agent.py          # AI agent chat
│   │   │   ├── automation.py     # Cron jobs
│   │   │   ├── messages.py       # Customer message drafts
│   │   │   ├── approvals.py      # Approval queue
│   │   │   ├── notifications.py
│   │   │   └── export.py         # Excel export
│   │   ├── agent/
│   │   │   ├── engine.py         # 7-phase agent loop
│   │   │   └── tools.py          # 14 structured agent tools
│   │   └── utils/
│   │       └── auth.py           # JWT + bcrypt
│   └── tests/
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── vite.config.ts
    ├── tailwind.config.js
    └── src/
        ├── main.tsx
        ├── App.tsx               # Route definitions
        ├── contexts/
        │   └── AuthContext.tsx   # Auth provider + useAuth hook
        ├── services/
        │   └── api.ts           # Axios client + API modules
        ├── components/
        │   └── Layout.tsx        # Sidebar + header layout
        └── pages/
            ├── Login.tsx
            ├── Dashboard.tsx
            ├── AIAssistant.tsx
            ├── Orders.tsx
            ├── Calendar.tsx
            ├── Academic.tsx
            ├── Products.tsx
            ├── Customers.tsx
            ├── Finance.tsx
            ├── BulkOrders.tsx
            ├── Exceptions.tsx
            ├── Messages.tsx
            ├── Automation.tsx
            ├── Approvals.tsx
            ├── AgentLogs.tsx
            ├── Settings.tsx
            └── Suppliers.tsx
```

---

## Features by Milestone

### Milestone 1 — Foundation (Done)
- FastAPI project scaffold with SQLAlchemy ORM, 14 database models
- JWT authentication (register, login, profile)
- React + TypeScript + Vite frontend with Tailwind CSS
- Protected routing, AuthContext, Axios API service layer
- Dashboard page with today's priorities, upcoming exams, packing queue, shipping deadlines

### Milestone 2 — Business Operations (Done)
- Order lifecycle with 8-state machine and transition validation gates
- Product management with stock buckets (available, reserved, incoming), stock movements
- Customer CRUD with auto-fill support
- Supplier records and purchase orders
- Bulk/group orders with two-phase cost allocation (equal, by-value, manual)
- Rounding residual rule (last participant absorbs 1-sen discrepancy)
- Finance module with realised vs estimated profit boundary
- Business exceptions (blackout, cancellation, supplier delay, missing/defective items, disputes)
- Packaging batches and shipping batches
- Bilingual customer message templates (16 types) with DRAFT -> APPROVED -> SENT flow

### Milestone 3 — Academic Planning (Done)
- Academic event types: CLASS, EXAM, COURSEWORK, ASSIGNMENT, STUDY_SESSION, PERSONAL
- Priority framework (CRITICAL/HIGH/MEDIUM/LOW) with deadline-proximity escalation
- Conflict detection across 5 families (OVERLAP, PREP_INSUFFICIENT, OVERLOAD, DEADLINE_AT_RISK, CROSS_MODULE)
- Schedule proposal generation with available time-slot finder
- Fixed vs flexible event matrix
- Rest period protection (sleep blocks, meal breaks, recovery days)
- Inter-module contract with business operations (DisruptionEvent protocol)

### Milestone 4 — AI Agent (Done)
- 7-phase agent loop: OBSERVE -> ANALYZE -> PRIORITIZE -> PLAN -> ACT -> VERIFY -> LOG
- 14 structured agent tools (observation, analysis, action, verification)
- Deterministic rule-based fallback (no external API required)
- Optional OpenAI-compatible model adapter (configurable via environment)
- Intent detection (exam conflict, packing management, payment review, schedule planning, message generation, inventory, finance)
- Agent audit log with full observation/analysis/plan/action/verification trail
- Approval gate for consequential actions (message drafts require approval before sending)

### Milestone 5 — Automation & Polish (Done)
- 10 default automation jobs (daily briefings, exam/deadline warnings, payment review, inventory alerts, weekly summary)
- Cron-based scheduling with manual trigger support
- Notification system (in-app alerts)
- Excel export (masterlist via openpyxl)
- Settings page for user profile and preferences

### Milestone 6 — Deployment (Done)
- Docker Compose (backend + frontend + seed service)
- Dockerfiles for backend (Python 3.13-slim) and frontend (Node 22 build + Nginx serve)
- Railway deployment configuration (railway.toml)
- Environment variable management (.env.example)
- Health check endpoint (/health)

---

## Documentation

- [Architecture](docs/ARCHITECTURE.md) — System architecture, agent loop, state machine, cost allocation, conflict detection
- [Deployment](docs/DEPLOYMENT.md) — Docker Compose, Railway, environment variables, database migration
- [Demo Guide](docs/DEMO_GUIDE.md) — Step-by-step demo walkthrough
- [Security](docs/SECURITY.md) — JWT, bcrypt, approval gates, CORS, data isolation
- [Progress](docs/PROGRESS.md) — Milestone completion status and known limitations
- [Business Rules](../docs/BUSINESS_RULES.md) — Full business operation rules specification
- [Academic Rules](../docs/ACADEMIC_RULES.md) — Full academic scheduling rules specification

---

## License

This project is built for the Dormathon 2026 hackathon.
