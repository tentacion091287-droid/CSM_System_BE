import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from fastapi import HTTPException, status
from app.models.driver import Driver
from app.models.driver_rating import DriverRating
from app.models.booking import Booking, BookingStatus
from app.models.user import User
from app.schemas.driver_rating import RatingCreate


async def submit_rating(db: AsyncSession, data: RatingCreate, current_user: User) -> DriverRating:
    booking_result = await db.execute(select(Booking).where(Booking.id == data.booking_id))
    booking = booking_result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.status != BookingStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Can only rate a completed booking",
        )

    if booking.customer_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only rate your own bookings",
        )

    if not booking.driver_id or booking.driver_id != data.driver_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Driver was not assigned to this booking",
        )

    existing = await db.execute(
        select(DriverRating).where(DriverRating.booking_id == data.booking_id)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This booking has already been rated",
        )

    rating_record = DriverRating(
        driver_id=data.driver_id,
        booking_id=data.booking_id,
        customer_id=current_user.id,
        rating=data.rating,
        review=data.review,
    )
    db.add(rating_record)
    await db.flush()

    avg_result = await db.execute(
        select(func.avg(DriverRating.rating)).where(DriverRating.driver_id == data.driver_id)
    )
    avg = avg_result.scalar() or data.rating

    driver_result = await db.execute(select(Driver).where(Driver.id == data.driver_id))
    driver = driver_result.scalar_one()
    driver.avg_rating = round(float(avg), 2)
    driver.total_trips += 1

    await db.commit()
    await db.refresh(rating_record)
    return rating_record


async def list_driver_ratings(
    db: AsyncSession, driver_id: uuid.UUID, page: int, size: int
) -> dict:
    driver_result = await db.execute(select(Driver).where(Driver.id == driver_id))
    if not driver_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Driver not found")

    query = (
        select(DriverRating)
        .where(DriverRating.driver_id == driver_id)
        .order_by(DriverRating.created_at.desc())
    )
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    records = (await db.execute(query.offset((page - 1) * size).limit(size))).scalars().all()
    return {
        "items": records,
        "total": total,
        "page": page,
        "size": size,
        "pages": max(1, (total + size - 1) // size),
    }
