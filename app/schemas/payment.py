import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from app.models.payment import PaymentMethod, PaymentStatus


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

    model_config = {"from_attributes": True}


class PaginatedPayments(BaseModel):
    items: list[PaymentResponse]
    total: int
    page: int
    size: int
    pages: int
