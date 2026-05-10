import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, computed_field
from app.models.payment import PaymentMethod, PaymentStatus


class _VehicleRef(BaseModel):
    make: str
    model: str
    model_config = {"from_attributes": True}


class _BookingRef(BaseModel):
    id: uuid.UUID
    vehicle: _VehicleRef | None = None
    model_config = {"from_attributes": True}


class _CustomerRef(BaseModel):
    id: uuid.UUID
    full_name: str

    @computed_field
    @property
    def name(self) -> str:
        return self.full_name

    model_config = {"from_attributes": True}


class PaymentCreate(BaseModel):
    booking_id: uuid.UUID
    payment_method: PaymentMethod = PaymentMethod.card


class PaymentResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    customer_id: uuid.UUID
    amount: Decimal
    payment_method: PaymentMethod
    status: PaymentStatus
    transaction_ref: str | None
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime

    booking:  _BookingRef | None = None
    customer: _CustomerRef | None = None

    model_config = {"from_attributes": True}


class PaginatedPayments(BaseModel):
    items: list[PaymentResponse]
    total: int
    page: int
    size: int
    pages: int
