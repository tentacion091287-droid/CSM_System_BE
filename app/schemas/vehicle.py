import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, computed_field
from app.models.vehicle import VehicleCategory, FuelType, VehicleStatus


class VehicleCreate(BaseModel):
    make: str = Field(min_length=1, max_length=100)
    model: str = Field(min_length=1, max_length=100)
    year: int = Field(ge=1900, le=2100)
    license_plate: str = Field(min_length=1, max_length=30)
    category: VehicleCategory
    daily_rate: Decimal = Field(gt=0)
    fuel_type: FuelType | None = None
    seats: int | None = Field(None, ge=1, le=50)
    image_url: str | None = None


class VehicleUpdate(BaseModel):
    make: str | None = Field(None, min_length=1, max_length=100)
    model: str | None = Field(None, min_length=1, max_length=100)
    year: int | None = Field(None, ge=1900, le=2100)
    license_plate: str | None = Field(None, min_length=1, max_length=30)
    category: VehicleCategory | None = None
    daily_rate: Decimal | None = Field(None, gt=0)
    fuel_type: FuelType | None = None
    seats: int | None = Field(None, ge=1, le=50)
    image_url: str | None = None


class VehicleStatusUpdate(BaseModel):
    status: VehicleStatus


class VehicleResponse(BaseModel):
    id: uuid.UUID
    make: str
    model: str
    year: int
    license_plate: str
    category: VehicleCategory
    daily_rate: Decimal
    fuel_type: FuelType | None
    seats: int | None
    status: VehicleStatus
    image_url: str | None
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def price_per_day(self) -> Decimal:
        return self.daily_rate

    model_config = {"from_attributes": True}


class PaginatedVehicles(BaseModel):
    items: list[VehicleResponse]
    total: int
    page: int
    size: int
    pages: int
