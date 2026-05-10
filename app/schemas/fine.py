import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, computed_field
from app.models.fine import FineStatus


class _BookingRef(BaseModel):
    id: uuid.UUID
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


class FineResponse(BaseModel):
    id: uuid.UUID
    booking_id: uuid.UUID
    customer_id: uuid.UUID
    overdue_days: int
    daily_fine_rate: Decimal
    total_amount: Decimal
    status: FineStatus
    paid_at: datetime | None
    created_at: datetime
    updated_at: datetime

    booking:  _BookingRef | None = None
    customer: _CustomerRef | None = None

    @computed_field
    @property
    def amount(self) -> Decimal:
        return self.total_amount

    @computed_field
    @property
    def reason(self) -> str:
        return f"Late return: {self.overdue_days} day(s) overdue"

    @computed_field
    @property
    def issued_date(self) -> datetime:
        return self.created_at

    model_config = {"from_attributes": True}


class PaginatedFines(BaseModel):
    items: list[FineResponse]
    total: int
    page: int
    size: int
    pages: int
