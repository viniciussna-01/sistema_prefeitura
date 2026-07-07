from httpx import AsyncClient


async def _create_user_with_role(client: AsyncClient, admin_headers, email: str, role: str) -> dict:
    response = await client.post(
        "/api/v1/users",
        json={"full_name": "Usuario", "email": email, "password": "senha-forte-123", "role": role},
        headers=admin_headers,
    )
    assert response.status_code == 201, response.text
    response = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "senha-forte-123"}
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


async def test_viewer_cannot_write(client: AsyncClient, auth_headers):
    viewer_headers = await _create_user_with_role(client, auth_headers, "viewer@teste.com", "viewer")

    response = await client.post(
        "/api/v1/companies",
        json={"name": "Empresa", "cnpj": "12.345.678/0001-99"},
        headers=viewer_headers,
    )
    assert response.status_code == 403

    # Mas pode ler
    response = await client.get("/api/v1/companies", headers=viewer_headers)
    assert response.status_code == 200


async def test_operator_cannot_manage_users(client: AsyncClient, auth_headers):
    operator_headers = await _create_user_with_role(
        client, auth_headers, "operator@teste.com", "operator"
    )
    response = await client.post(
        "/api/v1/users",
        json={
            "full_name": "Intruso",
            "email": "intruso@teste.com",
            "password": "senha-forte-123",
            "role": "admin",
        },
        headers=operator_headers,
    )
    assert response.status_code == 403


async def test_operator_can_create_company(client: AsyncClient, auth_headers):
    operator_headers = await _create_user_with_role(
        client, auth_headers, "operator2@teste.com", "operator"
    )
    response = await client.post(
        "/api/v1/companies",
        json={"name": "Empresa Op", "cnpj": "12.345.678/0001-99"},
        headers=operator_headers,
    )
    assert response.status_code == 201
