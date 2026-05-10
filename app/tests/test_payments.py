import pytest
from httpx import AsyncClient


async def _initiate(client, booking_id, customer_headers):
    return await client.post("/api/v1/payments/", headers=customer_headers, json={
        "booking_id": booking_id,
        "payment_method": "card",
    })


async def test_initiate_payment(client: AsyncClient, approved_booking, customer_headers):
    resp = await _initiate(client, str(approved_booking.id), customer_headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["status"] == "pending"
    assert data["booking_id"] == str(approved_booking.id)


async def test_process_payment_creates_invoice(
    client: AsyncClient, approved_booking, customer_headers, admin_headers
):
    pay = await _initiate(client, str(approved_booking.id), customer_headers)
    payment_id = pay.json()["id"]
    booking_id = str(approved_booking.id)

    resp = await client.patch(f"/api/v1/payments/{payment_id}/process", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "completed"

    inv_resp = await client.get(f"/api/v1/invoices/booking/{booking_id}", headers=customer_headers)
    assert inv_resp.status_code == 200
    inv = inv_resp.json()
    assert inv["booking_id"] == booking_id
    assert inv["invoice_number"].startswith("INV-")
    assert float(inv["total_amount"]) > 0


async def test_duplicate_payment_rejected(
    client: AsyncClient, approved_booking, customer_headers
):
    await _initiate(client, str(approved_booking.id), customer_headers)
    resp = await _initiate(client, str(approved_booking.id), customer_headers)
    assert resp.status_code == 409


async def test_refund_payment(
    client: AsyncClient, approved_booking, customer_headers, admin_headers
):
    pay = await _initiate(client, str(approved_booking.id), customer_headers)
    payment_id = pay.json()["id"]
    await client.patch(f"/api/v1/payments/{payment_id}/process", headers=admin_headers)
    resp = await client.patch(f"/api/v1/payments/{payment_id}/refund", headers=admin_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "refunded"


async def test_my_payments(client: AsyncClient, approved_booking, customer_headers):
    await _initiate(client, str(approved_booking.id), customer_headers)
    resp = await client.get("/api/v1/payments/my", headers=customer_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_customer_cannot_process_payment(
    client: AsyncClient, approved_booking, customer_headers
):
    pay = await _initiate(client, str(approved_booking.id), customer_headers)
    payment_id = pay.json()["id"]
    resp = await client.patch(f"/api/v1/payments/{payment_id}/process", headers=customer_headers)
    assert resp.status_code == 403
