from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException
from app.core.config import settings
from app.core.exceptions import (
    http_exception_handler,
    validation_exception_handler,
    unhandled_exception_handler,
)
from app.db.session import engine, Base
from app.routers import auth, admin, vehicles, drivers, bookings, payments, invoices, fines, maintenance


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await engine.dispose()


app = FastAPI(
    title="Car Rental & Service Management System",
    version="1.0.0",
    description=(
        "REST API for managing car rentals, drivers, bookings, payments, invoices, "
        "fines, maintenance records, and driver ratings."
    ),
    lifespan=lifespan,
    openapi_tags=[
        {"name": "auth", "description": "Registration, login, profile management"},
        {"name": "admin", "description": "Admin-only: dashboard, user management"},
        {"name": "vehicles", "description": "Vehicle CRUD and availability"},
        {"name": "drivers", "description": "Driver management and ratings"},
        {"name": "bookings", "description": "Booking lifecycle management"},
        {"name": "payments", "description": "Payment initiation and processing"},
        {"name": "invoices", "description": "Auto-generated invoices"},
        {"name": "fines", "description": "Late-return fine management"},
        {"name": "maintenance", "description": "Vehicle maintenance scheduling"},
        {"name": "health", "description": "Service health check"},
    ],
)

app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(vehicles.router, prefix="/api/v1")
app.include_router(drivers.router, prefix="/api/v1")
app.include_router(bookings.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(invoices.router, prefix="/api/v1")
app.include_router(fines.router, prefix="/api/v1")
app.include_router(maintenance.router, prefix="/api/v1")


@app.get("/api/v1/health", tags=["health"])
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
