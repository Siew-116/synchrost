"""Pytest fixtures for StudyBiz AI backend tests.

Uses an in-memory SQLite database that is recreated for each test function,
ensuring full isolation between tests.
"""
import sys
import os
from datetime import datetime, timedelta

# Ensure backend root is on sys.path so `app` package resolves
backend_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_root not in sys.path:
    sys.path.insert(0, backend_root)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app import config as config_module


# ---------------------------------------------------------------------------
# Test database setup
# ---------------------------------------------------------------------------

# Use a single in-memory connection shared across the StaticPool so that
# all sessions in the same test see the same data.
_TEST_ENGINE = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@event.listens_for(_TEST_ENGINE, "connect")
def _fk_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_TEST_ENGINE)


def _override_get_db():
    """Drop-in replacement for the `get_db` dependency that uses the test engine."""
    db = _TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function", autouse=True)
def _setup_database():
    """Create all tables before each test and drop them after."""
    Base.metadata.create_all(bind=_TEST_ENGINE)
    yield
    Base.metadata.drop_all(bind=_TEST_ENGINE)


# Override the database dependency globally for all tests
app.dependency_overrides[get_db] = _override_get_db


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def client():
    """FastAPI TestClient backed by the in-memory test database."""
    return TestClient(app)


@pytest.fixture(scope="function")
def auth_token(client):
    """Register a test user and return the JWT access token."""
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "testuser@studybiz.com",
            "full_name": "Test User",
            "password": "supersecret",
            "business_name": "StudyBiz Test Shop",
            "preferred_language": "en",
        },
    )
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    return token


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    """Authorization headers for an authenticated client."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
def second_user_token(client):
    """Register a second user for ownership-isolation tests."""
    resp = client.post(
        "/api/auth/register",
        json={
            "email": "other@studybiz.com",
            "full_name": "Other User",
            "password": "supersecret",
            "preferred_language": "en",
        },
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


@pytest.fixture(scope="function")
def sample_products(client, auth_headers):
    """Create three products via the API and return their JSON."""
    products = []
    for name, price, cost, stock in [
        ("Sticky Notes 100pk", "5.00", "2.50", 20),
        ("Highlighter Set", "12.00", "6.00", 15),
        ("Exam Notebook A5", "8.50", "3.00", 3),  # low-stock
    ]:
        resp = client.post(
            "/api/products/",
            json={
                "name": name,
                "sku": f"SKU-{name[:4].upper()}",
                "selling_price": price,
                "cost_price": cost,
                "available_stock": stock,
                "low_stock_threshold": 5,
                "is_active": True,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        products.append(resp.json())
    return products


@pytest.fixture(scope="function")
def sample_customers(client, auth_headers):
    """Create three customers via the API."""
    customers = []
    for name in ["Alice", "Bob", "Carol"]:
        resp = client.post(
            "/api/customers/",
            json={
                "name": name,
                "whatsapp_number": "+60123456789",
                "address": f"Room {len(customers)+1}, College Block A",
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200, resp.text
        customers.append(resp.json())
    return customers


@pytest.fixture(scope="function")
def sample_order(client, auth_headers, sample_products, sample_customers):
    """Create a single order in PENDING status."""
    resp = client.post(
        "/api/orders/",
        json={
            "customer_id": sample_customers[0]["id"],
            "order_items": [
                {"product_id": sample_products[0]["id"], "quantity": 2},
                {"product_id": sample_products[1]["id"], "quantity": 1},
            ],
        },
        headers=auth_headers,
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture(scope="function")
def sample_data(sample_products, sample_customers, sample_order):
    """Convenience fixture that returns a dict with all sample data."""
    return {
        "products": sample_products,
        "customers": sample_customers,
        "order": sample_order,
    }
