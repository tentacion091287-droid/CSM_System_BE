# CSM System — Backend

Car Rental & Service Management System — REST API built with FastAPI and PostgreSQL.

## Overview

CSM System is a full-featured backend for managing car rental operations. It handles vehicle inventory, customer bookings, driver assignment, payments, invoices, late-return fines, vehicle maintenance, and driver ratings. Both customers and admins interact through a single JWT-secured API.

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Framework | FastAPI 0.115 |
| Language | Python 3.11 |
| Database | PostgreSQL (Supabase hosted) |
| ORM | SQLAlchemy 2.0 (async) |
| Driver | asyncpg + psycopg2 (migrations) |
| Migrations | Alembic |
| Auth | JWT (python-jose) + bcrypt |
| Validation | Pydantic v2 |
| Server | Uvicorn (ASGI) |
| Deployment | Render.com |

## Project Structure

```
CSM_System_BE/
├── app/
│   ├── core/           # Config, security, dependencies, exception handlers
│   ├── db/             # Async engine & session factory
│   ├── models/         # SQLAlchemy ORM models
│   ├── schemas/        # Pydantic request/response schemas
│   ├── services/       # Business logic (no HTTP coupling)
│   ├── routers/        # FastAPI route handlers
│   ├── tests/          # Test suite
│   └── main.py         # App factory & lifespan
├── alembic/            # Database migrations
├── scripts/            # Seed data scripts
└── docs/               # Architecture documentation
    ├── HLD.md          # High-Level Design
    ├── LLD.md          # Low-Level Design
    └── CFD.md          # Context Flow Diagrams (user & admin)
```

## API Base URL

```
https://<your-render-app>.onrender.com/api/v1
```

Local: `http://localhost:8000/api/v1`

Interactive docs: `GET /docs` (Swagger UI), `GET /redoc` (ReDoc)

## Modules

| Module | Prefix | Description |
|--------|--------|-------------|
| Auth | `/auth` | Register, login, profile management |
| Admin | `/admin` | Dashboard, user management |
| Vehicles | `/vehicles` | Fleet inventory management |
| Drivers | `/drivers` | Driver management & ratings |
| Bookings | `/bookings` | Rental booking lifecycle |
| Payments | `/payments` | Payment processing |
| Invoices | `/invoices` | Auto-generated invoices |
| Fines | `/fines` | Late-return penalty management |
| Maintenance | `/maintenance` | Vehicle maintenance scheduling |

## Quick Start

### Prerequisites

- Python 3.11
- PostgreSQL 14+ (or Supabase project)

### Local Setup

```bash
# Clone the repo
git clone <repo-url>
cd CSM_System_BE

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate       # Linux/macOS
# venv\Scripts\activate        # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment template and fill in values
cp .env.example .env
# Edit .env — set DATABASE_URL, SECRET_KEY, etc.

# Run database migrations
alembic upgrade head

# (Optional) Seed sample data
python -m scripts.seed_vehicles
python -m scripts.seed_all

# Start the development server
uvicorn app.main:app --reload
```

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL async connection string (`postgresql+asyncpg://...`) |
| `SECRET_KEY` | Yes | Random 64-hex-char string for JWT signing |
| `ALGORITHM` | No | JWT algorithm — default `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | No | Token TTL — default `60` |
| `DAILY_FINE_RATE` | No | Late-return fine per day — default `500.0` |
| `TAX_RATE` | No | Tax applied to invoices — default `0.18` (18%) |
| `ALLOWED_ORIGINS` | No | CORS origins — default `*` |

### Running Tests

```bash
pip install -r requirements-dev.txt
pytest app/tests/ -v
```

## Authentication

All protected endpoints require a Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

Obtain a token via `POST /api/v1/auth/login`.

### Roles

| Role | Access |
|------|--------|
| `customer` | Self-service: book vehicles, make payments, view own records |
| `admin` | Full access: all customer actions + fleet/driver/user management |

## Key Design Decisions

- **NullPool + UUID prepared statements** — Required for PgBouncer transaction-mode pooling (Supabase port 6543). See [HLD](docs/HLD.md) for details.
- **Async-first** — All DB operations use SQLAlchemy async session; no blocking I/O in the request path.
- **Service layer** — Business logic lives in `app/services/`, completely decoupled from HTTP concerns.
- **Soft deletes** — Users and vehicles use `is_deleted`/`is_active` flags instead of hard deletes.
- **Lazy="raise"** — ORM relationships use `lazy="raise"` to surface accidental N+1 query patterns at dev time.

## Deployment (Render)

The app is configured for [Render.com](https://render.com) via `render.yaml`:

- **Build command:** `pip install -r requirements.txt && alembic upgrade head`
- **Start command:** `./start.sh` (runs `uvicorn app.main:app`)
- **Environment:** Python 3.11, all secrets set as Render env vars

## Documentation

- [HLD — High-Level Design](docs/HLD.md)
- [LLD — Low-Level Design](docs/LLD.md)
- [CFD — Context Flow Diagrams](docs/CFD.md)
