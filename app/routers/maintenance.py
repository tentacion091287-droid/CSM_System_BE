import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.dependencies import get_db, require_admin
from app.models.maintenance import MaintenanceStatus
from app.models.user import User
from app.schemas.maintenance import (
    MaintenanceComplete,
    MaintenanceCreate,
    MaintenanceResponse,
    MaintenanceUpdate,
    PaginatedMaintenance,
)
from app.services import maintenance_service

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.get("/", response_model=PaginatedMaintenance)
async def list_maintenance(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    vehicle_id: uuid.UUID | None = Query(None),
    status: MaintenanceStatus | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await maintenance_service.list_maintenance(db, page, size, vehicle_id, status)


@router.post("/", response_model=MaintenanceResponse, status_code=201)
async def schedule_maintenance(
    data: MaintenanceCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await maintenance_service.schedule_maintenance(db, data)


# /{record_id} dynamic routes — no static conflicts, UUIDs won't parse as "complete"/"cancel"
@router.get("/{record_id}", response_model=MaintenanceResponse)
async def get_maintenance(
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await maintenance_service.get_maintenance(db, record_id)


@router.put("/{record_id}", response_model=MaintenanceResponse)
async def update_maintenance(
    record_id: uuid.UUID,
    data: MaintenanceUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await maintenance_service.update_maintenance(db, record_id, data)


@router.patch("/{record_id}/complete", response_model=MaintenanceResponse)
async def complete_maintenance(
    record_id: uuid.UUID,
    data: MaintenanceComplete,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await maintenance_service.complete_maintenance(db, record_id, data)


@router.patch("/{record_id}/cancel", response_model=MaintenanceResponse)
async def cancel_maintenance(
    record_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_admin),
):
    return await maintenance_service.cancel_maintenance(db, record_id)
