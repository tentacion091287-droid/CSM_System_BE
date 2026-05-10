import uuid
from datetime import datetime, timezone
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from fastapi import HTTPException, status
from app.models.booking import Booking
from app.models.fine import Fine, FineStatus
from app.models.user import User, UserRole
from app.core.config import settings


async def create_fine(db: AsyncSession, booking: Booking) -> Fine | None:
    overdue_days = (booking.actual_return - booking.return_date).days
    if overdue_days <= 0:
        return None

    daily_fine_rate = Decimal(str(settings.DAILY_FINE_RATE))
    fine = Fine(
        booking_id=booking.id,
        customer_id=booking.customer_id,
        overdue_days=overdue_days,
        daily_fine_rate=daily_fine_rate,
        total_amount=Decimal(overdue_days) * daily_fine_rate,
    )
    db.add(fine)
    return fine


async def list_fines(db: AsyncSession, current_user: User, page: int, size: int) -> dict:
    if current_user.role == UserRole.admin:
        query = select(Fine)
    else:
        query = select(Fine).where(Fine.customer_id == current_user.id)

    query = query.order_by(Fine.created_at.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    fines = (await db.execute(query.offset((page - 1) * size).limit(size))).scalars().all()
    return {
        "items": fines,
        "total": total,
        "page": page,
        "size": size,
        "pages": max(1, (total + size - 1) // size),
    }


async def _get_fine_or_404(db: AsyncSession, fine_id: uuid.UUID) -> Fine:
    result = await db.execute(select(Fine).where(Fine.id == fine_id))
    fine = result.scalar_one_or_none()
    if not fine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fine not found")
    return fine


async def get_fine(db: AsyncSession, fine_id: uuid.UUID, current_user: User) -> Fine:
    fine = await _get_fine_or_404(db, fine_id)
    if current_user.role != UserRole.admin and fine.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return fine


async def get_fine_by_booking(
    db: AsyncSession, booking_id: uuid.UUID, current_user: User
) -> Fine:
    result = await db.execute(select(Fine).where(Fine.booking_id == booking_id))
    fine = result.scalar_one_or_none()
    if not fine:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Fine not found")
    if current_user.role != UserRole.admin and fine.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return fine


async def waive_fine(db: AsyncSession, fine_id: uuid.UUID) -> Fine:
    fine = await _get_fine_or_404(db, fine_id)
    if fine.status != FineStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending fines can be waived",
        )
    fine.status = FineStatus.waived
    await db.commit()
    await db.refresh(fine)
    return fine


async def pay_fine(db: AsyncSession, fine_id: uuid.UUID, current_user: User) -> Fine:
    fine = await _get_fine_or_404(db, fine_id)
    if fine.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if fine.status != FineStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending fines can be paid",
        )
    fine.status = FineStatus.paid
    fine.paid_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(fine)
    return fine
