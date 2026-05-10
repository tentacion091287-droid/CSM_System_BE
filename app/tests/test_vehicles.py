import pytest
from httpx import AsyncClient

VEHICLE_PAYLOAD = {
    "make": "Honda",
    "model": "Civic",
    "year": 2023,
    "license_plate": "KA-01-AB-1234",
    "category": "standard",
    "daily_rate": "1200.00",
}


async def test_admin_create_vehicle(client: AsyncClient, admin_headers):
    resp = await client.post("/api/v1/vehicles/", headers=admin_headers, json=VEHICLE_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["make"] == "Honda"
    assert data["status"] == "available"


async def test_customer_cannot_create_vehicle(client: AsyncClient, customer_headers):
    resp = await client.post("/api/v1/vehicles/", headers=customer_headers, json=VEHICLE_PAYLOAD)
    assert resp.status_code == 403


async def test_list_vehicles(client: AsyncClient, vehicle, customer_headers):
    resp = await client.get("/api/v1/vehicles/", headers=customer_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert any(v["id"] == str(vehicle.id) for v in data["items"])


async def test_get_vehicle(client: AsyncClient, vehicle, customer_headers):
    resp = await client.get(f"/api/v1/vehicles/{vehicle.id}", headers=customer_headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == str(vehicle.id)


async def test_get_vehicle_not_found(client: AsyncClient, admin_headers):
    resp = await client.get(
        "/api/v1/vehicles/00000000-0000-0000-0000-000000000000", headers=admin_headers
    )
    assert resp.status_code == 404


async def test_update_vehicle(client: AsyncClient, vehicle, admin_headers):
    resp = await client.put(
        f"/api/v1/vehicles/{vehicle.id}",
        headers=admin_headers,
        json={**VEHICLE_PAYLOAD, "license_plate": "KA-01-AB-9999", "daily_rate": "1500.00"},
    )
    assert resp.status_code == 200
    assert resp.json()["daily_rate"] == "1500.00"


async def test_delete_vehicle(client: AsyncClient, vehicle, admin_headers):
    resp = await client.delete(f"/api/v1/vehicles/{vehicle.id}", headers=admin_headers)
    assert resp.status_code == 204
    # Soft-deleted — should return 404 now
    resp2 = await client.get(f"/api/v1/vehicles/{vehicle.id}", headers=admin_headers)
    assert resp2.status_code == 404


async def test_duplicate_license_plate(client: AsyncClient, admin_headers):
    await client.post("/api/v1/vehicles/", headers=admin_headers, json=VEHICLE_PAYLOAD)
    resp = await client.post("/api/v1/vehicles/", headers=admin_headers, json=VEHICLE_PAYLOAD)
    assert resp.status_code == 400
