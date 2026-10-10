# Synchrost AI

Your AI Co-Admin. Your Business, Still Moving.

StudyBiz AI is an agentic AI operations assistant for student entrepreneurs who manage Telegram channels or groups for merchandise group buys, preorders, shared purchases, and small student-run businesses.

# Demo live link
https://synchrost.onrender.com/

# Presentation slides
https://canva.link/oio8j0n3lowz8sv

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

- Python 3.11+ (tested on Python 3.13)
- No Node.js required - the frontend is bundled as a single HTML file served by the backend

### Step 1: Install Dependencies

```bash
cd studybiz-ai/backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings python-dotenv httpx
```

### Step 2: Configure Environment

```bash
cp .env.example .env            # Windows: copy .env.example .env
```

Edit `.env` with your configuration (see Configuration section below).

### Step 3: Run the Server

```bash
cd backend
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The database auto-initializes and seeds demo data on first run.

Open http://127.0.0.1:8000 in your browser.

## Configuration

Edit `backend/.env` with these values:

### Minimum for Demo Mode (no external services needed)

```env
DEMO_MODE=true
EXAM_MODE=false
```

That is it. The app runs with:
- Deterministic AI (pattern-based intent matching and order extraction)
- Simulated Telegram environment (send test messages via Settings page)
- SQLite database with seed data (10 orders, 8 customers, 3 exceptions)

### Full Connected Mode

```env
# Telegram (from @BotFather)
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrSTUvwxYZ
TELEGRAM_CONNECTED=true
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/telegram/webhook

# AI / LLM (optional - improves AI responses)
LLM_API_KEY=sk-your-openai-key
LLM_MODEL=gpt-4o-mini

# Turn off demo mode
DEMO_MODE=false
```

### All Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| DEMO_MODE | No | true | If true, runs without external services |
| EXAM_MODE | No | false | Sets default for Busy Mode (rename in UI) |
| TELEGRAM_BOT_TOKEN | For Telegram | empty | Bot token from @BotFather |
| TELEGRAM_CONNECTED | No | false | Set true when Telegram is live |
| TELEGRAM_WEBHOOK_URL | No | empty | Public URL for Telegram webhooks |
| LLM_API_KEY | No | empty | OpenAI-compatible API key |
| LLM_API_BASE | No | https://api.openai.com/v1 | LLM API base URL |
| LLM_MODEL | No | gpt-4o-mini | Model name |
| DATABASE_URL | No | sqlite:///./studybiz.db | Database connection string |
| HOST | No | 0.0.0.0 | Server host |
| PORT | No | 8000 | Server port |

## App Navigation

The sidebar has three sections:

**Main**
- Overview: Dashboard with key metrics, AI summary, and quick actions
- AI Co-Admin: Chat interface to query your AI assistant

**Operations**
- Orders: All orders with tabs (All / Pending / Confirmed / Completed / Cancelled). Click any order for full detail including payments and messages
- Customers: Customer list and conversations in one module with tabs
- Approvals: Exceptions requiring admin decisions (approve, reject, request info)

**Configuration**
- Automation Rules: Toggle rules on/off, edit settings inline
- Settings: Busy Mode toggle, Telegram status, test AI agent, env config

## Demo Script (for pitching)

1. **Open Overview** - Show the hero banner with live metrics. Point to the AI Summary: "This is what the AI tells me about my business right now."

2. **Show Approvals** - Click the 3 exceptions. Explain: "The AI caught a late order, an unverified payment, and a cancellation request. I just approve or reject."

3. **Go to Orders** - Click the Pending Payment tab. Click an order to expand details. Show the action buttons (Confirm, Cancel, Mark Preparing, etc.)

4. **AI Co-Admin** - Click a suggestion like "How many orders?" Show the AI responding with real data.

5. **Settings > Test AI Agent** - Type a customer name and message like "Hi, can I order two black hoodies size M?" Show the AI creating an order automatically.

6. **Automation Rules** - Toggle a rule on/off. Click Edit to show the inline configuration.

7. **Busy Mode** - Go to Settings, toggle Busy Mode on. Explain: "When I am in class, the AI keeps running but queues sensitive decisions."

## Modes

### Demo Mode (default)

Runs without any external credentials. All business logic, validation, and state transitions work exactly as in connected mode.

### Busy Mode (formerly Exam Mode)

Toggle on/off from Settings page. When enabled:
- Routine operations continue (order creation, status updates)
- Non-urgent notifications are batched
- Sensitive decisions are queued for admin review
- Payment controls and cancellation policies are NOT overridden

## Deployment Guide

### Local Deployment (for demo or development)

1. Clone the repository:
```bash
git clone https://github.com/Siew-116/synchrost.git
cd synchrost/studybiz-ai
```

2. Create a Python virtual environment and install dependencies:
```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings python-dotenv httpx
```

3. Copy the environment template:
```bash
cp .env.example .env            # Windows: copy .env.example .env
```

4. Edit `.env` - for demo mode, just keep `DEMO_MODE=true`.

5. Start the server:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

6. Open http://127.0.0.1:8000 in your browser.

### Production Deployment (with Telegram)

1. Follow steps 1-4 above.

2. Edit `.env` with real credentials:
```env
DEMO_MODE=false
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
TELEGRAM_CONNECTED=true
TELEGRAM_WEBHOOK_URL=https://your-domain.com/api/telegram/webhook
LLM_API_KEY=your_openai_api_key
```

3. Set up a reverse proxy (nginx, Caddy) to forward port 443 to port 8000.

4. Start the server:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

5. Set the Telegram webhook:
```bash
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/setWebhook" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://your-domain.com/api/telegram/webhook"}'
```

6. Test by sending a message to your Telegram bot.

### Telegram Bot Setup

1. Open Telegram and search for @BotFather
2. Send `/newbot` and follow the prompts
3. Copy the bot token (format: `123456789:ABCdefGHIjklMNOpqrSTUvwxYZ`)
4. Set it as `TELEGRAM_BOT_TOKEN` in your `.env`
5. Set `TELEGRAM_CONNECTED=true`
6. Set `TELEGRAM_WEBHOOK_URL` to your public URL + `/api/telegram/webhook`

## Tech Stack

- Backend: FastAPI, SQLAlchemy, SQLite
- Frontend: Single-file HTML/CSS/JS (served by backend)
- Integration: Telegram Bot API
- AI: Deterministic demo mode or OpenAI-compatible LLM

## Safety Rules

- The AI never marks a payment as paid without manual verification
- Customer screenshots are evidence for review, not proof of payment
- The AI cannot issue refunds or make financial commitments
- Orders cannot bypass deadlines or capacity limits without admin approval
- All consequential actions are logged and auditable
- Bot tokens and API keys are never exposed in frontend code

## License

MIT
