import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel


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

    model_config = {"from_attributes": True}


class PaginatedInvoices(BaseModel):
    items: list[InvoiceResponse]
    total: int
    page: int
    size: int
    pages: int
