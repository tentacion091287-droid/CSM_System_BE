# Low-Level Design (LLD)

## Car Rental & Service Management System — Backend

---

## 1. Directory & Module Structure

```
app/
├── core/
│   ├── config.py           Settings (Pydantic BaseSettings)
│   ├── security.py         JWT encode/decode, password hash/verify
│   ├── dependencies.py     FastAPI Depends: get_db, get_current_user, require_admin
│   └── exceptions.py       Global exception handlers (HTTP, validation, unhandled)
├── db/
│   └── session.py          Async engine, AsyncSessionLocal, Base (DeclarativeBase)
├── models/
│   ├── user.py             User, UserRole enum
│   ├── vehicle.py          Vehicle, VehicleCategory/FuelType/VehicleStatus enum
│   ├── driver.py           Driver
│   ├── booking.py          Booking, BookingStatus enum
│   ├── payment.py          Payment, PaymentMethod/PaymentStatus enum
│   ├── invoice.py          Invoice
│   ├── fine.py             Fine, FineStatus enum
│   ├── maintenance.py      Maintenance, MaintenanceType/MaintenanceStatus enum
│   ├── driver_rating.py    DriverRating
│   └── __init__.py         Re-exports all models (required by Alembic)
├── schemas/
│   ├── auth.py             RegisterRequest, LoginRequest, TokenResponse, ProfileUpdate
│   ├── user.py             UserOut, UserUpdate, PasswordChange, RoleUpdate
│   ├── vehicle.py          VehicleCreate, VehicleUpdate, VehicleOut, VehicleStatusUpdate
│   ├── driver.py           DriverCreate, DriverUpdate, DriverOut, AvailabilityUpdate
│   ├── booking.py          BookingCreate, BookingUpdate, BookingOut, AdminNotes
│   ├── payment.py          PaymentCreate, PaymentOut
│   ├── invoice.py          InvoiceOut
│   ├── fine.py             FineOut
│   ├── maintenance.py      MaintenanceCreate, MaintenanceUpdate, MaintenanceOut
│   ├── driver_rating.py    RatingCreate, RatingOut
│   └── dashboard.py        DashboardStats
├── services/
│   ├── auth_service.py
│   ├── user_service.py
│   ├── vehicle_service.py
│   ├── driver_service.py
│   ├── booking_service.py
│   ├── payment_service.py
│   ├── invoice_service.py
│   ├── fine_service.py
│   ├── maintenance_service.py
│   ├── dashboard_service.py
│   └── driver_rating_service.py
├── routers/
│   ├── auth.py
│   ├── admin.py
│   ├── vehicles.py
│   ├── drivers.py
│   ├── bookings.py
│   ├── payments.py
│   ├── invoices.py
│   ├── fines.py
│   └── maintenance.py
└── main.py
```

---

## 2. Database Schema (DDL Summary)

### 2.1 users

```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name       VARCHAR(255) NOT NULL,
    phone           VARCHAR(20),
    role            userrole NOT NULL DEFAULT 'customer',   -- ENUM: customer, admin
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    is_deleted      BOOLEAN NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_users_email ON users(email);
```

### 2.2 vehicles

```sql
CREATE TABLE vehicles (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    make          VARCHAR(100) NOT NULL,
    model         VARCHAR(100) NOT NULL,
    year          SMALLINT NOT NULL,
    license_plate VARCHAR(30) UNIQUE NOT NULL,
    category      vehiclecategory NOT NULL,   -- ENUM: economy, standard, premium, suv, van
    daily_rate    NUMERIC(10,2) NOT NULL,
    fuel_type     fueltype,                   -- ENUM: petrol, diesel, electric, hybrid
    seats         SMALLINT,
    status        vehiclestatus NOT NULL DEFAULT 'available',  -- ENUM: available, booked, maintenance
    image_url     VARCHAR(500),
    is_deleted    BOOLEAN NOT NULL DEFAULT FALSE,
    created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_vehicles_license_plate ON vehicles(license_plate);
CREATE INDEX ix_vehicles_status ON vehicles(status);
```

### 2.3 drivers

```sql
CREATE TABLE drivers (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name        VARCHAR(255) NOT NULL,
    phone            VARCHAR(20) UNIQUE NOT NULL,
    license_number   VARCHAR(50) UNIQUE NOT NULL,
    license_expiry   DATE NOT NULL,
    is_available     BOOLEAN NOT NULL DEFAULT TRUE,
    avg_rating       NUMERIC(3,2) NOT NULL DEFAULT 0.00,
    total_trips      INTEGER NOT NULL DEFAULT 0,
    is_active        BOOLEAN NOT NULL DEFAULT TRUE,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 2.4 bookings

```sql
CREATE TABLE bookings (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id      UUID NOT NULL REFERENCES users(id),
    vehicle_id       UUID NOT NULL REFERENCES vehicles(id),
    driver_id        UUID REFERENCES drivers(id),
    pickup_date      DATE NOT NULL,
    return_date      DATE NOT NULL,
    actual_return    DATE,
    pickup_location  VARCHAR(500),
    drop_location    VARCHAR(500),
    needs_driver     BOOLEAN NOT NULL DEFAULT FALSE,
    status           bookingstatus NOT NULL DEFAULT 'pending',
        -- ENUM: pending, approved, active, completed, cancelled, rejected
    estimated_cost   NUMERIC(10,2),
    admin_notes      TEXT,
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_dates CHECK (return_date > pickup_date)
);
CREATE INDEX ix_bookings_customer_id ON bookings(customer_id);
CREATE INDEX ix_bookings_vehicle_id ON bookings(vehicle_id);
CREATE INDEX ix_bookings_status ON bookings(status);
```

### 2.5 payments

```sql
CREATE TABLE payments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id      UUID UNIQUE NOT NULL REFERENCES bookings(id),
    customer_id     UUID NOT NULL REFERENCES users(id),
    amount          NUMERIC(10,2) NOT NULL,
    payment_method  paymentmethod NOT NULL DEFAULT 'card',
        -- ENUM: card, cash, upi, bank_transfer
    status          paymentstatus NOT NULL DEFAULT 'pending',
        -- ENUM: pending, processing, completed, failed, refunded
    transaction_ref VARCHAR(255) UNIQUE,
    paid_at         TIMESTAMPTZ,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 2.6 invoices

```sql
CREATE TABLE invoices (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id     UUID UNIQUE NOT NULL REFERENCES bookings(id),
    payment_id     UUID UNIQUE NOT NULL REFERENCES payments(id),
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    rental_days    SMALLINT NOT NULL,
    daily_rate     NUMERIC(10,2) NOT NULL,
    base_amount    NUMERIC(10,2) NOT NULL,
    fine_amount    NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    tax_amount     NUMERIC(10,2) NOT NULL DEFAULT 0.00,
    total_amount   NUMERIC(10,2) NOT NULL,
    issued_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 2.7 fines

```sql
CREATE TABLE fines (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    booking_id     UUID UNIQUE NOT NULL REFERENCES bookings(id),
    customer_id    UUID NOT NULL REFERENCES users(id),
    overdue_days   SMALLINT NOT NULL,
    daily_fine_rate NUMERIC(10,2) NOT NULL,
    total_amount   NUMERIC(10,2) NOT NULL,
    status         finestatus NOT NULL DEFAULT 'pending',  -- ENUM: pending, paid, waived
    paid_at        TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 2.8 maintenance_records

```sql
CREATE TABLE maintenance_records (
    id               UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    vehicle_id       UUID NOT NULL REFERENCES vehicles(id),
    maintenance_type maintenancetype,  -- ENUM: routine, repair, inspection, cleaning
    description      TEXT,
    scheduled_date   DATE NOT NULL,
    completed_date   DATE,
    cost             NUMERIC(10,2),
    performed_by     VARCHAR(255),
    status           maintenancestatus NOT NULL DEFAULT 'scheduled',
        -- ENUM: scheduled, in_progress, completed, cancelled
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### 2.9 driver_ratings

```sql
CREATE TABLE driver_ratings (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    driver_id   UUID NOT NULL REFERENCES drivers(id),
    booking_id  UUID UNIQUE NOT NULL REFERENCES bookings(id),
    customer_id UUID NOT NULL REFERENCES users(id),
    rating      SMALLINT NOT NULL,
    review      TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_rating CHECK (rating >= 1 AND rating <= 5)
);
```

---

## 3. API Endpoints Reference

### Auth (`/api/v1/auth`)

| Method | Path | Auth | Request Body / Params | Response |
|--------|------|------|----------------------|----------|
| POST | `/register` | — | `RegisterRequest` | `201 UserOut` |
| POST | `/login` | — | `LoginRequest` (form) | `200 TokenResponse` |
| POST | `/logout` | Bearer | — | `204` |
| GET | `/me` | Bearer | — | `200 UserOut` |
| PUT | `/me` | Bearer | `ProfileUpdate` | `200 UserOut` |
| PUT | `/me/password` | Bearer | `PasswordChange` | `204` |

### Admin (`/api/v1/admin`)

| Method | Path | Auth | Request Body / Params | Response |
|--------|------|------|----------------------|----------|
| GET | `/dashboard` | Admin | — | `200 DashboardStats` |
| GET | `/users` | Admin | `?page&size` | `200 Page[UserOut]` |
| GET | `/users/{user_id}` | Admin | — | `200 UserOut` |
| PATCH | `/users/{user_id}/activate` | Admin | — | `200 UserOut` |
| PATCH | `/users/{user_id}/role` | Admin | `RoleUpdate` | `200 UserOut` |

### Vehicles (`/api/v1/vehicles`)

| Method | Path | Auth | Request Body / Params | Response |
|--------|------|------|----------------------|----------|
| GET | `/` | — | `?category&date_from&date_to&page&size` | `200 Page[VehicleOut]` |
| GET | `/{vehicle_id}` | — | — | `200 VehicleOut` |
| POST | `/` | Admin | `VehicleCreate` | `201 VehicleOut` |
| PUT | `/{vehicle_id}` | Admin | `VehicleUpdate` | `200 VehicleOut` |
| PATCH | `/{vehicle_id}/status` | Admin | `VehicleStatusUpdate` | `200 VehicleOut` |
| DELETE | `/{vehicle_id}` | Admin | — | `204` |

### Drivers (`/api/v1/drivers`)

| Method | Path | Auth | Request Body / Params | Response |
|--------|------|------|----------------------|----------|
| GET | `/` | Admin | `?is_available&page&size` | `200 Page[DriverOut]` |
| GET | `/{driver_id}` | Admin | — | `200 DriverOut` |
| GET | `/{driver_id}/ratings` | Bearer | `?page&size` | `200 Page[RatingOut]` |
| POST | `/` | Admin | `DriverCreate` | `201 DriverOut` |
| PUT | `/{driver_id}` | Admin | `DriverUpdate` | `200 DriverOut` |
| PATCH | `/{driver_id}/availability` | Admin | `AvailabilityUpdate` | `200 DriverOut` |
| DELETE | `/{driver_id}` | Admin | — | `204` |
| POST | `/ratings` | Bearer | `RatingCreate` | `201 RatingOut` |

### Bookings (`/api/v1/bookings`)

| Method | Path | Auth | Request Body / Params | Response |
|--------|------|------|----------------------|----------|
| POST | `/` | Bearer | `BookingCreate` | `201 BookingOut` |
| GET | `/` | Bearer | `?page&size` | `200 Page[BookingOut]` |
| GET | `/history` | Bearer | `?page&size` | `200 Page[BookingOut]` |
| GET | `/{booking_id}` | Bearer | — | `200 BookingOut` |
| PUT | `/{booking_id}` | Bearer | `BookingUpdate` | `200 BookingOut` |
| DELETE | `/{booking_id}` | Bearer | — | `204` |
| PATCH | `/{booking_id}/approve` | Admin | `AdminNotes` | `200 BookingOut` |
| PATCH | `/{booking_id}/reject` | Admin | `AdminNotes` | `200 BookingOut` |
| PATCH | `/{booking_id}/activate` | Admin | — | `200 BookingOut` |
| PATCH | `/{booking_id}/complete` | Admin | — | `200 BookingOut` |
| PATCH | `/{booking_id}/assign-driver` | Admin | `{ driver_id }` | `200 BookingOut` |

### Payments (`/api/v1/payments`)

| Method | Path | Auth | Request Body / Params | Response |
|--------|------|------|----------------------|----------|
| POST | `/` | Bearer | `PaymentCreate` | `201 PaymentOut` |
| GET | `/` | Admin | `?page&size` | `200 Page[PaymentOut]` |
| GET | `/my` | Bearer | `?page&size` | `200 Page[PaymentOut]` |
| GET | `/{payment_id}` | Bearer | — | `200 PaymentOut` |
| PATCH | `/{payment_id}/process` | Admin | — | `200 PaymentOut` |
| PATCH | `/{payment_id}/refund` | Admin | — | `200 PaymentOut` |

### Invoices (`/api/v1/invoices`)

| Method | Path | Auth | Request Body / Params | Response |
|--------|------|------|----------------------|----------|
| GET | `/` | Admin | `?page&size` | `200 Page[InvoiceOut]` |
| GET | `/my` | Bearer | `?page&size` | `200 Page[InvoiceOut]` |
| GET | `/booking/{booking_id}` | Bearer | — | `200 InvoiceOut` |
| GET | `/{invoice_id}` | Bearer | — | `200 InvoiceOut` |

### Fines (`/api/v1/fines`)

| Method | Path | Auth | Request Body / Params | Response |
|--------|------|------|----------------------|----------|
| GET | `/` | Admin | `?page&size` | `200 Page[FineOut]` |
| GET | `/my` | Bearer | `?page&size` | `200 Page[FineOut]` |
| GET | `/booking/{booking_id}` | Bearer | — | `200 FineOut` |
| GET | `/{fine_id}` | Bearer | — | `200 FineOut` |
| PATCH | `/{fine_id}/waive` | Admin | — | `200 FineOut` |
| PATCH | `/{fine_id}/pay` | Bearer | — | `200 FineOut` |

### Maintenance (`/api/v1/maintenance`)

| Method | Path | Auth | Request Body / Params | Response |
|--------|------|------|----------------------|----------|
| GET | `/` | Admin | `?vehicle_id&status&page&size` | `200 Page[MaintenanceOut]` |
| GET | `/{record_id}` | Admin | — | `200 MaintenanceOut` |
| POST | `/` | Admin | `MaintenanceCreate` | `201 MaintenanceOut` |
| PUT | `/{record_id}` | Admin | `MaintenanceUpdate` | `200 MaintenanceOut` |
| PATCH | `/{record_id}/complete` | Admin | — | `200 MaintenanceOut` |
| PATCH | `/{record_id}/cancel` | Admin | — | `200 MaintenanceOut` |
| DELETE | `/{record_id}` | Admin | — | `204` |

---

## 4. Core Dependencies (Dependency Injection)

```python
# get_db — provides an async DB session, auto-commits/rolls back
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

# get_current_user — decodes Bearer JWT, returns User ORM object
async def get_current_user(
    token: str = Depends(HTTPBearer()),
    db: AsyncSession = Depends(get_db)
) -> User:
    ...

# require_admin — wraps get_current_user, checks role == "admin"
async def require_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.role != UserRole.admin:
        raise HTTPException(403, "Admin access required")
    return current_user
```

---

## 5. Service Layer Contracts

Each service function has a consistent signature:

```python
async def <action>(db: AsyncSession, ...) -> <ModelOrSchema>
```

Key patterns:

**Paginated list:**
```python
async def list_vehicles(
    db: AsyncSession,
    category: VehicleCategory | None,
    date_from: date | None,
    date_to: date | None,
    page: int,
    size: int
) -> tuple[list[Vehicle], int]:   # (items, total_count)
```

**Status transition (guarded):**
```python
async def approve_booking(db: AsyncSession, booking_id: UUID, admin: User) -> Booking:
    booking = await _get_or_404(db, booking_id)
    if booking.status != BookingStatus.pending:
        raise HTTPException(400, "Booking is not in pending state")
    booking.status = BookingStatus.approved
    await db.commit()
    return booking
```

**Auto-invoice on payment completion:**
```python
async def process_payment(db: AsyncSession, payment_id: UUID) -> Payment:
    payment.status = PaymentStatus.completed
    payment.paid_at = datetime.now(tz=timezone.utc)
    await db.flush()
    await invoice_service.create_for_payment(db, payment)
    await db.commit()
    return payment
```

---

## 6. Security Implementation

### JWT

```python
# Encoding (login)
def create_access_token(data: dict) -> str:
    payload = data | {"exp": datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# Decoding (every protected request)
def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    # Raises JWTError on expiry or invalid signature
```

### Password Hashing

```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(plain: str) -> str:
    return pwd_context.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)
```

---

## 7. Invoice Calculation Logic

```
rental_days  = (actual_return or return_date) - pickup_date   [days]
base_amount  = rental_days × vehicle.daily_rate
fine_amount  = fine.total_amount  (if fine exists, else 0)
tax_amount   = (base_amount + fine_amount) × TAX_RATE         (default 18%)
total_amount = base_amount + fine_amount + tax_amount

invoice_number = "INV-" + YYYYMMDD + "-" + 6-char-UUID-fragment
```

---

## 8. Fine Calculation Logic

Triggered when `PATCH /bookings/{id}/complete` is called and `actual_return > return_date`:

```
overdue_days    = actual_return - return_date   [days]
daily_fine_rate = settings.DAILY_FINE_RATE      (default ₹500/day)
total_amount    = overdue_days × daily_fine_rate
```

Fine record is created with `status = "pending"`. Customer pays via `PATCH /fines/{id}/pay`.

---

## 9. ORM Model Design Patterns

**Timestamp mixin (applied to all models):**
```python
created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
updated_at = Column(DateTime(timezone=True), server_default=func.now(),
                    onupdate=func.now(), nullable=False)
```

**Relationship loading strategy:**
```python
# All relationships use lazy="raise" to surface accidental N+1 patterns
vehicle: Mapped[Vehicle] = relationship("Vehicle", lazy="raise")

# Explicit eager loading in service queries
stmt = select(Booking).options(selectinload(Booking.vehicle))
```

**Soft delete:**
```python
# User deactivation (admin toggle)
user.is_active = False

# Vehicle soft delete
vehicle.is_deleted = True

# All list queries filter: .where(Vehicle.is_deleted == False)
```

---

## 10. Error Response Format

All errors follow FastAPI's default structure via the global exception handlers:

```json
{
    "detail": "Human-readable error message"
}
```

**Common HTTP status codes:**

| Code | Scenario |
|------|---------|
| 400 | Bad request (invalid state transition, business rule violation) |
| 401 | Missing or invalid JWT |
| 403 | Authenticated but insufficient role |
| 404 | Resource not found |
| 409 | Conflict (duplicate email, license plate, etc.) |
| 422 | Pydantic validation failure |
| 500 | Unhandled server error |
