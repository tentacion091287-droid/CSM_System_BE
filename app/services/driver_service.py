import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from app.models.driver import Driver
from app.schemas.driver import DriverCreate, DriverUpdate, DriverAvailabilityUpdate


async def list_drivers(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    is_available: bool | None = None,
) -> dict:
    query = select(Driver).where(Driver.is_active == True)
    if is_available is not None:
        query = query.where(Driver.is_available == is_available)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    drivers = (await db.execute(query.offset((page - 1) * size).limit(size))).scalars().all()
    return {
        "items": drivers,
        "total": total,
        "page": page,
        "size": size,
        "pages": max(1, (total + size - 1) // size),
    }


async def get_driver(db: AsyncSession, driver_id: uuid.UUID) -> Driver:
    result = await db.execute(
        select(Driver).where(Driver.id == driver_id, Driver.is_active == True)
    )
    driver = result.scalar_one_or_none()
    if not driver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")
    return driver


async def create_driver(db: AsyncSession, data: DriverCreate) -> Driver:
    existing_phone = await db.execute(
        select(Driver).where(Driver.phone == data.phone, Driver.is_active == True)
    )
    if existing_phone.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Phone number already registered"
        )

    existing_license = await db.execute(
        select(Driver).where(Driver.license_number == data.license_number, Driver.is_active == True)
    )
    if existing_license.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="License number already registered"
        )

    driver = Driver(**data.model_dump())
    db.add(driver)
    await db.commit()
    await db.refresh(driver)
    return driver


async def update_driver(
    db: AsyncSession, driver_id: uuid.UUID, data: DriverUpdate
) -> Driver:
    driver = await get_driver(db, driver_id)
    updates = data.model_dump(exclude_none=True)

    if "phone" in updates and updates["phone"] != driver.phone:
        existing = await db.execute(
            select(Driver).where(
                Driver.phone == updates["phone"],
                Driver.is_active == True,
                Driver.id != driver_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Phone number already registered",
            )

    if "license_number" in updates and updates["license_number"] != driver.license_number:
        existing = await db.execute(
            select(Driver).where(
                Driver.license_number == updates["license_number"],
                Driver.is_active == True,
                Driver.id != driver_id,
            )
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="License number already registered",
            )

    for key, value in updates.items():
        setattr(driver, key, value)
    await db.commit()
    await db.refresh(driver)
    return driver


async def toggle_availability(
    db: AsyncSession, driver_id: uuid.UUID, data: DriverAvailabilityUpdate
) -> Driver:
    driver = await get_driver(db, driver_id)
    driver.is_available = data.is_available
    await db.commit()
    await db.refresh(driver)
    return driver


async def deactivate_driver(db: AsyncSession, driver_id: uuid.UUID) -> None:
    driver = await get_driver(db, driver_id)
    driver.is_active = False
    await db.commit()
