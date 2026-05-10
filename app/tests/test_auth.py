import pytest
from httpx import AsyncClient


async def test_register_success(client: AsyncClient):
    resp = await client.post("/api/v1/auth/register", json={
        "email": "new@test.com",
        "password": "Pass@123",
        "full_name": "New User",
    })
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@test.com"
    assert data["role"] == "customer"


async def test_register_duplicate_email(client: AsyncClient):
    payload = {"email": "dup@test.com", "password": "Pass@123", "full_name": "Dup"}
    await client.post("/api/v1/auth/register", json=payload)
    resp = await client.post("/api/v1/auth/register", json=payload)
    assert resp.status_code == 400


async def test_login_success(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "login@test.com", "password": "Pass@123", "full_name": "Login User"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "login@test.com", "password": "Pass@123"
    })
    assert resp.status_code == 200
    assert "access_token" in resp.json()


async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "wp@test.com", "password": "Pass@123", "full_name": "WP"
    })
    resp = await client.post("/api/v1/auth/login", json={
        "email": "wp@test.com", "password": "WrongPass"
    })
    assert resp.status_code == 401


async def test_get_me(client: AsyncClient, customer_headers):
    resp = await client.get("/api/v1/auth/me", headers=customer_headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "customer@test.com"


async def test_get_me_unauthenticated(client: AsyncClient):
    resp = await client.get("/api/v1/auth/me")
    assert resp.status_code == 403


async def test_update_profile(client: AsyncClient, customer_headers):
    resp = await client.put("/api/v1/auth/me", headers=customer_headers, json={
        "full_name": "Updated Name"
    })
    assert resp.status_code == 200
    assert resp.json()["full_name"] == "Updated Name"


async def test_validation_error_shape(client: AsyncClient):
    resp = await client.post("/api/v1/auth/login", json={"email": "not-an-email", "password": "x"})
    assert resp.status_code == 422
    body = resp.json()
    assert "detail" in body
    assert isinstance(body["detail"], list)
    assert "field" in body["detail"][0]
    assert "message" in body["detail"][0]
