# High-Level Design (HLD)

## Car Rental & Service Management System — Backend

---

## 1. System Overview

CSM System is a multi-tenant REST API that manages the complete lifecycle of a car rental business — from vehicle browsing and booking through payment, invoice generation, fine assessment, driver management, and fleet maintenance. Two roles interact with the system: **customers** (self-service) and **admins** (full operational control).

---

## 2. Architecture Style

**Layered Monolith with Async I/O**

```
┌──────────────────────────────────────────┐
│              Client (Browser / Mobile)   │
└─────────────────────┬────────────────────┘
                      │ HTTPS / REST
┌─────────────────────▼────────────────────┐
│         Render.com (Web Service)          │
│   ┌──────────────────────────────────┐   │
│   │        Uvicorn ASGI Server       │   │
│   │   ┌──────────────────────────┐   │   │
│   │   │      FastAPI App          │   │   │
│   │   │  ┌────────────────────┐  │   │   │
│   │   │  │  Routers / Routes  │  │   │   │
│   │   │  ├────────────────────┤  │   │   │
│   │   │  │   Service Layer    │  │   │   │
│   │   │  ├────────────────────┤  │   │   │
│   │   │  │  SQLAlchemy ORM    │  │   │   │
│   │   │  └────────────────────┘  │   │   │
│   │   └──────────────────────────┘   │   │
│   └──────────────────────────────────┘   │
└─────────────────────┬────────────────────┘
                      │ asyncpg / TCP
┌─────────────────────▼────────────────────┐
│          Supabase (PostgreSQL)            │
│   PgBouncer (port 6543, transaction mode) │
│   PostgreSQL 15 (port 5432)               │
└──────────────────────────────────────────┘
```

---

## 3. Component Breakdown

### 3.1 API Layer (FastAPI + Uvicorn)

The application is an ASGI app served by Uvicorn. FastAPI handles routing, request parsing, response serialization, and OpenAPI documentation generation. All I/O is non-blocking (async/await throughout).

**Routers registered at startup (`app/main.py`):**

| Router | Prefix | Visibility |
|--------|--------|-----------|
| auth | `/api/v1/auth` | Public + Authenticated |
| admin | `/api/v1/admin` | Admin only |
| vehicles | `/api/v1/vehicles` | Public + Admin |
| drivers | `/api/v1/drivers` | Admin + Authenticated |
| bookings | `/api/v1/bookings` | Authenticated + Admin |
| payments | `/api/v1/payments` | Authenticated + Admin |
| invoices | `/api/v1/invoices` | Authenticated + Admin |
| fines | `/api/v1/fines` | Authenticated + Admin |
| maintenance | `/api/v1/maintenance` | Admin only |

### 3.2 Service Layer

Each domain has a dedicated service module in `app/services/`. Services receive an `AsyncSession` via dependency injection and contain all business logic — no SQLAlchemy queries appear in routers.

Services:
- `auth_service` — registration, login, token management
- `user_service` — profile updates, admin user management
- `vehicle_service` — CRUD, availability filtering, status transitions
- `driver_service` — CRUD, availability toggle, rating aggregation
- `booking_service` — booking lifecycle state machine
- `payment_service` — payment initiation, processing, refunds
- `invoice_service` — auto-generation on payment completion
- `fine_service` — overdue detection, waiver/payment
- `maintenance_service` — scheduling, completion, cancellation
- `dashboard_service` — aggregated statistics for admin dashboard
- `driver_rating_service` — rating submission, average recalculation

### 3.3 Data Layer (SQLAlchemy + asyncpg)

**Engine Configuration:**

```
NullPool  ←  disables app-side pooling so PgBouncer owns connections
prepared_statement_name_func = lambda: f"__asyncpg_{uuid4()}__"
  ← UUID names prevent DuplicatePreparedStatementError when PgBouncer
     recycles server connections (transaction-mode limitation)
statement_cache_size = 0  ← disables asyncpg's own statement cache
```

This configuration is mandatory for **PgBouncer transaction-mode** (Supabase port 6543). Without it, SQLAlchemy's asyncpg dialect generates sequential named prepared statements (`__asyncpg_stmt_0__`, `__asyncpg_stmt_1__`, …) that collide when PgBouncer gives a recycled backend connection to a new request.

### 3.4 Database (PostgreSQL via Supabase)

- Hosted on Supabase (AWS ap-northeast-2)
- Accessed through PgBouncer transaction-mode pooler on port 6543
- Schema managed entirely via Alembic migrations
- 9 tables, 8 enum types

### 3.5 Migrations (Alembic)

Alembic uses a **synchronous** psycopg2 connection (never asyncpg) to avoid prepared-statement issues during migration runs. The `_sync_url()` function in `alembic/env.py` rewrites the asyncpg URL (`postgresql+asyncpg://...?ssl=require`) to a psycopg2 URL (`postgresql://...?sslmode=require`).

---

## 4. Data Model Overview

```
users ──────────────────────────────────────────────┐
  │                                                  │
  │ (customer_id FK)                                 │
  ▼                                                  │
bookings ──── vehicles                              │
  │    │          │                                  │
  │    │ (driver) │ (maintenance)                    │
  │    ▼          ▼                                  │
  │   drivers   maintenance_records                  │
  │    │                                             │
  │    └─── driver_ratings ◄──────────────────── (customer_id FK)
  │                                                  │
  ├─── payments ─── invoices                         │
  │                                                  │
  └─── fines ◄────────────────────────────────────── ┘
```

| Entity | Cardinality |
|--------|------------|
| User → Bookings | 1 : N |
| Vehicle → Bookings | 1 : N |
| Booking → Payment | 1 : 1 |
| Booking → Invoice | 1 : 1 |
| Booking → Fine | 1 : 0..1 |
| Driver → Bookings | 1 : N |
| Driver → DriverRatings | 1 : N |
| Vehicle → MaintenanceRecords | 1 : N |

---

## 5. Authentication & Authorization

```
Client                    FastAPI
  │                          │
  ├─ POST /auth/login ───────►│
  │                          │ verify password (bcrypt)
  │◄── { access_token } ─────┤ sign JWT (HS256, 60 min TTL)
  │                          │
  ├─ GET /bookings/ ─────────►│
  │  Authorization: Bearer   │ decode JWT → user_id + role
  │                          │ role == "admin" → require_admin()
  │◄── 200 / 401 / 403 ──────┤
```

**Dependencies (app/core/dependencies.py):**
- `get_db` — yields `AsyncSession`
- `get_current_user` — decodes JWT, fetches user from DB, raises 401 if invalid
- `require_admin` — wraps `get_current_user`, raises 403 if role ≠ admin

---

## 6. Booking Lifecycle (State Machine)

```
          ┌──────────┐
          │ PENDING  │◄─── POST /bookings/
          └────┬─────┘
               │ PATCH /bookings/{id}/approve
               ▼
          ┌──────────┐
          │ APPROVED │
          └────┬─────┘
               │ PATCH /bookings/{id}/activate
               ▼
          ┌──────────┐
          │  ACTIVE  │
          └────┬─────┘
               │ PATCH /bookings/{id}/complete
               ▼
          ┌──────────────┐
          │  COMPLETED   │──► auto-generate Invoice
          └──────────────┘    auto-assess Fine (if overdue)

  From PENDING/APPROVED:
     PATCH /reject  → REJECTED
     DELETE         → CANCELLED (customer action)
```

---

## 7. Payment → Invoice Flow

```
POST /payments/            ← customer initiates payment
       │
       ▼
Payment.status = pending
       │
PATCH /payments/{id}/process  ← admin confirms
       │
       ▼
Payment.status = completed
Invoice auto-created:
  base_amount  = rental_days × daily_rate
  fine_amount  = overdue_days × DAILY_FINE_RATE (if fine exists)
  tax_amount   = (base + fine) × TAX_RATE
  total_amount = base + fine + tax
```

---

## 8. Deployment Architecture

```
GitHub (main branch)
       │
       │ push / PR merge
       ▼
Render CI/CD
  ├─ pip install -r requirements.txt
  ├─ alembic upgrade head          ← migrations run before start
  └─ ./start.sh → uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

**Render service type:** Web Service (auto-scaled, sleeps on free tier)  
**Region:** Configurable (follow Supabase region for latency)

---

## 9. Non-Functional Characteristics

| Concern | Approach |
|---------|----------|
| Scalability | Stateless app → horizontal scaling on Render |
| Reliability | NullPool prevents stale connections; Render restarts on crash |
| Security | JWT HS256, bcrypt passwords, CORS allowlist, no SQL injection (ORM) |
| Observability | FastAPI exception handlers log unhandled errors; Uvicorn access logs |
| Data integrity | DB-level constraints, Alembic migrations, soft deletes |
| Performance | Async I/O, indexed email/license_plate/status columns |
