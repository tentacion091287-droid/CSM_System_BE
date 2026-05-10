import uuid
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status
from app.models.booking import Booking, BookingStatus
from app.models.vehicle import Vehicle, VehicleStatus
from app.models.driver import Driver
from app.models.user import User, UserRole
from app.schemas.booking import (
    BookingCreate,
    BookingUpdate,
    BookingReject,
    BookingComplete,
    AssignDriverRequest,
)


_BOOKING_RELS = [
    selectinload(Booking.vehicle),
    selectinload(Booking.customer),
    selectinload(Booking.driver),
    selectinload(Booking.rating),
]


async def _get_booking_or_404(db: AsyncSession, booking_id: uuid.UUID) -> Booking:
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return booking


async def _get_booking_with_rels(db: AsyncSession, booking_id: uuid.UUID) -> Booking:
    result = await db.execute(
        select(Booking).options(*_BOOKING_RELS).where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")
    return booking


async def _check_vehicle_availability(
    db: AsyncSession,
    vehicle_id: uuid.UUID,
    pickup_date: date,
    return_date: date,
    exclude_booking_id: uuid.UUID | None = None,
) -> None:
    query = select(Booking).where(
        Booking.vehicle_id == vehicle_id,
        Booking.status.in_([BookingStatus.approved, BookingStatus.active]),
        Booking.return_date > pickup_date,
        Booking.pickup_date < return_date,
    )
    if exclude_booking_id:
        query = query.where(Booking.id != exclude_booking_id)
    result = await db.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vehicle is not available for the selected dates",
        )


async def create_booking(db: AsyncSession, data: BookingCreate, current_user: User) -> Booking:
    vehicle_result = await db.execute(
        select(Vehicle).where(Vehicle.id == data.vehicle_id, Vehicle.is_deleted == False)
    )
    vehicle = vehicle_result.scalar_one_or_none()
    if not vehicle:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")

    if vehicle.status == VehicleStatus.maintenance:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vehicle is currently under maintenance",
        )

    await _check_vehicle_availability(db, data.vehicle_id, data.pickup_date, data.return_date)

    days = (data.return_date - data.pickup_date).days
    estimated_cost = Decimal(days) * vehicle.daily_rate

    booking = Booking(
        **data.model_dump(),
        customer_id=current_user.id,
        estimated_cost=estimated_cost,
    )
    db.add(booking)
    await db.commit()
    await db.refresh(booking)
    return await _get_booking_with_rels(db, booking.id)


async def list_bookings(db: AsyncSession, current_user: User, page: int, size: int) -> dict:
    if current_user.role == UserRole.admin:
        base = select(Booking)
    else:
        base = select(Booking).where(Booking.customer_id == current_user.id)

    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar()
    bookings = (
        await db.execute(
            base.options(*_BOOKING_RELS)
            .order_by(Booking.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
    ).scalars().all()
    return {
        "items": bookings,
        "total": total,
        "page": page,
        "size": size,
        "pages": max(1, (total + size - 1) // size),
    }


async def get_booking(db: AsyncSession, booking_id: uuid.UUID, current_user: User) -> Booking:
    booking = await _get_booking_or_404(db, booking_id)
    if current_user.role != UserRole.admin and booking.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return await _get_booking_with_rels(db, booking_id)


async def get_history(db: AsyncSession, current_user: User, page: int, size: int) -> dict:
    base = select(Booking).where(
        Booking.customer_id == current_user.id,
        Booking.status == BookingStatus.completed,
    )
    total = (await db.execute(select(func.count()).select_from(base.subquery()))).scalar()
    bookings = (
        await db.execute(
            base.options(*_BOOKING_RELS)
            .order_by(Booking.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
    ).scalars().all()
    return {
        "items": bookings,
        "total": total,
        "page": page,
        "size": size,
        "pages": max(1, (total + size - 1) // size),
    }


async def update_booking(
    db: AsyncSession, booking_id: uuid.UUID, data: BookingUpdate, current_user: User
) -> Booking:
    booking = await _get_booking_or_404(db, booking_id)
    if booking.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if booking.status != BookingStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Only pending bookings can be edited"
        )

    updates = data.model_dump(exclude_none=True)
    new_pickup = updates.get("pickup_date", booking.pickup_date)
    new_return = updates.get("return_date", booking.return_date)

    if new_return <= new_pickup:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="return_date must be after pickup_date",
        )

    date_changed = "pickup_date" in updates or "return_date" in updates
    if date_changed:
        await _check_vehicle_availability(
            db, booking.vehicle_id, new_pickup, new_return, exclude_booking_id=booking_id
        )
        vehicle_result = await db.execute(
            select(Vehicle).where(Vehicle.id == booking.vehicle_id)
        )
        vehicle = vehicle_result.scalar_one()
        days = (new_return - new_pickup).days
        updates["estimated_cost"] = Decimal(days) * vehicle.daily_rate

    for key, value in updates.items():
        setattr(booking, key, value)

    await db.commit()
    return await _get_booking_with_rels(db, booking.id)


async def cancel_booking(db: AsyncSession, booking_id: uuid.UUID, current_user: User) -> None:
    booking = await _get_booking_or_404(db, booking_id)
    if booking.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if booking.status != BookingStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Only pending bookings can be cancelled"
        )
    booking.status = BookingStatus.cancelled
    await db.commit()


async def approve_booking(db: AsyncSession, booking_id: uuid.UUID) -> Booking:
    booking = await _get_booking_or_404(db, booking_id)
    if booking.status != BookingStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Only pending bookings can be approved"
        )
    booking.status = BookingStatus.approved
    await db.commit()
    return await _get_booking_with_rels(db, booking.id)


async def reject_booking(
    db: AsyncSession, booking_id: uuid.UUID, data: BookingReject
) -> Booking:
    booking = await _get_booking_or_404(db, booking_id)
    if booking.status not in (BookingStatus.pending, BookingStatus.approved):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending or approved bookings can be rejected",
        )
    booking.status = BookingStatus.rejected
    if data.admin_notes:
        booking.admin_notes = data.admin_notes
    await db.commit()
    return await _get_booking_with_rels(db, booking.id)


async def activate_booking(db: AsyncSession, booking_id: uuid.UUID) -> Booking:
    booking = await _get_booking_or_404(db, booking_id)
    if booking.status != BookingStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only approved bookings can be activated",
        )

    booking.status = BookingStatus.active

    vehicle_result = await db.execute(select(Vehicle).where(Vehicle.id == booking.vehicle_id))
    vehicle = vehicle_result.scalar_one()
    vehicle.status = VehicleStatus.booked

    if booking.driver_id:
        driver_result = await db.execute(
            select(Driver).where(Driver.id == booking.driver_id)
        )
        driver = driver_result.scalar_one_or_none()
        if driver:
            driver.is_available = False

    await db.commit()
    return await _get_booking_with_rels(db, booking.id)


async def complete_booking(
    db: AsyncSession, booking_id: uuid.UUID, data: BookingComplete
) -> Booking:
    booking = await _get_booking_or_404(db, booking_id)
    if booking.status != BookingStatus.active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Only active bookings can be completed"
        )

    booking.actual_return = data.actual_return
    booking.status = BookingStatus.completed

    vehicle_result = await db.execute(select(Vehicle).where(Vehicle.id == booking.vehicle_id))
    vehicle = vehicle_result.scalar_one()
    vehicle.status = VehicleStatus.available

    if booking.driver_id:
        driver_result = await db.execute(
            select(Driver).where(Driver.id == booking.driver_id)
        )
        driver = driver_result.scalar_one_or_none()
        if driver:
            driver.is_available = True

    if booking.actual_return and booking.actual_return > booking.return_date:
        from app.services import fine_service
        await fine_service.create_fine(db, booking)

    await db.commit()
    return await _get_booking_with_rels(db, booking.id)


async def assign_driver(
    db: AsyncSession, booking_id: uuid.UUID, data: AssignDriverRequest
) -> Booking:
    booking = await _get_booking_or_404(db, booking_id)
    if booking.status not in (BookingStatus.pending, BookingStatus.approved):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Driver can only be assigned to pending or approved bookings",
        )

    driver_result = await db.execute(
        select(Driver).where(Driver.id == data.driver_id, Driver.is_active == True)
    )
    if not driver_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    booking.driver_id = data.driver_id
    await db.commit()
    return await _get_booking_with_rels(db, booking.id)
