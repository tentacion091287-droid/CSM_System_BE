import pytest
from datetime import date, timedelta
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking, BookingStatus
from app.models.fine import Fine, FineStatus
from app.models.vehicle import Vehicle, VehicleStatus


# ── Fines ──────────────────────────────────────────────────────────────────────

async def _make_late_booking(db: AsyncSession, customer_user, vehicle):
    b = Booking(
        customer_id=customer_user.id,
        vehicle_id=vehicle.id,
        pickup_date=date.today() - timedelta(days=7),
        return_date=date.today() - timedelta(days=4),
        actual_return=date.today() - timedelta(days=1),  # 3 days late
        status=BookingStatus.completed,
        estimated_cost=Decimal("3000.00"),
    )
    db.add(b)
    await db.flush()  # get DB-generated UUID for b.id
    fine = Fine(
        booking_id=b.id,
        customer_id=customer_user.id,
        overdue_days=3,
        daily_fine_rate=Decimal("500.00"),
        total_amount=Decimal("1500.00"),
        status=FineStatus.pending,
    )
    db.add(fine)
    await db.commit()
    await db.refresh(fine)
    return b, fine


async def test_admin_can_waive_fine(
    client: AsyncClient, db: AsyncSession, customer_user, vehicle, admin_headers
):
    _, fine = await _make_late_booking(db, customer_user, vehicle)
    resp = await client.patch(f"/api/v1/fines/{fine.id}/waive", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "waived"


async def test_customer_can_pay_fine(
    client: AsyncClient, db: AsyncSession, customer_user, vehicle, customer_headers
):
    _, fine = await _make_late_booking(db, customer_user, vehicle)
    resp = await client.patch(f"/api/v1/fines/{fine.id}/pay", headers=customer_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "paid"


async def test_customer_cannot_waive_fine(
    client: AsyncClient, db: AsyncSession, customer_user, vehicle, customer_headers
):
    _, fine = await _make_late_booking(db, customer_user, vehicle)
    resp = await client.patch(f"/api/v1/fines/{fine.id}/waive", headers=customer_headers)
    assert resp.status_code == 403


async def test_my_fines(
    client: AsyncClient, db: AsyncSession, customer_user, vehicle, customer_headers
):
    await _make_late_booking(db, customer_user, vehicle)
    resp = await client.get("/api/v1/fines/my", headers=customer_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


# ── Maintenance ────────────────────────────────────────────────────────────────

async def test_schedule_maintenance(
    client: AsyncClient, vehicle, admin_headers
):
    from datetime import date
    resp = await client.post("/api/v1/maintenance/", headers=admin_headers, json={
        "vehicle_id": str(vehicle.id),
        "scheduled_date": date.today().isoformat(),
        "maintenance_type": "routine",
        "description": "Oil change",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "scheduled"
    assert data["vehicle_id"] == str(vehicle.id)


async def test_complete_maintenance_frees_vehicle(
    client: AsyncClient, vehicle, admin_headers
):
    from datetime import date
    sched = await client.post("/api/v1/maintenance/", headers=admin_headers, json={
        "vehicle_id": str(vehicle.id),
        "scheduled_date": date.today().isoformat(),
    })
    record_id = sched.json()["id"]
    resp = await client.patch(
        f"/api/v1/maintenance/{record_id}/complete",
        headers=admin_headers,
        json={"completed_date": date.today().isoformat(), "cost": "5000.00"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"

    veh_resp = await client.get(f"/api/v1/vehicles/{vehicle.id}", headers=admin_headers)
    assert veh_resp.json()["status"] == "available"


async def test_cancel_maintenance_frees_vehicle(
    client: AsyncClient, vehicle, admin_headers
):
    from datetime import date
    sched = await client.post("/api/v1/maintenance/", headers=admin_headers, json={
        "vehicle_id": str(vehicle.id),
        "scheduled_date": date.today().isoformat(),
    })
    record_id = sched.json()["id"]
    resp = await client.patch(f"/api/v1/maintenance/{record_id}/cancel", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "cancelled"


async def test_cannot_double_schedule_vehicle(
    client: AsyncClient, vehicle, admin_headers
):
    from datetime import date
    payload = {"vehicle_id": str(vehicle.id), "scheduled_date": date.today().isoformat()}
    await client.post("/api/v1/maintenance/", headers=admin_headers, json=payload)
    resp = await client.post("/api/v1/maintenance/", headers=admin_headers, json=payload)
    assert resp.status_code == 409


# ── Driver Ratings ─────────────────────────────────────────────────────────────

async def test_submit_rating(
    client: AsyncClient, completed_booking_with_driver, customer_headers
):
    b = completed_booking_with_driver
    resp = await client.post("/api/v1/drivers/ratings", headers=customer_headers, json={
        "driver_id": str(b.driver_id),
        "booking_id": str(b.id),
        "rating": 5,
        "review": "Excellent!",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["rating"] == 5
    assert data["driver_id"] == str(b.driver_id)


async def test_duplicate_rating_rejected(
    client: AsyncClient, completed_booking_with_driver, customer_headers
):
    b = completed_booking_with_driver
    payload = {"driver_id": str(b.driver_id), "booking_id": str(b.id), "rating": 4}
    await client.post("/api/v1/drivers/ratings", headers=customer_headers, json=payload)
    resp = await client.post("/api/v1/drivers/ratings", headers=customer_headers, json=payload)
    assert resp.status_code == 409


async def test_rating_out_of_range(
    client: AsyncClient, completed_booking_with_driver, customer_headers
):
    b = completed_booking_with_driver
    resp = await client.post("/api/v1/drivers/ratings", headers=customer_headers, json={
        "driver_id": str(b.driver_id),
        "booking_id": str(b.id),
        "rating": 6,
    })
    assert resp.status_code == 422


async def test_list_driver_ratings(
    client: AsyncClient, completed_booking_with_driver, customer_headers
):
    b = completed_booking_with_driver
    await client.post("/api/v1/drivers/ratings", headers=customer_headers, json={
        "driver_id": str(b.driver_id),
        "booking_id": str(b.id),
        "rating": 4,
    })
    resp = await client.get(f"/api/v1/drivers/{b.driver_id}/ratings", headers=customer_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["rating"] == 4
