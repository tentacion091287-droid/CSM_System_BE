import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, Field


class DriverCreate(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    phone: str = Field(min_length=1, max_length=20)
    license_number: str = Field(min_length=1, max_length=50)
    license_expiry: date


class DriverUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=255)
    phone: str | None = Field(None, min_length=1, max_length=20)
    license_number: str | None = Field(None, min_length=1, max_length=50)
    license_expiry: date | None = None


class DriverAvailabilityUpdate(BaseModel):
    is_available: bool


class DriverResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    phone: str
    license_number: str
    license_expiry: date
    is_available: bool
    avg_rating: Decimal
    total_trips: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedDrivers(BaseModel):
    items: list[DriverResponse]
    total: int
    page: int
    size: int
    pages: int
