import pytest
from datetime import date, timedelta
from httpx import AsyncClient


def _future(days: int) -> str:
    return (date.today() + timedelta(days=days)).isoformat()


async def test_create_booking(client: AsyncClient, vehicle, customer_headers):
    resp = await client.post("/api/v1/bookings/", headers=customer_headers, json={
        "vehicle_id": str(vehicle.id),
        "pickup_date": _future(2),
        "return_date": _future(5),
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert data["vehicle_id"] == str(vehicle.id)


async def test_approve_booking(client: AsyncClient, vehicle, customer_headers, admin_headers):
    create = await client.post("/api/v1/bookings/", headers=customer_headers, json={
        "vehicle_id": str(vehicle.id),
        "pickup_date": _future(2),
        "return_date": _future(5),
    })
    booking_id = create.json()["id"]

    resp = await client.patch(f"/api/v1/bookings/{booking_id}/approve", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "approved"


async def test_activate_booking(client: AsyncClient, vehicle, customer_headers, admin_headers):
    create = await client.post("/api/v1/bookings/", headers=customer_headers, json={
        "vehicle_id": str(vehicle.id),
        "pickup_date": _future(2),
        "return_date": _future(5),
    })
    booking_id = create.json()["id"]
    await client.patch(f"/api/v1/bookings/{booking_id}/approve", headers=admin_headers)
    resp = await client.patch(f"/api/v1/bookings/{booking_id}/activate", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


async def test_complete_booking_on_time(client: AsyncClient, vehicle, customer_headers, admin_headers):
    return_date = _future(3)
    create = await client.post("/api/v1/bookings/", headers=customer_headers, json={
        "vehicle_id": str(vehicle.id),
        "pickup_date": _future(1),
        "return_date": return_date,
    })
    bid = create.json()["id"]
    await client.patch(f"/api/v1/bookings/{bid}/approve", headers=admin_headers)
    await client.patch(f"/api/v1/bookings/{bid}/activate", headers=admin_headers)
    resp = await client.patch(f"/api/v1/bookings/{bid}/complete", headers=admin_headers, json={
        "actual_return": return_date
    })
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"


async def test_cancel_booking(client: AsyncClient, vehicle, customer_headers):
    create = await client.post("/api/v1/bookings/", headers=customer_headers, json={
        "vehicle_id": str(vehicle.id),
        "pickup_date": _future(2),
        "return_date": _future(5),
    })
    booking_id = create.json()["id"]
    resp = await client.delete(f"/api/v1/bookings/{booking_id}", headers=customer_headers)
    assert resp.status_code == 204


async def test_reject_booking(client: AsyncClient, vehicle, customer_headers, admin_headers):
    create = await client.post("/api/v1/bookings/", headers=customer_headers, json={
        "vehicle_id": str(vehicle.id),
        "pickup_date": _future(2),
        "return_date": _future(5),
    })
    booking_id = create.json()["id"]
    resp = await client.patch(
        f"/api/v1/bookings/{booking_id}/reject",
        headers=admin_headers,
        json={"admin_notes": "Fleet full"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "rejected"


async def test_customer_cannot_approve(client: AsyncClient, vehicle, customer_headers):
    create = await client.post("/api/v1/bookings/", headers=customer_headers, json={
        "vehicle_id": str(vehicle.id),
        "pickup_date": _future(2),
        "return_date": _future(5),
    })
    booking_id = create.json()["id"]
    resp = await client.patch(f"/api/v1/bookings/{booking_id}/approve", headers=customer_headers)
    assert resp.status_code == 403


async def test_list_bookings_customer_sees_own(
    client: AsyncClient, vehicle, customer_headers, admin_headers
):
    await client.post("/api/v1/bookings/", headers=customer_headers, json={
        "vehicle_id": str(vehicle.id),
        "pickup_date": _future(2),
        "return_date": _future(5),
    })
    resp = await client.get("/api/v1/bookings/", headers=customer_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1
