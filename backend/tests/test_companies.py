from httpx import AsyncClient

COMPANY = {
    "name": "Empresa A",
    "cnpj": "12.345.678/0001-99",
    "default_portal": "nfse_sp",
}


async def test_company_crud(client: AsyncClient, auth_headers):
    response = await client.post("/api/v1/companies", json=COMPANY, headers=auth_headers)
    assert response.status_code == 201, response.text
    company = response.json()
    assert company["name"] == "Empresa A"

    response = await client.get("/api/v1/companies", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = await client.patch(
        f"/api/v1/companies/{company['id']}",
        json={"name": "Empresa A Renomeada"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Empresa A Renomeada"

    response = await client.delete(f"/api/v1/companies/{company['id']}", headers=auth_headers)
    assert response.status_code == 204

    response = await client.get("/api/v1/companies", headers=auth_headers)
    assert response.json() == []


async def test_invalid_cnpj_rejected(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/companies",
        json={"name": "Empresa X", "cnpj": "123"},
        headers=auth_headers,
    )
    assert response.status_code == 422


async def test_org_isolation(client: AsyncClient, auth_headers):
    await client.post("/api/v1/companies", json=COMPANY, headers=auth_headers)

    # Outra organização não enxerga as empresas da primeira
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Org Concorrente",
            "full_name": "Fulano",
            "email": "fulano@concorrente.com",
            "password": "senha-forte-123",
        },
    )
    other_headers = {"Authorization": f"Bearer {response.json()['access_token']}"}
    response = await client.get("/api/v1/companies", headers=other_headers)
    assert response.json() == []
