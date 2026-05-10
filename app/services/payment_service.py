import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from fastapi import HTTPException, status
from app.models.booking import Booking, BookingStatus
from app.models.payment import Payment, PaymentStatus
from app.models.user import User, UserRole
from app.schemas.payment import PaymentCreate
from app.services import invoice_service


async def _get_payment_or_404(db: AsyncSession, payment_id: uuid.UUID) -> Payment:
    result = await db.execute(select(Payment).where(Payment.id == payment_id))
    payment = result.scalar_one_or_none()
    if not payment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Payment not found")
    return payment


async def initiate_payment(
    db: AsyncSession, data: PaymentCreate, current_user: User
) -> Payment:
    booking_result = await db.execute(
        select(Booking).where(
            Booking.id == data.booking_id, Booking.customer_id == current_user.id
        )
    )
    booking = booking_result.scalar_one_or_none()
    if not booking:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Booking not found")

    if booking.status != BookingStatus.approved:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment can only be initiated for approved bookings",
        )

    existing_result = await db.execute(
        select(Payment).where(Payment.booking_id == data.booking_id)
    )
    if existing_result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Payment already exists for this booking",
        )

    payment = Payment(
        booking_id=data.booking_id,
        customer_id=current_user.id,
        amount=booking.estimated_cost,
        payment_method=data.payment_method,
    )
    db.add(payment)
    await db.commit()
    await db.refresh(payment)
    return payment


async def list_payments(db: AsyncSession, current_user: User, page: int, size: int) -> dict:
    if current_user.role == UserRole.admin:
        query = select(Payment)
    else:
        query = select(Payment).where(Payment.customer_id == current_user.id)

    query = query.order_by(Payment.created_at.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    payments = (await db.execute(query.offset((page - 1) * size).limit(size))).scalars().all()
    return {
        "items": payments,
        "total": total,
        "page": page,
        "size": size,
        "pages": max(1, (total + size - 1) // size),
    }


async def get_payment(db: AsyncSession, payment_id: uuid.UUID, current_user: User) -> Payment:
    payment = await _get_payment_or_404(db, payment_id)
    if current_user.role != UserRole.admin and payment.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return payment


async def process_payment(db: AsyncSession, payment_id: uuid.UUID) -> Payment:
    payment = await _get_payment_or_404(db, payment_id)
    if payment.status != PaymentStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only pending payments can be processed",
        )

    payment.status = PaymentStatus.completed
    payment.paid_at = datetime.now(timezone.utc)
    payment.transaction_ref = f"TXN-{uuid.uuid4().hex[:12].upper()}"

    await invoice_service.create_invoice(db, payment)

    await db.commit()
    await db.refresh(payment)
    return payment


async def refund_payment(db: AsyncSession, payment_id: uuid.UUID) -> Payment:
    payment = await _get_payment_or_404(db, payment_id)
    if payment.status != PaymentStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only completed payments can be refunded",
        )

    payment.status = PaymentStatus.refunded
    await db.commit()
    await db.refresh(payment)
    return payment
