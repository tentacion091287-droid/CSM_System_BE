import pytest
from httpx import AsyncClient


async def test_dashboard_admin_only(client: AsyncClient, admin_headers, customer_headers):
    resp = await client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert resp.status_code == 200

    resp_cust = await client.get("/api/v1/admin/dashboard", headers=customer_headers)
    assert resp_cust.status_code == 403


async def test_dashboard_shape(client: AsyncClient, admin_headers):
    resp = await client.get("/api/v1/admin/dashboard", headers=admin_headers)
    data = resp.json()

    for key in ("bookings", "vehicles", "drivers", "revenue", "payments", "fines", "maintenance", "monthly_revenue"):
        assert key in data, f"missing key: {key}"

    assert "total" in data["bookings"]
    assert "total" in data["vehicles"]
    assert "total" in data["revenue"]
    assert "pending_count" in data["fines"]
    assert isinstance(data["monthly_revenue"], list)


async def test_dashboard_counts_reflect_data(
    client: AsyncClient, vehicle, admin_headers, customer_headers
):
    # One vehicle exists from the fixture — should show up in vehicles total
    resp = await client.get("/api/v1/admin/dashboard", headers=admin_headers)
    data = resp.json()
    assert data["vehicles"]["total"] >= 1
    assert data["vehicles"]["available"] >= 1

    # Create a booking → pending count goes up
    from datetime import date, timedelta
    await client.post("/api/v1/bookings/", headers=customer_headers, json={
        "vehicle_id": str(vehicle.id),
        "pickup_date": (date.today() + timedelta(days=1)).isoformat(),
        "return_date": (date.today() + timedelta(days=4)).isoformat(),
    })
    resp2 = await client.get("/api/v1/admin/dashboard", headers=admin_headers)
    data2 = resp2.json()
    assert data2["bookings"]["pending"] >= 1


async def test_dashboard_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/admin/dashboard")
    assert resp.status_code == 403
