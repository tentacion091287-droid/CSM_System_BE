import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel
from app.models.maintenance import MaintenanceStatus, MaintenanceType


class MaintenanceCreate(BaseModel):
    vehicle_id: uuid.UUID
    maintenance_type: MaintenanceType | None = None
    description: str | None = None
    scheduled_date: date
    cost: Decimal | None = None
    performed_by: str | None = None


class MaintenanceUpdate(BaseModel):
    maintenance_type: MaintenanceType | None = None
    description: str | None = None
    scheduled_date: date | None = None
    cost: Decimal | None = None
    performed_by: str | None = None
    status: MaintenanceStatus | None = None


class MaintenanceComplete(BaseModel):
    completed_date: date | None = None
    cost: Decimal | None = None
    performed_by: str | None = None


class MaintenanceResponse(BaseModel):
    id: uuid.UUID
    vehicle_id: uuid.UUID
    maintenance_type: MaintenanceType | None
    description: str | None
    scheduled_date: date
    completed_date: date | None
    cost: Decimal | None
    performed_by: str | None
    status: MaintenanceStatus
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedMaintenance(BaseModel):
    items: list[MaintenanceResponse]
    total: int
    page: int
    size: int
    pages: int
