# StudyBiz AI

Your AI Co-Admin. Your Business, Still Moving.

StudyBiz AI is an agentic AI operations assistant for student entrepreneurs who manage Telegram channels or groups for merchandise group buys, preorders, shared purchases, and small student-run businesses.

## What It Does

A customer sends a Telegram message. The AI:

1. Understands the customer's intention
2. Extracts order information from natural language
3. Validates against product, stock, deadline, and business-policy records
4. Executes permitted business actions (create order, check status, etc.)
5. Updates the database with the result
6. Sends an accurate response to the customer
7. Escalates exceptions (late orders, unverified payments, complaints) to the admin

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Copy and configure environment
cp ../.env.example ../.env

# Run (database auto-initializes and seeds on first run)
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173 in your browser.

## Modes

### Demo Mode (default)

Runs without any external credentials. Uses:
- Deterministic AI (pattern-based intent matching and order extraction)
- Simulated Telegram environment (send test messages via the Settings page)
- SQLite database with seed data

All business logic, validation, and state transitions work exactly as in connected mode.

### Connected Mode

Set these in `.env`:
- `TELEGRAM_BOT_TOKEN` - from @BotFather on Telegram
- `TELEGRAM_CONNECTED=true`
- `TELEGRAM_WEBHOOK_URL` - your public URL for webhooks
- `LLM_API_KEY` - OpenAI-compatible API key (optional)
- `DEMO_MODE=false`

## Project Structure

```
studybiz-ai/
  .env.example          # Environment configuration template
  backend/
    requirements.txt    # Python dependencies
    app/
      main.py           # FastAPI entry point
      config.py         # Settings
      database.py       # SQLAlchemy models
      seed.py           # Demo data seeding
      routers/          # API endpoints
        dashboard.py
        campaigns.py
        orders.py
        customers.py
        inbox.py
        exceptions.py
        supplier.py
        automation.py
        agent.py
        telegram_api.py
        settings.py
      services/
        agent.py        # AI agent with business tools
        telegram.py     # Telegram Bot API integration
  frontend/
    package.json
    vite.config.js
    tailwind.config.js
    src/
      App.jsx           # Main app with sidebar navigation
      pages/
        Overview.jsx
        AIAdmin.jsx
        GroupBuys.jsx
        Orders.jsx
        Customers.jsx
        Inbox.jsx
        Approvals.jsx
        SupplierSummary.jsx
        AutomationRules.jsx
        Settings.jsx
```

## Key Features

- AI Co-Admin: Ask about orders, customers, supplier summaries, and exceptions
- Group Buy Management: Create campaigns with products, variants, deadlines, and policies
- Order Management: Track order, payment, and fulfilment status independently
- Customer Inbox: View conversations with AI intent classification
- Approvals & Exceptions: Resolve late orders, unverified payments, cancellations
- Supplier Summary: Calculate quantities by variant, export CSV
- Automation Rules: Configure business hours, exam mode, escalation conditions
- Telegram Integration: Webhook and polling support with idempotent processing
- Demo Mode: Full functionality without external credentials

## Safety Rules

- The AI never marks a payment as paid without manual verification
- Customer screenshots are evidence for review, not proof of payment
- The AI cannot issue refunds or make financial commitments
- Orders cannot bypass deadlines or capacity limits without admin approval
- All consequential actions are logged and auditable
- Bot tokens and API keys are never exposed in frontend code

## Tech Stack

- Backend: FastAPI, SQLAlchemy, SQLite
- Frontend: React, Vite, Tailwind CSS
- Integration: Telegram Bot API
- AI: Deterministic demo mode or OpenAI-compatible LLM

## License

MIT
