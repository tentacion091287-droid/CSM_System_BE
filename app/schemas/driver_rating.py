import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class RatingCreate(BaseModel):
    driver_id: uuid.UUID
    booking_id: uuid.UUID
    rating: int = Field(..., ge=1, le=5)
    review: str | None = None


class RatingResponse(BaseModel):
    id: uuid.UUID
    driver_id: uuid.UUID
    booking_id: uuid.UUID
    customer_id: uuid.UUID
    rating: int
    review: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaginatedRatings(BaseModel):
    items: list[RatingResponse]
    total: int
    page: int
    size: int
    pages: int
