"""
Test fixtures.

Runs against csm_db directly. Each test truncates all tables with CASCADE to
start from a clean state.  Uses a small connection pool (pool_size=2) so
connections are reclaimed quickly between tests.
"""

import pytest_asyncio
from datetime import date, timedelta
from decimal import Decimal

from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import settings
from app.core.dependencies import get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.booking import Booking, BookingStatus
from app.models.driver import Driver
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle, VehicleCategory, VehicleStatus

# NullPool: no connection caching — each operation gets a fresh connection.
# This is essential for async tests because asyncpg connections are bound to
# the event loop that created them; with function-scoped loops (pytest-asyncio
# default), a pooled connection from test N cannot be used by test N+1.
_test_engine = create_async_engine(
    settings.DATABASE_URL, echo=False, future=True, poolclass=NullPool
)
TestSession = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)

_TABLES = [
    "driver_ratings", "invoices", "fines", "payments",
    "maintenance_records", "bookings", "vehicles", "drivers", "users",
]


@pytest_asyncio.fixture(autouse=True)
async def clean_db():
    async with _test_engine.begin() as conn:
        await conn.execute(text(f"TRUNCATE TABLE {', '.join(_TABLES)} CASCADE"))


async def _override_get_db():
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def db():
    async with TestSession() as session:
        yield session


@pytest_asyncio.fixture
async def client():
    app.dependency_overrides[get_db] = _override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ── User helpers ───────────────────────────────────────────────────────────────

async def _make_user(
    db: AsyncSession, email: str, password: str, role: UserRole, name: str
) -> User:
    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=name,
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@pytest_asyncio.fixture
async def admin_user(db):
    return await _make_user(db, "admin@test.com", "Admin@123", UserRole.admin, "Test Admin")


@pytest_asyncio.fixture
async def customer_user(db):
    return await _make_user(
        db, "customer@test.com", "Cust@123", UserRole.customer, "Test Customer"
    )


@pytest_asyncio.fixture
async def admin_headers(admin_user):
    return {"Authorization": f"Bearer {create_access_token(str(admin_user.id))}"}


@pytest_asyncio.fixture
async def customer_headers(customer_user):
    return {"Authorization": f"Bearer {create_access_token(str(customer_user.id))}"}


# ── Domain object helpers ──────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def vehicle(db):
    v = Vehicle(
        make="Toyota",
        model="Camry",
        year=2022,
        license_plate="TEST-001",
        category=VehicleCategory.standard,
        daily_rate=Decimal("1000.00"),
        status=VehicleStatus.available,
    )
    db.add(v)
    await db.commit()
    await db.refresh(v)
    return v


@pytest_asyncio.fixture
async def driver(db):
    d = Driver(
        full_name="Test Driver",
        phone="9999999999",
        license_number="DL-TEST-001",
        license_expiry=date.today() + timedelta(days=365),
    )
    db.add(d)
    await db.commit()
    await db.refresh(d)
    return d


@pytest_asyncio.fixture
async def approved_booking(db, customer_user, vehicle):
    b = Booking(
        customer_id=customer_user.id,
        vehicle_id=vehicle.id,
        pickup_date=date.today() + timedelta(days=1),
        return_date=date.today() + timedelta(days=4),
        status=BookingStatus.approved,
        estimated_cost=Decimal("3000.00"),
    )
    db.add(b)
    await db.commit()
    await db.refresh(b)
    return b


@pytest_asyncio.fixture
async def completed_booking_with_driver(db, customer_user, vehicle, driver):
    b = Booking(
        customer_id=customer_user.id,
        vehicle_id=vehicle.id,
        driver_id=driver.id,
        pickup_date=date.today() - timedelta(days=5),
        return_date=date.today() - timedelta(days=2),
        actual_return=date.today() - timedelta(days=2),
        status=BookingStatus.completed,
        estimated_cost=Decimal("3000.00"),
    )
    db.add(b)
    await db.commit()
    await db.refresh(b)
    return b
