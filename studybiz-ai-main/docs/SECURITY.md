# Security

## Authentication Flow

### JWT Token-Based Authentication

StudyBiz AI uses JSON Web Tokens (JWT) for stateless authentication. The flow is:

```
1. Client sends credentials:
   POST /api/auth/login
   Body: { "email": "nurul@studybiz.my", "password": "demo123456" }

2. Server verifies password (bcrypt.checkpw)
   └── If invalid: 401 Unauthorized
   └── If valid: creates JWT with payload { "sub": user.email, "exp": now + 1440min }

3. Server returns token:
   { "access_token": "eyJhbG...", "token_type": "bearer", "user": {...} }

4. Client stores token in localStorage
   └── Axios interceptor attaches "Authorization: Bearer <token>" to all requests

5. On each protected request:
   └── get_current_user dependency decodes JWT
   └── Extracts email from "sub" claim
   └── Queries User table for the user
   └── Checks user.is_active
   └── Returns User object or raises 401

6. On 401 response:
   └── Axios interceptor clears localStorage
   └── Redirects to /login
```

### Token Configuration

| Setting | Value | Notes |
|---|---|---|
| Algorithm | HS256 | HMAC-SHA256 symmetric |
| Secret key | `SECRET_KEY` env var | **Must be changed in production** |
| Expiry | 1440 minutes (24h) | Configurable via `ACCESS_TOKEN_EXPIRE_MINUTES` |
| Storage | localStorage (client-side) | Vulnerable to XSS; see [Considerations](#considerations) |

### Token Creation

```python
# app/utils/auth.py
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
```

### Token Verification

```python
# app/utils/auth.py
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    email = payload.get("sub")
    user = db.query(User).filter(User.email == email).first()
    if not user or not user.is_active:
        raise credentials_exception
    return user
```

---

## Password Hashing

### bcrypt

Passwords are hashed using bcrypt with automatic salt generation. Raw passwords are never stored or logged.

**Hashing:**
```python
def get_password_hash(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(pwd_bytes, salt)
    return hashed.decode("utf-8")
```

**Verification:**
```python
def verify_password(plain_password: str, hashed_password: str) -> bool:
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode("utf-8")
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password)
```

### Properties

| Property | Value |
|---|---|
| Algorithm | bcrypt (Blowfish cipher) |
| Salt | Auto-generated per password |
| Work factor | Default (12 rounds) |
| Storage | `User.hashed_password` column |

---

## Approval Gate for Consequential Agent Actions

### Principle

The business rules spec mandates: *"Automation drafts and alerts; the operator decides and confirms every outward action."*

No customer-facing or money-moving action is auto-executed. The agent can draft and analyze, but the operator must approve before execution.

### Implementation

The `TOOL_REGISTRY` in `app/agent/tools.py` marks each tool with `requires_approval`:

```python
TOOL_REGISTRY = {
    "get_academic_schedule": { ..., "requires_approval": False },
    "detect_schedule_conflicts": { ..., "requires_approval": False },
    "create_message_draft": { ..., "requires_approval": True },   # <-- gated
    ...
}
```

When the agent calls a tool with `requires_approval: True`:

1. The tool executes (creates the draft/record) but the result is masked in the response as `"[requires approval]"`
2. An entry is added to `approval_requests` in the agent response
3. The user reviews the draft in the Approvals page
4. The user approves or rejects via `PUT /api/approvals/{id}/decide`
5. Only after approval can the action proceed to execution (e.g., message marked as SENT)

### Gated Actions

| Action | Tool | Gate |
|---|---|---|
| Send customer message | `create_message_draft` | Requires approval before sending |
| Issue refund | N/A (manual via exceptions) | Requires approval + transfer reference |
| Cancel order (paid) | N/A (manual via orders) | Requires refund decision |
| Place supplier PO | N/A (manual via suppliers) | Requires purchase proof |

### Approval Queue

The `ApprovalRequest` model stores:
- `action_type` — Type of action (send_message, refund, cancel_order, etc.)
- `description` — Human-readable description
- `payload` — JSON string with action details
- `status` — `pending` / `approved` / `rejected`
- `resolved_by` — Email of the user who decided
- `result` — Optional note from the resolver

### Message Draft Flow

Customer messages follow a strict 3-state flow:

```
DRAFTED -> AWAITING_APPROVAL -> APPROVED -> EXECUTED
                                          -> FAILED
```

No template is ever sent without passing through `DRAFT -> APPROVED -> SENT`. A template with an unfilled required variable cannot be approved.

---

## CORS Configuration

### Setup

CORS is configured in `app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,   # from CORS_ORIGINS env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Allowed Origins

| Environment | Origins |
|---|---|
| Development (local) | `http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:3000` |
| Docker Compose | `http://localhost:5173`, `http://127.0.0.1:5173`, `http://localhost:80` |
| Production | Set via `CORS_ORIGINS` env var (comma-separated) |

### Configuration

The `CORS_ORIGINS` environment variable accepts a comma-separated list:

```
CORS_ORIGINS=https://studybiz.example.com,https://www.studybiz.example.com
```

The `cors_origins_list` property in `Settings` parses this into a list:

```python
@property
def cors_origins_list(self) -> List[str]:
    return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
```

---

## Data Isolation

### User-Scoped Queries

Every database query in the application is scoped by `user_id`. The `get_current_user` dependency extracts the authenticated user, and all routers filter by `user_id`:

```python
# Example from orders.py
@router.get("/", response_model=List[OrderResponse])
def list_orders(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Order).filter(Order.user_id == current_user.id)
    ...
```

This pattern is applied consistently across all 16 routers:

| Router | User-Scoped Filter |
|---|---|
| Academic | `AcademicEvent.user_id == current_user.id` |
| Customers | `Customer.user_id == current_user.id` |
| Products | `Product.user_id == current_user.id` |
| Orders | `Order.user_id == current_user.id` |
| Bulk Orders | `BulkOrder.user_id == current_user.id` |
| Suppliers | `Supplier.user_id == current_user.id` |
| Exceptions | `BusinessException.user_id == current_user.id` |
| Finance | `FinanceTransaction.user_id == current_user.id` |
| Agent Logs | `AgentLog.user_id == current_user.id` |
| Approvals | `ApprovalRequest.user_id == current_user.id` |
| Notifications | `Notification.user_id == current_user.id` |
| Automation | `AutomationJob.user_id == current_user.id` |
| Messages | `MessageDraft.user_id == current_user.id` |

### Single-Operator Design

The application is designed for a **single student operator**. There is no multi-tenant organization model — each user account represents one independent student business. Data isolation is enforced at the query level, not via row-level security.

### No Data Leakage

- A user cannot access another user's orders, products, or academic events
- The agent tools (`AgentTools` class) accept `self.user` and scope all queries by `self.user.id`
- Dashboard data is aggregated per-user
- Finance transactions are per-user

---

## Considerations

### Token Storage

JWT tokens are stored in `localStorage`, which is vulnerable to Cross-Site Scripting (XSS) attacks. In a production deployment with higher security requirements, consider:

- Using `httpOnly` cookies instead of localStorage
- Implementing refresh token rotation
- Adding CSRF protection if using cookies

### Secret Key

The default `SECRET_KEY` in `config.py` is `dev-secret-key-change-in-production`. **This must be changed in production** via the `JWT_SECRET_KEY` / `SECRET_KEY` environment variable.

### SQL Injection Protection

All database queries use SQLAlchemy ORM with parameterized queries. No raw SQL is used in the application, preventing SQL injection.

### Input Validation

All API requests are validated by Pydantic schemas (`app/schemas/__init__.py`). Invalid input is rejected with 422 Unprocessable Entity before reaching the database layer.
