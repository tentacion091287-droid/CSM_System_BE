"""
Seed all tables (except vehicles) with realistic demo data.

Usage (from project root, with venv active):
    python -m scripts.seed_all

Safe to re-run — each section checks existing data and skips if already present.

Credentials:
    Admin  : admin@csm.com       / Admin@1234
    Customer: arjun.sharma@email.com / Customer@1234  (and 7 more, same password)
"""

import asyncio
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.models.booking import Booking, BookingStatus
from app.models.driver import Driver
from app.models.driver_rating import DriverRating
from app.models.fine import Fine, FineStatus
from app.models.invoice import Invoice
from app.models.maintenance import Maintenance, MaintenanceStatus, MaintenanceType
from app.models.payment import Payment, PaymentMethod, PaymentStatus
from app.models.user import User, UserRole
from app.models.vehicle import Vehicle, VehicleCategory, VehicleStatus


def _today(offset: int = 0) -> date:
    return date.today() + timedelta(days=offset)


# ─────────────────────────────────────────────────────────────────────────────
# 1. USERS
# ─────────────────────────────────────────────────────────────────────────────

_USERS = [
    # email, full_name, phone, role, password
    ("admin@csm.com",            "Admin User",      "+91-9800000001", "admin",    "Admin@1234"),
    ("arjun.sharma@email.com",   "Arjun Sharma",    "+91-9810000001", "customer", "Customer@1234"),
    ("priya.nair@email.com",     "Priya Nair",      "+91-9820000002", "customer", "Customer@1234"),
    ("rohit.verma@email.com",    "Rohit Verma",     "+91-9830000003", "customer", "Customer@1234"),
    ("sneha.patel@email.com",    "Sneha Patel",     "+91-9840000004", "customer", "Customer@1234"),
    ("vikram.iyer@email.com",    "Vikram Iyer",     "+91-9850000005", "customer", "Customer@1234"),
    ("kavya.reddy@email.com",    "Kavya Reddy",     "+91-9860000006", "customer", "Customer@1234"),
    ("manish.gupta@email.com",   "Manish Gupta",    "+91-9870000007", "customer", "Customer@1234"),
    ("divya.menon@email.com",    "Divya Menon",     "+91-9880000008", "customer", "Customer@1234"),
]


async def _seed_users(db: AsyncSession) -> dict[str, User]:
    existing = {r[0] for r in (await db.execute(select(User.email))).all()}
    new = [
        User(
            email=email, full_name=full_name, phone=phone,
            role=UserRole(role), hashed_password=hash_password(pwd),
        )
        for email, full_name, phone, role, pwd in _USERS
        if email not in existing
    ]
    if new:
        db.add_all(new)
        await db.flush()
        print(f"  Users       : +{len(new)} inserted")
    else:
        print(f"  Users       : already seeded, skipped")

    rows = (await db.execute(
        select(User).where(User.email.in_([e for e, *_ in _USERS]))
    )).scalars().all()
    return {u.email: u for u in rows}


# ─────────────────────────────────────────────────────────────────────────────
# 2. DRIVERS
# ─────────────────────────────────────────────────────────────────────────────

_DRIVERS = [
    # full_name, phone, license_number, license_expiry, avg_rating, total_trips, is_available
    ("Ramesh Kumar",    "+91-9900000001", "KA-DL-2023-001", date(2027, 6, 15),  Decimal("4.8"), 142, True),
    ("Suresh Babu",     "+91-9900000002", "KA-DL-2022-002", date(2026, 3, 20),  Decimal("4.5"),  98, True),
    ("Prakash Naidu",   "+91-9900000003", "KA-DL-2023-003", date(2027, 9, 10),  Decimal("4.2"),  76, True),
    ("Dinesh Rao",      "+91-9900000004", "KA-DL-2021-004", date(2025, 12,  5), Decimal("3.9"),  54, False),  # on active trip
    ("Anil Tiwari",     "+91-9900000005", "KA-DL-2023-005", date(2028, 2, 28),  Decimal("4.7"), 115, False),  # on active trip
    ("Venkat Swamy",    "+91-9900000006", "KA-DL-2022-006", date(2026, 7, 15),  Decimal("4.1"),  63, True),
    ("Mohan Das",       "+91-9900000007", "KA-DL-2023-007", date(2027, 11, 30), Decimal("4.6"),  89, True),
    ("Rajesh Singh",    "+91-9900000008", "KA-DL-2021-008", date(2025, 8, 20),  Decimal("3.7"),  41, True),
    ("Santosh Gowda",   "+91-9900000009", "KA-DL-2023-009", date(2028, 4, 12),  Decimal("4.9"), 167, True),
    ("Nagaraj Patil",   "+91-9900000010", "KA-DL-2022-010", date(2026, 5,  8),  Decimal("4.3"),  72, True),
    ("Harish Bhat",     "+91-9900000011", "KA-DL-2023-011", date(2027, 1, 25),  Decimal("4.0"),  58, True),
    ("Krishnamurthy R", "+91-9900000012", "KA-DL-2023-012", date(2028, 10,  3), Decimal("4.4"),  95, True),
]


async def _seed_drivers(db: AsyncSession) -> list[Driver]:
    existing_phones = {r[0] for r in (await db.execute(select(Driver.phone))).all()}
    new = [
        Driver(
            full_name=full_name, phone=phone, license_number=lic,
            license_expiry=expiry, avg_rating=avg, total_trips=trips,
            is_available=avail, is_active=True,
        )
        for full_name, phone, lic, expiry, avg, trips, avail in _DRIVERS
        if phone not in existing_phones
    ]
    if new:
        db.add_all(new)
        await db.flush()
        print(f"  Drivers     : +{len(new)} inserted")
    else:
        print(f"  Drivers     : already seeded, skipped")

    rows = (await db.execute(
        select(Driver).where(Driver.phone.in_([p for _, p, *_ in _DRIVERS]))
    )).scalars().all()
    return rows


# ─────────────────────────────────────────────────────────────────────────────
# 3. PICK VEHICLES
# ─────────────────────────────────────────────────────────────────────────────

async def _pick_vehicles(db: AsyncSession) -> list[Vehicle]:
    """Return up to 6 vehicles per category (30 total) for use in bookings."""
    out: list[Vehicle] = []
    for cat in VehicleCategory:
        rows = (await db.execute(
            select(Vehicle)
            .where(Vehicle.category == cat, Vehicle.is_deleted == False)
            .order_by(Vehicle.created_at)
            .limit(6)
        )).scalars().all()
        out.extend(rows)
    return out


# ─────────────────────────────────────────────────────────────────────────────
# 4. BOOKINGS + PAYMENTS + INVOICES + FINES + DRIVER RATINGS
# ─────────────────────────────────────────────────────────────────────────────

async def _seed_transactions(
    db: AsyncSession,
    users: dict[str, User],
    drivers: list[Driver],
    vehicles: list[Vehicle],
) -> None:
    customers = [u for u in users.values() if u.role == UserRole.customer]

    # Skip if already seeded
    cust_ids = [c.id for c in customers]
    existing = (await db.execute(
        select(func.count()).select_from(Booking)
        .where(Booking.customer_id.in_(cust_ids))
    )).scalar() or 0
    if existing >= 10:
        print(f"  Bookings/etc: already seeded ({existing} found), skipped")
        return

    def v(i: int) -> Vehicle: return vehicles[i % len(vehicles)]
    def c(i: int) -> User:    return customers[i % len(customers)]
    def d(i: int) -> Driver:  return drivers[i % len(drivers)]

    daily_fine = Decimal(str(settings.DAILY_FINE_RATE))
    tax_rate   = Decimal(str(settings.TAX_RATE))

    # Invoice number helper (counter avoids duplicate-key inside single flush)
    today_str = date.today().strftime("%Y%m%d")
    inv_prefix = f"INV-{today_str}-"
    inv_base = (await db.execute(
        select(func.count()).select_from(Invoice)
        .where(Invoice.invoice_number.like(f"{inv_prefix}%"))
    )).scalar() or 0
    inv_seq = [inv_base]

    def next_inv() -> str:
        inv_seq[0] += 1
        return f"{inv_prefix}{inv_seq[0]:04d}"

    # ── 5 COMPLETED ────────────────────────────────────────────────────────
    # (cust_idx, veh_idx, drv_idx|None, pickup_off, return_off, actual_off, needs_driver)
    completed_defs = [
        (0,  0,  0,   -90, -85, -85, True),   # on-time,  driver rated
        (1,  5,  1,   -75, -70, -68, True),   # 2d overdue → fine, rated
        (2, 10, None, -60, -55, -55, False),  # on-time,  no driver
        (3, 15,  2,   -45, -40, -37, True),   # 3d overdue → fine, rated
        (4, 20, None, -30, -25, -25, False),  # on-time,  no driver
    ]

    completed_rows: list[tuple] = []
    for ci, vi, di, p_off, r_off, a_off, needs_drv in completed_defs:
        cu, ve = c(ci), v(vi)
        dr = d(di) if di is not None else None
        pickup = _today(p_off);  ret = _today(r_off);  actual = _today(a_off)
        cost   = Decimal((ret - pickup).days) * ve.daily_rate
        bk = Booking(
            customer_id=cu.id, vehicle_id=ve.id,
            driver_id=dr.id if dr else None,
            pickup_date=pickup, return_date=ret, actual_return=actual,
            needs_driver=needs_drv, status=BookingStatus.completed,
            estimated_cost=cost,
            pickup_location="Bengaluru Airport, Terminal 1",
            drop_location="MG Road, Bengaluru",
        )
        db.add(bk)
        completed_rows.append((bk, ve, cu, dr, ret, actual))

    await db.flush()

    for bk, ve, cu, dr, ret, actual in completed_rows:
        overdue  = (actual - ret).days
        fine_amt = Decimal("0.00")
        if overdue > 0:
            fine_amt = Decimal(overdue) * daily_fine
            db.add(Fine(
                booking_id=bk.id, customer_id=cu.id,
                overdue_days=overdue, daily_fine_rate=daily_fine,
                total_amount=fine_amt, status=FineStatus.paid,
                paid_at=datetime.now(timezone.utc),
            ))

        paid_dt = datetime.combine(ret, datetime.min.time()).replace(tzinfo=timezone.utc)
        pmt = Payment(
            booking_id=bk.id, customer_id=cu.id, amount=bk.estimated_cost,
            payment_method=PaymentMethod.card, status=PaymentStatus.completed,
            transaction_ref=f"TXN-{str(bk.id)[:12].upper()}",
            paid_at=paid_dt,
        )
        db.add(pmt)
        await db.flush()

        rental_days = (ret - bk.pickup_date).days
        base = Decimal(rental_days) * ve.daily_rate
        tax  = (base + fine_amt) * tax_rate
        db.add(Invoice(
            booking_id=bk.id, payment_id=pmt.id, invoice_number=next_inv(),
            rental_days=rental_days, daily_rate=ve.daily_rate,
            base_amount=base, fine_amount=fine_amt,
            tax_amount=tax, total_amount=base + fine_amt + tax,
        ))

    # Ratings for completed bookings that had a driver
    rating_defs = [
        # booking list index, rating, review
        (0, 5, "Excellent driver — very punctual and professional!"),
        (1, 4, "Good experience, friendly and safe driver."),
        (3, 5, "Outstanding service, highly recommend Prakash!"),
    ]
    for b_idx, rating, review in rating_defs:
        bk, _, cu, dr, *_ = completed_rows[b_idx]
        if dr:
            db.add(DriverRating(
                driver_id=dr.id, booking_id=bk.id, customer_id=cu.id,
                rating=rating, review=review,
            ))

    await db.flush()

    # ── 3 ACTIVE ───────────────────────────────────────────────────────────
    # (cust_idx, veh_idx, drv_idx|None, pickup_off, return_off, needs_driver)
    for ci, vi, di, p_off, r_off, needs_drv in [
        (5,  1,  3, -10,  5, True),
        (6,  6, None, -7,  8, False),
        (7, 11,  4,  -5, 10, True),
    ]:
        cu, ve = c(ci), v(vi)
        dr = d(di) if di is not None else None
        pickup = _today(p_off); ret = _today(r_off)
        cost   = Decimal((ret - pickup).days) * ve.daily_rate
        bk = Booking(
            customer_id=cu.id, vehicle_id=ve.id,
            driver_id=dr.id if dr else None,
            pickup_date=pickup, return_date=ret, needs_driver=needs_drv,
            status=BookingStatus.active, estimated_cost=cost,
            pickup_location="Kempegowda Bus Stand, Bengaluru",
            drop_location="Electronic City, Bengaluru",
        )
        db.add(bk)
        # Mark vehicle as booked
        ve.status = VehicleStatus.booked

    await db.flush()

    # ── 3 APPROVED (pending payment) ───────────────────────────────────────
    approved_rows: list[tuple] = []
    for ci, vi, di, p_off, r_off, needs_drv in [
        (0,  2,  5,  3,  7, True),
        (1,  7, None, 5, 10, False),
        (2, 12,  6,  8, 14, True),
    ]:
        cu, ve = c(ci), v(vi)
        dr = d(di) if di is not None else None
        pickup = _today(p_off); ret = _today(r_off)
        cost   = Decimal((ret - pickup).days) * ve.daily_rate
        bk = Booking(
            customer_id=cu.id, vehicle_id=ve.id,
            driver_id=dr.id if dr else None,
            pickup_date=pickup, return_date=ret, needs_driver=needs_drv,
            status=BookingStatus.approved, estimated_cost=cost,
            pickup_location="Indiranagar, Bengaluru",
            drop_location="Whitefield, Bengaluru",
        )
        db.add(bk)
        approved_rows.append((bk, cu))

    await db.flush()

    for bk, cu in approved_rows:
        db.add(Payment(
            booking_id=bk.id, customer_id=cu.id, amount=bk.estimated_cost,
            payment_method=PaymentMethod.upi, status=PaymentStatus.pending,
        ))

    await db.flush()

    # ── 4 PENDING ──────────────────────────────────────────────────────────
    for ci, vi, p_off, r_off, needs_drv in [
        (3,  3, 15, 20, True),
        (4,  8, 12, 18, False),
        (5, 13, 10, 17, True),
        (6, 18, 20, 28, False),
    ]:
        cu, ve = c(ci), v(vi)
        pickup = _today(p_off); ret = _today(r_off)
        cost   = Decimal((ret - pickup).days) * ve.daily_rate
        db.add(Booking(
            customer_id=cu.id, vehicle_id=ve.id,
            pickup_date=pickup, return_date=ret, needs_driver=needs_drv,
            status=BookingStatus.pending, estimated_cost=cost,
            pickup_location="Koramangala, Bengaluru",
        ))

    # ── 3 CANCELLED ────────────────────────────────────────────────────────
    for ci, vi, p_off, r_off in [
        (7,  4, -20, -15),
        (0,  9, -35, -28),
        (1, 14, -50, -44),
    ]:
        cu, ve = c(ci), v(vi)
        pickup = _today(p_off); ret = _today(r_off)
        cost   = Decimal((ret - pickup).days) * ve.daily_rate
        db.add(Booking(
            customer_id=cu.id, vehicle_id=ve.id,
            pickup_date=pickup, return_date=ret,
            needs_driver=False, status=BookingStatus.cancelled, estimated_cost=cost,
        ))

    # ── 2 REJECTED ─────────────────────────────────────────────────────────
    for ci, vi, p_off, r_off in [
        (2, 19, -25, -20),
        (3, 24, -40, -33),
    ]:
        cu, ve = c(ci), v(vi)
        pickup = _today(p_off); ret = _today(r_off)
        cost   = Decimal((ret - pickup).days) * ve.daily_rate
        db.add(Booking(
            customer_id=cu.id, vehicle_id=ve.id,
            pickup_date=pickup, return_date=ret,
            needs_driver=False, status=BookingStatus.rejected, estimated_cost=cost,
            admin_notes="Requested vehicle not available for the selected period.",
        ))

    await db.flush()
    print(f"  Bookings/etc: inserted (5 completed, 3 active, 3 approved, 4 pending, 3 cancelled, 2 rejected)")


# ─────────────────────────────────────────────────────────────────────────────
# 5. MAINTENANCE
# ─────────────────────────────────────────────────────────────────────────────

async def _seed_maintenance(db: AsyncSession, vehicles: list[Vehicle]) -> None:
    existing = (await db.execute(select(func.count()).select_from(Maintenance))).scalar() or 0
    if existing >= 5:
        print(f"  Maintenance : already seeded ({existing} records), skipped")
        return

    def v(i: int) -> Vehicle: return vehicles[i % len(vehicles)]

    records = [
        # veh_idx, type, description, sched_off, comp_off|None, cost, performed_by, status
        ( 0, "routine",    "Oil change, oil filter & air filter replacement",     -30, -28, 2500,  "SpeedCare Garage",       "completed"),
        ( 1, "inspection", "Full vehicle safety and roadworthiness inspection",   -20, -18, 1800,  "AutoCheck Hub",          "completed"),
        ( 2, "repair",     "Front brake pad & rotor replacement",                 -10,  -8, 4500,  "BrakeMaster Auto",       "completed"),
        ( 3, "cleaning",   "Deep interior and exterior detailing",                 -5,  -4,  800,  "ShineAuto Detailing",    "completed"),
        ( 4, "routine",    "Tyre rotation, wheel alignment & balancing",          -60, -58, 3200,  "WheelPro Services",      "completed"),
        ( 5, "routine",    "AC service, refrigerant top-up & filter cleaning",    -15, None, 1500, "CoolBreeze AC",          "in_progress"),
        ( 6, "repair",     "Shock absorber replacement & suspension alignment",     5, None, 6000, "SuspensionPro Bengaluru","scheduled"),
        ( 7, "inspection", "Pre-delivery inspection — premium vehicle",             8, None,  900, "AutoCheck Hub",          "scheduled"),
        ( 8, "routine",    "40,000 km major service — full fluid flush",           12, None, 8500, "Authorised Service Ctr", "scheduled"),
        ( 9, "cleaning",   "Post-rental sanitisation and deep clean",               2, None,  750, "ShineAuto Detailing",    "scheduled"),
        (10, "repair",     "Windshield chip repair — deferred, vehicle free",      -8, None, 2200, "GlassFix India",         "cancelled"),
        (11, "routine",    "Battery load test & replacement if needed",            -3, None, 3800, "ElectroAuto Services",   "scheduled"),
    ]

    added = []
    for vi, mtype, desc, s_off, c_off, cost, by, status in records:
        ve = v(vi)
        added.append(Maintenance(
            vehicle_id=ve.id,
            maintenance_type=MaintenanceType(mtype),
            description=desc,
            scheduled_date=_today(s_off),
            completed_date=_today(c_off) if c_off is not None else None,
            cost=Decimal(str(cost)),
            performed_by=by,
            status=MaintenanceStatus(status),
        ))
        # Keep vehicle status consistent for in-progress maintenance
        if status == "in_progress":
            ve.status = VehicleStatus.maintenance

    db.add_all(added)
    await db.flush()
    print(f"  Maintenance : +{len(added)} inserted")


# ─────────────────────────────────────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────────────────────────────────────

async def seed() -> None:
    engine  = create_async_engine(settings.DATABASE_URL, echo=False, future=True)
    Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with Session() as db:
        print("\nSeeding database …\n")

        users   = await _seed_users(db)
        drivers = await _seed_drivers(db)
        vehs    = await _pick_vehicles(db)

        if not vehs:
            print("  ⚠  No vehicles found — run seed_vehicles first!")
        else:
            await _seed_transactions(db, users, drivers, vehs)
            await _seed_maintenance(db, vehs)

        await db.commit()
        print("\nDone ✓\n")
        print("  Login credentials:")
        print("    Admin    → admin@csm.com          / Admin@1234")
        print("    Customer → arjun.sharma@email.com / Customer@1234")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed())
