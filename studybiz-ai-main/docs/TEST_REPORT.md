# StudyBiz AI — Test Report

**Date:** October 10, 2026  
**Application:** StudyBiz AI v1.0  
**Test Environment:** Windows, Python 3.13, Node 22, SQLite  

---

## 1. Test Summary

| Test Category | Total | Passed | Failed | Status |
|--------------|-------|--------|--------|--------|
| Full-Stack API Integration | 10 | 10 | 0 | ✅ PASS |
| Demo Scenario | 8 | 8 | 0 | ✅ PASS |
| Agent Tool Execution | 4 | 4 | 0 | ✅ PASS |
| Backend pytest | 50 | 50 | 0 | ✅ PASS |
| Playwright E2E | — | — | — | Written, not yet run |

---

## 2. Full-Stack API Integration Tests

Verified via Python httpx client through Vite proxy (127.0.0.1:5173 → 127.0.0.1:8000).

| # | Test | Endpoint | Status | Result |
|---|------|----------|--------|--------|
| 1 | Backend health | GET /health | 200 | ✅ {"status":"healthy","timestamp":"ok"} |
| 2 | Frontend HTML | GET / (5173) | 200 | ✅ React app served |
| 3 | API proxy health | GET /api/health via 5173 | 404* | ✅ (expected: health endpoint not under /api prefix) |
| 4 | Login via proxy | POST /api/auth/login | 200 | ✅ Token issued, user: Nurul Aisyah Rahman |
| 5 | Dashboard data | GET /api/dashboard/ | 200 | ✅ 30 orders, 9 paid, 1 exam |
| 6 | Orders list | GET /api/orders/ | 200 | ✅ 30 orders returned |
| 7 | Finance summary | GET /api/finance/summary | 200 | ✅ Realised RM 202, Estimated RM 1,045 |
| 8 | Agent chat | POST /api/agent/chat | 200 | ✅ CRITICAL priority, 4 actions |
| 9 | Automation jobs | GET /api/automation/ | 200 | ✅ 10 jobs configured |
| 10 | Messages | GET /api/messages/ | 200 | ✅ 1 message draft |

*Note: /health is served at backend root without /api prefix. All /api/* routes proxy correctly.

---

## 3. Demo Scenario Results

### Scenario: Exam Tomorrow + 9 Orders to Pack + Shipping Cutoff

| Step | Feature | Expected | Actual | Pass |
|------|---------|----------|--------|------|
| 1 | Login | JWT token | Token issued | ✅ |
| 2 | Dashboard stats | 30 orders, 9 paid, 1 exam | 30/9/1 | ✅ |
| 3 | Upcoming exam | Database Systems Final Exam, 1 day away | CSC3013, 1 day | ✅ |
| 4 | Packing queue | 9 orders to pack | 9 orders, 99 min (1.6h) | ✅ |
| 5 | Calendar warning | Shipping deadline | SB-20261010-0007, 1 day | ✅ |
| 6 | AI Agent | CRITICAL conflict detection | Priority: CRITICAL, 4 tools | ✅ |
| 7 | Finance | Realised + Estimated profit | RM 202 / RM 1,045 | ✅ |
| 8 | Automation | 10 jobs configured | 10 jobs (all paused) | ✅ |

---

## 4. Agent Tool Execution

| Tool | Purpose | Approval Required | Result | Details |
|------|---------|-------------------|--------|---------|
| detect_schedule_conflicts | Find exam-vs-business conflicts | No | ✅ SUCCESS | Found CRITICAL: Exam tomorrow, 9 orders need packing (99 min) |
| estimate_packing_duration | Calculate packing time for paid orders | No | ✅ SUCCESS | 9 orders, 99 minutes total, 1.6 hours |
| find_available_time_slots | Find open slots in schedule | No | ✅ SUCCESS | 10 slots found (1-hour each, 11:00-16:30) |
| generate_schedule_proposal | Generate balanced schedule | No | ✅ SUCCESS | Recommended splitting into 2-3 sessions, protect revision time |

### Agent Response:
```
**Priority: CRITICAL**

📚 Exam: **Database Systems Final Exam**
   When: 11/10/2026 09:00
   Priority: critical

📦 You have **9** paid orders to pack
   Total packing time: **1.6 hours** (99 minutes)

✅ **Available packing slots:**
   • 10/10 11:00 - 12:00
   • 10/10 11:30 - 12:30
   • 10/10 12:00 - 13:00

⚠️ I recommend packing **before or after the exam** to protect your revision time.
```

---

## 5. Order State Machine Verification

### Validated Transitions (from seed data):
| From | To | Gate | Verified |
|------|----|------|----------|
| PENDING | CONFIRMED | None | ✅ |
| CONFIRMED | PAID | None | ✅ |
| PAID | PACKED | Payment required | ✅ (amount_paid > 0) |
| PACKED | DISPATCHED | Tracking number required | ✅ (tracking_number set) |
| DISPATCHED | DELIVERED | None | ✅ |
| Any → EXCEPTION | — | ✅ |
| EXCEPTION → PAID/PACKED/DISPATCHED | — | ✅ (recovery) |

### Order Status Distribution (seed data):
| Status | Count |
|--------|-------|
| pending | 3 |
| confirmed | 3 |
| paid | 9 |
| packed | 5 |
| dispatched | 2 |
| delivered | 4 |
| cancelled | 2 |
| exception | 2 |
| **Total** | **30** |

---

## 6. Finance Boundary Verification

| Metric | Expected Rule | Actual Value | Pass |
|--------|--------------|--------------|------|
| Gross Sales | Sum of subtotals (realised + estimated) | RM 1,933.00 | ✅ |
| Net Sales | Gross - Discounts - Refunds | RM 1,933.00 | ✅ |
| Realised Profit | DELIVERED orders only | RM 202.00 | ✅ |
| Estimated Profit | PAID + PACKED + DISPATCHED | RM 1,045.00 | ✅ |
| Outstanding Payments | Balance due (not cancelled/delivered) | RM 1,033.00 | ✅ |
| Product Cost | Sum of cost_price × qty | RM 941.00 | ✅ |
| Shipping Charged | Sum of shipping_charged | RM 104.00 | ✅ |
| Shipping Expenses | Sum of shipping_cost | RM 51.00 | ✅ |

---

## 7. Seed Data Verification

| Entity | Count | Verified |
|--------|-------|----------|
| Users | 2 (nurul@studybiz.my, ariff@studybiz.my) | ✅ |
| Products | 12 (K-pop merch) | ✅ |
| Customers | 30 | ✅ |
| Orders | 30 (8 different statuses) | ✅ |
| Bulk Orders | 2 | ✅ |
| Suppliers | 2 | ✅ |
| Exceptions | 5 (supplier delay, cancellation, missing item, defective item, blackout) | ✅ |
| Purchase Orders | 2 | ✅ |
| Academic Events | 6 (including exam tomorrow) | ✅ |
| Notifications | 5 | ✅ |
| Message Drafts | 1 | ✅ |
| Agent Logs | 1 | ✅ |
| Automation Jobs | 10 | ✅ |

---

## 8. Test Environment

- **OS:** Windows 10
- **Python:** 3.13.12 (managed)
- **Node:** 22.22.2 (managed)
- **Backend:** FastAPI + Uvicorn on port 8000
- **Frontend:** Vite dev server on port 5173
- **Database:** SQLite (studybiz.db)
- **Test Client:** httpx (Python) for API tests
- **Demo Credentials:** nurul@studybiz.my / demo123456

---

## 9. Known Issues

1. **npm optional dependencies bug (#4828):** `@rollup/rollup-win32-x64-msvc` and `@esbuild/win32-x64` not installed by default on Windows. Fixed by manual `npm install --force`.
2. **passlib/bcrypt 4.x incompatibility:** passlib 1.7.4 fails with bcrypt 4.x (`__about__` attribute missing). Fixed by rewriting auth to use bcrypt directly.
3. **Health endpoint path:** `/health` is served at backend root, not under `/api` prefix. Frontend proxy works correctly for all `/api/*` routes.

---

**Test conducted by:** StudyBiz AI Development Team  
**Report date:** October 10, 2026
