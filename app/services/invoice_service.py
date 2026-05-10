import uuid
from datetime import date
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from fastapi import HTTPException, status
from app.models.booking import Booking
from app.models.invoice import Invoice
from app.models.payment import Payment
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle
from app.core.config import settings


async def _generate_invoice_number(db: AsyncSession) -> str:
    today = date.today().strftime("%Y%m%d")
    prefix = f"INV-{today}-"
    count_result = await db.execute(
        select(func.count()).select_from(Invoice).where(Invoice.invoice_number.like(f"{prefix}%"))
    )
    count = count_result.scalar() or 0
    return f"{prefix}{str(count + 1).zfill(4)}"


async def create_invoice(db: AsyncSession, payment: Payment) -> Invoice:
    booking_result = await db.execute(select(Booking).where(Booking.id == payment.booking_id))
    booking = booking_result.scalar_one()

    vehicle_result = await db.execute(select(Vehicle).where(Vehicle.id == booking.vehicle_id))
    vehicle = vehicle_result.scalar_one()

    rental_days = (booking.return_date - booking.pickup_date).days
    base_amount = Decimal(rental_days) * vehicle.daily_rate

    # Fine lookup wired up in Phase 7
    fine_amount = Decimal("0.00")

    tax_amount = (base_amount + fine_amount) * Decimal(str(settings.TAX_RATE))
    total_amount = base_amount + fine_amount + tax_amount

    invoice_number = await _generate_invoice_number(db)

    invoice = Invoice(
        booking_id=booking.id,
        payment_id=payment.id,
        invoice_number=invoice_number,
        rental_days=rental_days,
        daily_rate=vehicle.daily_rate,
        base_amount=base_amount,
        fine_amount=fine_amount,
        tax_amount=tax_amount,
        total_amount=total_amount,
    )
    db.add(invoice)
    return invoice


async def list_invoices(db: AsyncSession, current_user: User, page: int, size: int) -> dict:
    if current_user.role == UserRole.admin:
        query = select(Invoice)
    else:
        query = (
            select(Invoice)
            .join(Payment, Invoice.payment_id == Payment.id)
            .where(Payment.customer_id == current_user.id)
        )

    query = query.order_by(Invoice.issued_at.desc())
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar()
    invoices = (await db.execute(query.offset((page - 1) * size).limit(size))).scalars().all()
    return {
        "items": invoices,
        "total": total,
        "page": page,
        "size": size,
        "pages": max(1, (total + size - 1) // size),
    }


async def _get_invoice_or_404(db: AsyncSession, invoice_id: uuid.UUID) -> Invoice:
    result = await db.execute(select(Invoice).where(Invoice.id == invoice_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    return invoice


async def _check_invoice_access(db: AsyncSession, invoice: Invoice, current_user: User) -> None:
    if current_user.role == UserRole.admin:
        return
    payment_result = await db.execute(select(Payment).where(Payment.id == invoice.payment_id))
    payment = payment_result.scalar_one()
    if payment.customer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


async def get_invoice(db: AsyncSession, invoice_id: uuid.UUID, current_user: User) -> Invoice:
    invoice = await _get_invoice_or_404(db, invoice_id)
    await _check_invoice_access(db, invoice, current_user)
    return invoice


async def get_invoice_by_booking(
    db: AsyncSession, booking_id: uuid.UUID, current_user: User
) -> Invoice:
    result = await db.execute(select(Invoice).where(Invoice.booking_id == booking_id))
    invoice = result.scalar_one_or_none()
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
    await _check_invoice_access(db, invoice, current_user)
    return invoice
