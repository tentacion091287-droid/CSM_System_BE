import uuid
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel
from app.models.fine import FineStatus


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

    model_config = {"from_attributes": True}


class PaginatedFines(BaseModel):
    items: list[FineResponse]
    total: int
    page: int
    size: int
    pages: int
