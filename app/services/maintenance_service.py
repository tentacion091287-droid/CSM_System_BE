import uuid
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from fastapi import HTTPException, status
from app.models.maintenance import Maintenance, MaintenanceStatus
from app.models.vehicle import Vehicle, VehicleStatus
from app.schemas.maintenance import MaintenanceCreate, MaintenanceComplete, MaintenanceUpdate


async def _get_record_or_404(db: AsyncSession, record_id: uuid.UUID) -> Maintenance:
    result = await db.execute(select(Maintenance).where(Maintenance.id == record_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Maintenance record not found"
        )
    return record


async def list_maintenance(
    db: AsyncSession,
    page: int,
    size: int,
    vehicle_id: uuid.UUID | None = None,
    filter_status: MaintenanceStatus | None = None,
) -> dict:
    query = select(Maintenance)
    if vehicle_id:
        query = query.where(Maintenance.vehicle_id == vehicle_id)
    if filter_status:
        query = query.where(Maintenance.status == filter_status)

    query = query.order_by(Maintenance.scheduled_date.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    records = (await db.execute(query.offset((page - 1) * size).limit(size))).scalars().all()
    return {
        "items": records,
        "total": total,
        "page": page,
        "size": size,
        "pages": max(1, (total + size - 1) // size),
    }


async def get_maintenance(db: AsyncSession, record_id: uuid.UUID) -> Maintenance:
    return await _get_record_or_404(db, record_id)


async def schedule_maintenance(db: AsyncSession, data: MaintenanceCreate) -> Maintenance:
    vehicle_result = await db.execute(
        select(Vehicle).where(Vehicle.id == data.vehicle_id, Vehicle.is_deleted == False)
    )
    vehicle = vehicle_result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    if vehicle.status == VehicleStatus.booked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot schedule maintenance for a booked vehicle",
        )
    if vehicle.status == VehicleStatus.maintenance:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vehicle is already under maintenance",
        )

    vehicle.status = VehicleStatus.maintenance

    record = Maintenance(**data.model_dump())
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def update_maintenance(
    db: AsyncSession, record_id: uuid.UUID, data: MaintenanceUpdate
) -> Maintenance:
    record = await _get_record_or_404(db, record_id)

    if record.status in (MaintenanceStatus.completed, MaintenanceStatus.cancelled):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Completed or cancelled records cannot be updated",
        )

    updates = data.model_dump(exclude_none=True)

    if "status" in updates:
        new_status = updates["status"]
        allowed = {
            MaintenanceStatus.scheduled: [MaintenanceStatus.in_progress],
            MaintenanceStatus.in_progress: [],
        }
        if new_status not in allowed.get(record.status, []):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Cannot transition status from {record.status} to {new_status}",
            )

    for key, value in updates.items():
        setattr(record, key, value)

    await db.commit()
    await db.refresh(record)
    return record


async def complete_maintenance(
    db: AsyncSession, record_id: uuid.UUID, data: MaintenanceComplete
) -> Maintenance:
    record = await _get_record_or_404(db, record_id)

    if record.status not in (MaintenanceStatus.scheduled, MaintenanceStatus.in_progress):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only scheduled or in-progress records can be completed",
        )

    record.status = MaintenanceStatus.completed
    record.completed_date = data.completed_date or date.today()
    if data.cost is not None:
        record.cost = data.cost
    if data.performed_by is not None:
        record.performed_by = data.performed_by

    vehicle_result = await db.execute(select(Vehicle).where(Vehicle.id == record.vehicle_id))
    vehicle = vehicle_result.scalar_one()
    vehicle.status = VehicleStatus.available

    await db.commit()
    await db.refresh(record)
    return record


async def cancel_maintenance(db: AsyncSession, record_id: uuid.UUID) -> Maintenance:
    record = await _get_record_or_404(db, record_id)

    if record.status not in (MaintenanceStatus.scheduled, MaintenanceStatus.in_progress):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only scheduled or in-progress records can be cancelled",
        )

    record.status = MaintenanceStatus.cancelled

    vehicle_result = await db.execute(select(Vehicle).where(Vehicle.id == record.vehicle_id))
    vehicle = vehicle_result.scalar_one()
    vehicle.status = VehicleStatus.available

    await db.commit()
    await db.refresh(record)
    return record


async def delete_maintenance(db: AsyncSession, record_id: uuid.UUID) -> None:
    record = await _get_record_or_404(db, record_id)

    if record.status not in (MaintenanceStatus.scheduled, MaintenanceStatus.cancelled):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only scheduled or cancelled records can be deleted",
        )

    await db.delete(record)
    await db.commit()
