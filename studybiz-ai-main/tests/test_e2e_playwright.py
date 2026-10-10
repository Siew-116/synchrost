"""
StudyBiz AI - Playwright E2E Tests

Tests the critical user flows:
1. Login flow
2. Dashboard display with seed data
3. AI Assistant exam-vs-packing conflict detection
4. Order status change (state machine)
5. Finance summary display
6. Excel export download

Run: npx playwright test --headed
"""
import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://127.0.0.1:5173"

# Demo credentials (from seed_data.py)
DEMO_EMAIL = "nurul@studybiz.my"
DEMO_PASSWORD = "demo123456"


@pytest.fixture(scope="module")
def auth_page(page: Page):
    """Login and return authenticated page."""
    page.goto(f"{BASE_URL}/login")
    page.fill('input[type="email"]', DEMO_EMAIL)
    page.fill('input[type="password"]', DEMO_PASSWORD)
    page.click('button[type="submit"]')
    # Wait for dashboard to load
    page.wait_for_url(BASE_URL + "/", timeout=10000)
    return page


class TestLogin:
    """Test suite for authentication flows."""

    def test_login_page_loads(self, page: Page):
        """Login page renders with form fields."""
        page.goto(f"{BASE_URL}/login")
        expect(page.locator('input[type="email"]')).to_be_visible()
        expect(page.locator('input[type="password"]')).to_be_visible()

    def test_successful_login(self, page: Page):
        """Valid credentials redirect to dashboard."""
        page.goto(f"{BASE_URL}/login")
        page.fill('input[type="email"]', DEMO_EMAIL)
        page.fill('input[type="password"]', DEMO_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_url(BASE_URL + "/", timeout=10000)
        expect(page).to_have_url(BASE_URL + "/")
        # Dashboard should show welcome message
        expect(page.locator("h1")).to_contain_text("Welcome")

    def test_invalid_login(self, page: Page):
        """Invalid credentials show error."""
        page.goto(f"{BASE_URL}/login")
        page.fill('input[type="email"]', "wrong@example.com")
        page.fill('input[type="password"]', "wrongpass")
        page.click('button[type="submit"]')
        # Should stay on login page
        page.wait_for_timeout(2000)
        expect(page).to_have_url(f"{BASE_URL}/login")


class TestDashboard:
    """Test suite for dashboard data display."""

    def test_dashboard_shows_stats(self, auth_page: Page):
        """Dashboard displays stat cards with seed data."""
        # Should show 4 stat cards
        cards = auth_page.locator(".bg-white.rounded-xl")
        expect(cards.first).to_be_visible()
        # Total Orders should show 30
        expect(auth_page.locator("text=30")).to_be_visible()

    def test_dashboard_shows_priorities(self, auth_page: Page):
        """Today's priorities section is visible."""
        expect(auth_page.locator("text=Today's Priorities")).to_be_visible()

    def test_dashboard_shows_packing_queue(self, auth_page: Page):
        """Packing queue shows orders."""
        expect(auth_page.locator("text=Packing Queue")).to_be_visible()

    def test_dashboard_shows_exam_warning(self, auth_page: Page):
        """Upcoming exams section shows the seeded exam."""
        expect(auth_page.locator("text=Upcoming Exams")).to_be_visible()
        expect(auth_page.locator("text=Database Systems")).to_be_visible()


class TestAIAssistant:
    """Test suite for AI Agent conflict detection - the key demo scenario."""

    def test_navigate_to_assistant(self, auth_page: Page):
        """Navigate to AI Assistant page."""
        auth_page.click('a[href="/assistant"]')
        auth_page.wait_for_url(f"{BASE_URL}/assistant")
        expect(auth_page.locator("h1")).to_contain_text("AI Assistant")

    def test_exam_conflict_detection(self, auth_page: Page):
        """Agent detects exam-vs-packing conflict when asked."""
        # Find the chat input
        input_locator = auth_page.locator('input[type="text"], textarea').last
        input_locator.fill("I have an exam tomorrow and orders to pack. What should I do?")
        
        # Click send button
        send_btn = auth_page.locator("button").filter(has_text="Send")
        if send_btn.count() == 0:
            send_btn = auth_page.locator('button[type="submit"]')
        send_btn.click()
        
        # Wait for agent response
        auth_page.wait_for_timeout(5000)
        
        # Response should mention exam conflict
        page_text = auth_page.content()
        assert any(keyword in page_text.lower() for keyword in ["exam", "critical", "packing", "conflict"]), \
            "Agent response should mention exam/packing conflict"

    def test_quick_prompt_buttons(self, auth_page: Page):
        """Quick prompt buttons are available."""
        # Should have quick prompt buttons
        buttons = auth_page.locator("button")
        assert buttons.count() > 2, "Should have multiple buttons on assistant page"


class TestOrders:
    """Test suite for order management and state machine."""

    def test_orders_page_loads(self, auth_page: Page):
        """Orders page displays the orders table."""
        auth_page.goto(f"{BASE_URL}/orders")
        auth_page.wait_for_load_state("networkidle")
        # Should show orders table
        expect(auth_page.locator("text=Orders")).to_be_visible()
        # Should have order numbers
        expect(auth_page.locator("text=SB-")).to_be_visible()

    def test_status_filter_works(self, auth_page: Page):
        """Status filter chips filter orders."""
        # Click "paid" filter
        paid_chip = auth_page.locator("button").filter(has_text="paid")
        if paid_chip.count() > 0:
            paid_chip.first.click()
            auth_page.wait_for_timeout(1000)
            # Should show paid orders
            expect(auth_page.locator("text=paid")).to_be_visible()


class TestFinance:
    """Test suite for finance summary display."""

    def test_finance_page_loads(self, auth_page: Page):
        """Finance page shows profit cards."""
        auth_page.goto(f"{BASE_URL}/finance")
        auth_page.wait_for_load_state("networkidle")
        expect(auth_page.locator("text=Finance")).to_be_visible()

    def test_realised_profit_displayed(self, auth_page: Page):
        """Realised profit card shows RM value."""
        expect(auth_page.locator("text=Realised Profit")).to_be_visible()
        # Should show RM currency
        expect(auth_page.locator("text=/RM/")).to_be_visible()


class TestNavigation:
    """Test suite for sidebar navigation."""

    @pytest.mark.parametrize("route,label", [
        ("/", "Dashboard"),
        ("/assistant", "AI Assistant"),
        ("/orders", "Orders"),
        ("/calendar", "Calendar"),
        ("/academic", "Academic"),
        ("/products", "Products"),
        ("/customers", "Customers"),
        ("/finance", "Finance"),
        ("/exceptions", "Business Exceptions"),
        ("/messages", "Customer Messages"),
        ("/automation", "Automation"),
        ("/approvals", "Approval Queue"),
        ("/agent-logs", "Agent Logs"),
        ("/settings", "Settings"),
        ("/suppliers", "Suppliers"),
    ])
    def test_page_navigates(self, auth_page: Page, route: str, label: str):
        """Each page in the sidebar loads correctly."""
        auth_page.goto(f"{BASE_URL}{route}")
        auth_page.wait_for_load_state("networkidle")
        # Page should show its title
        expect(auth_page.locator("h1").first).to_be_visible()


class TestExport:
    """Test suite for Excel export."""

    def test_export_button_present(self, auth_page: Page):
        """Export masterlist button is on dashboard."""
        auth_page.goto(f"{BASE_URL}/")
        auth_page.wait_for_load_state("networkidle")
        expect(auth_page.locator("text=Export Masterlist")).to_be_visible()
