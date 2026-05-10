import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, field_validator, model_validator
from app.models.booking import BookingStatus


class BookingCreate(BaseModel):
    vehicle_id: uuid.UUID
    pickup_date: date
    return_date: date
    pickup_location: str | None = None
    drop_location: str | None = None
    needs_driver: bool = False

    @model_validator(mode="after")
    def return_after_pickup(self):
        if self.return_date <= self.pickup_date:
            raise ValueError("return_date must be after pickup_date")
        return self


class BookingUpdate(BaseModel):
    pickup_date: date | None = None
    return_date: date | None = None
    pickup_location: str | None = None
    drop_location: str | None = None
    needs_driver: bool | None = None


class BookingReject(BaseModel):
    admin_notes: str | None = None


class BookingComplete(BaseModel):
    actual_return: date


class AssignDriverRequest(BaseModel):
    driver_id: uuid.UUID


class BookingResponse(BaseModel):
    id: uuid.UUID
    customer_id: uuid.UUID
    vehicle_id: uuid.UUID
    driver_id: uuid.UUID | None
    pickup_date: date
    return_date: date
    actual_return: date | None
    pickup_location: str | None
    drop_location: str | None
    needs_driver: bool
    status: BookingStatus
    estimated_cost: Decimal | None
    admin_notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedBookings(BaseModel):
    items: list[BookingResponse]
    total: int
    page: int
    size: int
    pages: int
