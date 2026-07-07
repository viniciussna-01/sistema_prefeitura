from httpx import AsyncClient


async def test_register_login_me(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Minha Contabilidade",
            "full_name": "Maria Silva",
            "email": "maria@exemplo.com",
            "password": "senha-forte-123",
        },
    )
    assert response.status_code == 201
    assert "access_token" in response.json()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "maria@exemplo.com", "password": "senha-forte-123"},
    )
    assert response.status_code == 200
    tokens = response.json()

    response = await client.get(
        "/api/v1/auth/me", headers={"Authorization": f"Bearer {tokens['access_token']}"}
    )
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "maria@exemplo.com"
    assert body["role"] == "admin"


async def test_login_wrong_password(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@teste.com", "password": "senha-errada-123"},
    )
    assert response.status_code == 401


async def test_duplicate_email_rejected(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Outra Org",
            "full_name": "Outro Nome",
            "email": "admin@teste.com",
            "password": "senha-qualquer-1",
        },
    )
    assert response.status_code == 409


async def test_refresh_token(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Org Refresh",
            "full_name": "Nome",
            "email": "refresh@teste.com",
            "password": "senha-forte-123",
        },
    )
    refresh_token = response.json()["refresh_token"]
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert response.status_code == 200
    assert "access_token" in response.json()

    # Access token não pode ser usado como refresh
    access = response.json()["access_token"]
    response = await client.post("/api/v1/auth/refresh", json={"refresh_token": access})
    assert response.status_code == 401


async def test_me_requires_token(client: AsyncClient):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
