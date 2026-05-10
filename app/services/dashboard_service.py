from datetime import date, timezone, datetime
from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import case, func, select, text
from app.models.booking import Booking, BookingStatus
from app.models.driver import Driver
from app.models.fine import Fine, FineStatus
from app.models.maintenance import Maintenance, MaintenanceStatus
from app.models.payment import Payment, PaymentStatus
from app.models.vehicle import Vehicle, VehicleStatus


def _first_of_month_n_months_ago(n: int) -> date:
    today = date.today()
    month = today.month - n
    year = today.year
    while month <= 0:
        month += 12
        year -= 1
    return date(year, month, 1)


async def get_dashboard(db: AsyncSession) -> dict:
    # ── Booking stats ──────────────────────────────────────────────────────────
    booking_rows = (
        await db.execute(select(Booking.status, func.count().label("n")).group_by(Booking.status))
    ).all()
    bc = {row.status: row.n for row in booking_rows}
    bookings = {
        "total": sum(bc.values()),
        "pending": bc.get(BookingStatus.pending, 0),
        "approved": bc.get(BookingStatus.approved, 0),
        "active": bc.get(BookingStatus.active, 0),
        "completed": bc.get(BookingStatus.completed, 0),
        "cancelled": bc.get(BookingStatus.cancelled, 0),
        "rejected": bc.get(BookingStatus.rejected, 0),
    }

    # ── Vehicle stats ──────────────────────────────────────────────────────────
    vehicle_rows = (
        await db.execute(
            select(Vehicle.status, func.count().label("n"))
            .where(Vehicle.is_deleted == False)
            .group_by(Vehicle.status)
        )
    ).all()
    vc = {row.status: row.n for row in vehicle_rows}
    vehicles = {
        "total": sum(vc.values()),
        "available": vc.get(VehicleStatus.available, 0),
        "booked": vc.get(VehicleStatus.booked, 0),
        "maintenance": vc.get(VehicleStatus.maintenance, 0),
    }

    # ── Driver stats ───────────────────────────────────────────────────────────
    driver_row = (
        await db.execute(
            select(
                func.count().label("total"),
                func.sum(case((Driver.is_available == True, 1), else_=0)).label("available"),
            ).where(Driver.is_active == True)
        )
    ).one()
    drivers = {
        "total": driver_row.total,
        "available": driver_row.available or 0,
    }

    # ── Revenue stats ──────────────────────────────────────────────────────────
    first_of_this_month = date.today().replace(day=1)
    first_of_this_month_dt = datetime(
        first_of_this_month.year, first_of_this_month.month, 1, tzinfo=timezone.utc
    )

    total_rev = (
        await db.execute(
            select(func.coalesce(func.sum(Payment.amount), Decimal("0.00"))).where(
                Payment.status == PaymentStatus.completed
            )
        )
    ).scalar()

    this_month_rev = (
        await db.execute(
            select(func.coalesce(func.sum(Payment.amount), Decimal("0.00"))).where(
                Payment.status == PaymentStatus.completed,
                Payment.paid_at >= first_of_this_month_dt,
            )
        )
    ).scalar()

    revenue = {"total": total_rev, "this_month": this_month_rev}

    # ── Payment stats ──────────────────────────────────────────────────────────
    payment_rows = (
        await db.execute(select(Payment.status, func.count().label("n")).group_by(Payment.status))
    ).all()
    pc = {row.status: row.n for row in payment_rows}
    payments = {
        "pending": pc.get(PaymentStatus.pending, 0),
        "completed": pc.get(PaymentStatus.completed, 0),
        "refunded": pc.get(PaymentStatus.refunded, 0),
    }

    # ── Fine stats ─────────────────────────────────────────────────────────────
    fine_row = (
        await db.execute(
            select(
                func.count().label("count"),
                func.coalesce(func.sum(Fine.total_amount), Decimal("0.00")).label("amount"),
            ).where(Fine.status == FineStatus.pending)
        )
    ).one()
    fines = {"pending_count": fine_row.count, "pending_amount": fine_row.amount}

    # ── Maintenance stats ──────────────────────────────────────────────────────
    maint_rows = (
        await db.execute(
            select(Maintenance.status, func.count().label("n"))
            .where(
                Maintenance.status.in_(
                    [MaintenanceStatus.scheduled, MaintenanceStatus.in_progress]
                )
            )
            .group_by(Maintenance.status)
        )
    ).all()
    mc = {row.status: row.n for row in maint_rows}
    maintenance = {
        "scheduled": mc.get(MaintenanceStatus.scheduled, 0),
        "in_progress": mc.get(MaintenanceStatus.in_progress, 0),
    }

    # ── Monthly revenue (last 6 months) ────────────────────────────────────────
    six_months_ago_dt = datetime(
        *_first_of_month_n_months_ago(5).timetuple()[:3], tzinfo=timezone.utc
    )
    monthly_rows = (
        await db.execute(
            select(
                func.date_trunc("month", Payment.paid_at).label("month"),
                func.sum(Payment.amount).label("revenue"),
            )
            .where(
                Payment.status == PaymentStatus.completed,
                Payment.paid_at >= six_months_ago_dt,
            )
            .group_by(text("1"))
            .order_by(text("1"))
        )
    ).all()
    monthly_revenue = [
        {"month": row.month.strftime("%Y-%m"), "revenue": row.revenue}
        for row in monthly_rows
    ]

    return {
        "bookings": bookings,
        "vehicles": vehicles,
        "drivers": drivers,
        "revenue": revenue,
        "payments": payments,
        "fines": fines,
        "maintenance": maintenance,
        "monthly_revenue": monthly_revenue,
    }
