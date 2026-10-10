"""StudyBiz AI - Dormathon 2026 Demo Scenario Script"""
import httpx

BASE = "http://127.0.0.1:8000"

print("=" * 70)
print("STUDYBIZ AI - DORMATHON 2026 DEMO SCENARIO")
print("Track 2: Agentic Solutions")
print("=" * 70)
print()

# 1. Login
print("[1/8] Logging in as Nurul (student entrepreneur)...")
r = httpx.post(f"{BASE}/api/auth/login", json={"email": "nurul@studybiz.my", "password": "demo123456"})
token = r.json()["access_token"]
user = r.json()["user"]
h = {"Authorization": f"Bearer {token}"}
print(f"  User: {user['full_name']} ({user['email']})")
print(f"  Campus: {user.get('campus', 'Universiti Malaya')}")
print()

# 2. Dashboard overview
print("[2/8] Fetching dashboard...")
r = httpx.get(f"{BASE}/api/dashboard/", headers=h)
dash = r.json()
stats = dash.get("stats", {})
print(f"  Total Orders: {stats.get('total_orders', 0)}")
print(f"  Paid Orders (ready to pack): {stats.get('paid_orders', 0)}")
print(f"  Packed Orders (ready to ship): {stats.get('packed_orders', 0)}")
print(f"  Open Exceptions: {stats.get('open_exceptions', 0)}")
print(f"  Upcoming Exams: {stats.get('upcoming_exams', 0)}")
print()

# 3. Upcoming exams
print("[3/8] Checking upcoming exams...")
if dash.get("upcoming_exams"):
    for exam in dash["upcoming_exams"]:
        days = exam.get("days_until", "?")
        label = "TODAY" if days == 0 else f"{days} day(s) away"
        print(f"  EXAM: {exam['title']}")
        print(f"    Course: {exam.get('course_code', 'N/A')}")
        print(f"    Date: {exam.get('date', '?')} ({label})")
        print(f"    Priority: {exam.get('priority', '?')}")
else:
    print("  No upcoming exams")
print()

# 4. Packing queue
print("[4/8] Checking packing queue...")
if dash.get("packing_queue"):
    total_minutes = sum(o.get("estimated_packing_minutes", 0) for o in dash["packing_queue"])
    print(f"  Orders to pack: {len(dash['packing_queue'])}")
    print(f"  Total packing time: {total_minutes} minutes ({total_minutes/60:.1f} hours)")
    for o in dash["packing_queue"][:5]:
        print(f"    {o['order_number']}: {o.get('estimated_packing_minutes', '?')} min - Dispatch: {o.get('promised_dispatch_date', '?')}")
    if len(dash["packing_queue"]) > 5:
        print(f"    ... and {len(dash['packing_queue']) - 5} more")
else:
    print("  No orders in packing queue")
print()

# 5. Calendar warnings
print("[5/8] Checking calendar warnings...")
if dash.get("calendar_warnings"):
    for w in dash["calendar_warnings"]:
        days = w.get("days_until", "?")
        label = "TODAY!" if days == 0 else f"{days} day(s)"
        if w.get("type") == "assignment_due":
            print(f"  ASSIGNMENT DUE: {w.get('title', '?')} ({label})")
        else:
            print(f"  SHIPPING DEADLINE: {w.get('order_number', '?')} ({label})")
else:
    print("  No calendar warnings")
print()

# 6. AI Agent - Key Demo: Exam vs Packing Conflict
print("[6/8] AI AGENT: Detecting exam-vs-packing conflict...")
r = httpx.post(
    f"{BASE}/api/agent/chat",
    json={"message": "I have an exam tomorrow and orders to pack. What should I do?"},
    headers=h,
)
agent = r.json()
resp = agent.get("response", "")
mode = "deterministic"
if "Mode:" in resp:
    mode = resp.split("Mode:")[-1].strip().split("\n")[0].strip()
print(f"  Mode: {mode}")
print(f"  Session: {agent.get('session_id', '?')}")
print()
print("  Agent Response:")
print("  " + "-" * 60)
for line in resp.split("\n"):
    print(f"  {line}")
print("  " + "-" * 60)
print()
actions = agent.get("actions_taken", [])
print(f"  Actions taken: {len(actions)}")
for a in actions:
    status = "SUCCESS" if a.get("success") else "FAILED"
    print(f"    [{status}] {a['tool']}")
print()

# 7. Finance summary
print("[7/8] Finance summary...")
r = httpx.get(f"{BASE}/api/finance/summary", headers=h)
fin = r.json()
print(f"  Gross Sales: RM {fin.get('gross_sales', '0')}")
print(f"  Net Sales: RM {fin.get('net_sales', '0')}")
print(f"  Realised Profit (DELIVERED): RM {fin.get('realized_profit', '0')}")
print(f"  Estimated Profit (PAID+PACKED+DISPATCHED): RM {fin.get('estimated_profit', '0')}")
print(f"  Outstanding Payments: RM {fin.get('outstanding_payments', '0')}")
print()

# 8. Automation jobs
print("[8/8] Automation jobs...")
r = httpx.get(f"{BASE}/api/automation/", headers=h)
jobs = r.json()
active = [j for j in jobs if j.get("is_active")]
print(f"  Total jobs: {len(jobs)}")
print(f"  Active jobs: {len(active)}")
for j in jobs[:5]:
    status = "ACTIVE" if j.get("is_active") else "PAUSED"
    print(f"    [{status}] {j['name']}")
if len(jobs) > 5:
    print(f"    ... and {len(jobs) - 5} more")
print()

print("=" * 70)
print("DEMO SCENARIO COMPLETE - All systems operational")
print("=" * 70)
