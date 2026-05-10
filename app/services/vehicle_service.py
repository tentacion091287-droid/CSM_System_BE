import uuid
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, column, text
from fastapi import HTTPException, status
from app.models.vehicle import Vehicle, VehicleCategory, VehicleStatus
from app.schemas.vehicle import VehicleCreate, VehicleUpdate, VehicleStatusUpdate


async def list_vehicles(
    db: AsyncSession,
    category: VehicleCategory | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    page: int = 1,
    size: int = 20,
) -> dict:
    query = select(Vehicle).where(Vehicle.is_deleted == False)

    if category:
        query = query.where(Vehicle.category == category)

    if date_from and date_to:
        # exclude vehicles with overlapping approved/active bookings
        booked_subquery = (
            select(column("vehicle_id"))
            .select_from(text("bookings"))
            .where(
                text(
                    "status IN ('approved', 'active') "
                    "AND NOT (return_date <= :date_from OR pickup_date >= :date_to)"
                ).bindparams(date_from=date_from, date_to=date_to)
            )
            .scalar_subquery()
        )
        query = query.where(Vehicle.id.not_in(booked_subquery))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    vehicles = (await db.execute(query.offset((page - 1) * size).limit(size))).scalars().all()

    return {
        "items": vehicles,
        "total": total,
        "page": page,
        "size": size,
        "pages": max(1, (total + size - 1) // size),
    }


async def get_vehicle(db: AsyncSession, vehicle_id: uuid.UUID) -> Vehicle:
    result = await db.execute(
        select(Vehicle).where(Vehicle.id == vehicle_id, Vehicle.is_deleted == False)
    )
    vehicle = result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return vehicle


async def create_vehicle(db: AsyncSession, data: VehicleCreate) -> Vehicle:
    existing = await db.execute(
        select(Vehicle).where(
            Vehicle.license_plate == data.license_plate, Vehicle.is_deleted == False
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="License plate already registered"
        )
    vehicle = Vehicle(**data.model_dump())
    db.add(vehicle)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


async def update_vehicle(
    db: AsyncSession, vehicle_id: uuid.UUID, data: VehicleUpdate
) -> Vehicle:
    vehicle = await get_vehicle(db, vehicle_id)
    updates = data.model_dump(exclude_none=True)

    if "license_plate" in updates and updates["license_plate"] != vehicle.license_plate:
        existing = await db.execute(
            select(Vehicle).where(
                Vehicle.license_plate == updates["license_plate"],
                Vehicle.is_deleted == False,
                Vehicle.id != vehicle_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License plate already registered",
            )

    for key, value in updates.items():
        setattr(vehicle, key, value)
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


async def update_status(
    db: AsyncSession, vehicle_id: uuid.UUID, data: VehicleStatusUpdate
) -> Vehicle:
    vehicle = await get_vehicle(db, vehicle_id)
    vehicle.status = data.status
    await db.commit()
    await db.refresh(vehicle)
    return vehicle


async def delete_vehicle(db: AsyncSession, vehicle_id: uuid.UUID) -> None:
    vehicle = await get_vehicle(db, vehicle_id)
    vehicle.is_deleted = True
    await db.commit()
