import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, computed_field


class _VehicleRef(BaseModel):
    make: str
    model: str
    model_config = {"from_attributes": True}


class _BookingRef(BaseModel):
    id: uuid.UUID
    vehicle: _VehicleRef | None = None
    pickup_date: date | None = None
    return_date: date | None = None
    model_config = {"from_attributes": True}


class _CustomerRef(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str

    @computed_field
    @property
    def name(self) -> str:
        return self.full_name

    model_config = {"from_attributes": True}


class InvoiceResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    payment_id: uuid.UUID
    invoice_number: str
    rental_days: int
    daily_rate: Decimal
    base_amount: Decimal
    fine_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    issued_at: datetime

    booking:  _BookingRef | None = None
    customer: _CustomerRef | None = None

    @computed_field
    @property
    def amount(self) -> Decimal:
        return self.total_amount

    @computed_field
    @property
    def status(self) -> str:
        return "paid"

    @computed_field
    @property
    def issued_date(self) -> datetime:
        return self.issued_at

    model_config = {"from_attributes": True}


class PaginatedInvoices(BaseModel):
    items: list[InvoiceResponse]
    total: int
    page: int
    size: int
    pages: int
