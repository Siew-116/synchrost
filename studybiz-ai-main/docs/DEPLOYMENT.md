# Deployment

## Docker Compose (Local / Self-Hosted)

### Prerequisites

- Docker 24+
- Docker Compose v2

### Quick Start

```bash
# From the project root (studybiz-ai/)
docker compose up --build
```

This starts three services:

| Service | Container | Port | Purpose |
|---|---|---|---|
| backend | studybiz-backend | 8000 | FastAPI application |
| frontend | studybiz-frontend | 5173 (->80) | Nginx serving built React SPA |
| seed | studybiz-seed | — | One-shot seed data initialization |

### What Happens on Start

1. **Backend** container builds from `backend/Dockerfile` (Python 3.13-slim). Tables auto-create on startup via `Base.metadata.create_all()`. Health check runs every 30s on `/health`.
2. **Frontend** container builds from `frontend/Dockerfile` (Node 22 build stage + Nginx Alpine serve stage). Nginx proxies `/api` requests to the backend container. SPA routing falls back to `index.html`.
3. **Seed** container runs `python seed_data.py` once the backend is healthy, populating the SQLite database with demo data (demo user, products, orders, academic events).

### Accessing the Application

- Frontend: `http://localhost:5173`
- Backend API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Demo login: `nurul@studybiz.my` / `demo123456`

### Stopping

```bash
docker compose down          # Stop containers
docker compose down -v       # Stop + delete data volume
```

### Architecture

```
┌──────────────────────────────────────────────────┐
│                 docker-compose.yml               │
│                                                  │
│  ┌─────────────────┐    ┌─────────────────────┐ │
│  │  studybiz-       │    │  studybiz-frontend   │ │
│  │  backend         │    │  (Nginx)             │ │
│  │  (FastAPI)       │    │  :5173 -> :80        │ │
│  │  :8000           │◀───│  /api proxy           │ │
│  └──────┬──────────┘    └─────────────────────┘ │
│         │                                         │
│         │    ┌─────────────────────┐             │
│         │    │  studybiz-seed       │             │
│         └───▶│  (one-shot, exits)   │             │
│              └─────────────────────┘             │
│                                                  │
│  ┌────────────────────────────────────────┐     │
│  │  Volume: backend-data (/app/data)       │     │
│  │  SQLite: data/studybiz.db               │     │
│  └────────────────────────────────────────┘     │
└──────────────────────────────────────────────────┘
```

### Dockerfiles

**Backend** (`backend/Dockerfile`):
- Base: `python:3.13-slim`
- Installs gcc for bcrypt/psycopg2 compilation
- Copies requirements, pip installs, copies app
- Creates `/app/data` for SQLite storage
- Runs uvicorn on port 8000

**Frontend** (`frontend/Dockerfile`):
- Build stage: `node:22-alpine` — installs deps, runs `npm run build`
- Serve stage: `nginx:alpine` — copies built assets to nginx html dir
- Nginx config (`nginx.conf`): SPA fallback routing, `/api` proxy to backend, static asset caching (1y)

---

## Railway Deployment

### Prerequisites

- Railway account (https://railway.app)
- Railway CLI (optional) or GitHub integration

### Steps

1. **Connect repository** — In Railway, create a new project from your GitHub repo containing the `studybiz-ai/` directory.

2. **Backend service**:
   - Source: `backend/` directory
   - Start command: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - Railway auto-detects the `railway.toml` configuration:
     ```toml
     [deploy]
     startCommand = python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT
     healthcheckPath = /health
     healthcheckTimeout = 30
     restartPolicyType = "ON_FAILURE"
     restartPolicyMaxRetries = 3

     [env]
     PYTHONPATH = "/app"
     APP_ENV = "production"
     ```
   - Health check: Railway probes `/health` (returns `{"status": "healthy"}`)

3. **Frontend service**:
   - Source: `frontend/` directory
   - Build command: `npm ci --legacy-peer-deps && npm run build`
   - Start command: `npx serve dist --single` (or use the Nginx Dockerfile)
   - Set `VITE_API_BASE_URL` to the Railway backend URL

4. **Database**:
   - Add a PostgreSQL plugin in Railway
   - Set `DATABASE_URL` to the Railway-provided connection string
   - Format: `postgresql://user:password@host:5432/railway`

5. **Environment variables** — Set all variables listed below in the Railway dashboard.

6. **Deploy** — Railway will build and deploy on every push to the main branch.

### Railway Environment

The `railway.toml` file configures:
- Start command using `$PORT` (Railway injects this)
- Health check on `/health`
- Restart policy: `ON_FAILURE` with max 3 retries
- `PYTHONPATH=/app` and `APP_ENV=production`

---

## Environment Variables

All environment variables are defined in `backend/.env.example` and managed via Pydantic Settings (`app/config.py`).

| Variable | Default | Description |
|---|---|---|
| `APP_ENV` | `development` | Environment mode |
| `DATABASE_URL` | `sqlite:///./data/studybiz.db` | Database connection string. Use `postgresql://...` for production |
| `JWT_SECRET_KEY` | `dev-secret-key-change-in-production` | JWT signing secret. **Change in production.** |
| `JWT_ALGORITHM` | `HS256` | JWT algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `1440` (24h) | JWT token expiry. Docker Compose uses `10080` (7 days) |
| `CORS_ORIGINS` | `http://localhost:5173,...` | Comma-separated allowed origins |
| `AI_MODEL_API_BASE` | (empty) | OpenAI-compatible API base URL. Leave empty for deterministic mode |
| `AI_MODEL_API_KEY` | (empty) | API key for model service |
| `AI_MODEL_NAME` | `gpt-4o-mini` | Model name |
| `TIMEZONE` | `Asia/Kuala_Lumpur` | Application timezone |
| `PORT` | `8000` | Port (Railway injects automatically) |

### .env File

Copy `.env.example` to `.env` in the backend directory:

```bash
cd backend
cp .env.example .env
```

Edit values as needed. The Pydantic Settings class reads from `.env` automatically.

---

## Database Migration (SQLite -> PostgreSQL)

### Current State

Development uses SQLite (`studybiz.db`). The SQLAlchemy models are database-agnostic and the `database.py` module auto-detects SQLite vs PostgreSQL:

```python
# database.py
connect_args = {}
if settings.use_sqlite:
    connect_args["check_same_thread"] = False

engine = create_engine(settings.DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

# SQLite: enable foreign key enforcement
if settings.use_sqlite:
    @event.listens_for(engine, "connect")
    def _fk_pragma_on_connect(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
```

### Migration Steps

1. **Switch the connection string** — Set `DATABASE_URL` to a PostgreSQL connection string:
   ```
   DATABASE_URL=postgresql://user:password@localhost:5432/studybiz
   ```

2. **Auto-create tables** — On startup, `Base.metadata.create_all(bind=engine)` creates all tables in PostgreSQL. This works for initial setup.

3. **Alembic migrations** (for schema evolution) — The project includes Alembic (`alembic/` directory) and `alembic` in `requirements.txt`. To set up proper migrations:

   ```bash
   cd backend
   source venv/bin/activate

   # Initialize Alembic (if not already done)
   alembic init alembic

   # Edit alembic.ini to set sqlalchemy.url = your DATABASE_URL
   # Edit alembic/env.py to import your models:
   #   from app.database import Base
   #   from app.models import *  # noqa
   #   target_metadata = Base.metadata

   # Generate initial migration
   alembic revision --autogenerate -m "Initial schema"

   # Apply migration
   alembic upgrade head
   ```

4. **Seed data** — After migration, run the seed script to populate demo data:
   ```bash
   python seed_data.py
   ```

### Notes

- All monetary fields use `Numeric(12, 2)` which maps to `NUMERIC(12,2)` in PostgreSQL and `REAL` in SQLite. Both store decimal correctly.
- The `SQLEnum` columns (OrderStatus, EventType, etc.) work identically in both databases.
- The `JSON` column type (used in some optional fields) maps to `JSONB` in PostgreSQL and `TEXT` in SQLite.
- `psycopg2-binary` is included in `requirements.txt` for PostgreSQL support.
