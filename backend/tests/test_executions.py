from httpx import AsyncClient


async def _setup_company_and_cert(client: AsyncClient, auth_headers) -> tuple[str, str]:
    response = await client.post(
        "/api/v1/companies",
        json={"name": "Empresa A", "cnpj": "12.345.678/0001-99"},
        headers=auth_headers,
    )
    company_id = response.json()["id"]
    response = await client.get("/api/v1/certificates", headers=auth_headers)
    certificate_id = response.json()[0]["id"]
    return company_id, certificate_id


async def test_full_execution_flow(client: AsyncClient, auth_headers, enrolled_agent):
    company_id, certificate_id = await _setup_company_and_cert(client, auth_headers)

    # 1) Usuário cria a execução com filtros de período
    response = await client.post(
        "/api/v1/executions",
        json={
            "company_id": company_id,
            "certificate_id": certificate_id,
            "portal": "nfse_nacional",
            "filters": {"start_date": "2026-06-01", "end_date": "2026-06-30"},
        },
        headers=auth_headers,
    )
    assert response.status_code == 201, response.text
    execution = response.json()
    assert execution["status"] == "pending"
    assert execution["agent_id"] == enrolled_agent["agent_id"]

    # 2) Agente busca trabalhos pendentes
    response = await client.get("/api/v1/agents/me/jobs", headers=enrolled_agent["headers"])
    jobs = response.json()
    assert len(jobs) == 1
    job = jobs[0]
    assert job["execution_id"] == execution["id"]
    assert job["certificate_thumbprint"] == "ABCDEF1234567890"
    assert job["filters"]["start_date"] == "2026-06-01"

    # Job despachado não é entregue novamente
    response = await client.get("/api/v1/agents/me/jobs", headers=enrolled_agent["headers"])
    assert response.json() == []

    # 3) Agente inicia, loga progresso e reporta downloads
    response = await client.patch(
        f"/api/v1/agents/me/jobs/{execution['id']}",
        headers=enrolled_agent["headers"],
        json={"status": "running", "logs": [{"message": "Autenticado no portal"}]},
    )
    assert response.status_code == 200

    response = await client.patch(
        f"/api/v1/agents/me/jobs/{execution['id']}",
        headers=enrolled_agent["headers"],
        json={
            "status": "success",
            "downloads": [
                {
                    "file_name": "EmpresaA_20260615_101500_001.xlsx",
                    "original_name": "relatorio.xlsx",
                    "local_path": "C:\\Downloads\\NFSe\\Empresa_A\\EmpresaA_20260615_101500_001.xlsx",
                    "size_bytes": 2048,
                    "sha256": "a" * 64,
                },
                {
                    "file_name": "EmpresaA_20260616_090000_002.xlsx",
                    "local_path": "C:\\Downloads\\NFSe\\Empresa_A\\EmpresaA_20260616_090000_002.xlsx",
                    "size_bytes": 1024,
                },
            ],
            "logs": [{"message": "2 documentos baixados"}],
        },
    )
    assert response.status_code == 200

    # 4) Dashboard vê o resultado
    response = await client.get(f"/api/v1/executions/{execution['id']}", headers=auth_headers)
    body = response.json()
    assert body["status"] == "success"
    assert body["files_count"] == 2
    assert body["started_at"] is not None
    assert body["finished_at"] is not None

    response = await client.get(f"/api/v1/executions/{execution['id']}/downloads", headers=auth_headers)
    assert len(response.json()) == 2

    response = await client.get(f"/api/v1/executions/{execution['id']}/logs", headers=auth_headers)
    assert len(response.json()) == 2

    response = await client.get("/api/v1/dashboard/stats", headers=auth_headers)
    stats = response.json()
    assert stats["downloads_total"] == 2
    assert stats["executions_total"] == 1
    assert stats["total_certificates"] == 1


async def test_cancel_pending_execution(client: AsyncClient, auth_headers, enrolled_agent):
    company_id, certificate_id = await _setup_company_and_cert(client, auth_headers)
    response = await client.post(
        "/api/v1/executions",
        json={
            "company_id": company_id,
            "certificate_id": certificate_id,
            "portal": "nfse_sp",
            "filters": {"start_date": "2026-06-01", "end_date": "2026-06-30"},
        },
        headers=auth_headers,
    )
    execution_id = response.json()["id"]

    response = await client.post(f"/api/v1/executions/{execution_id}/cancel", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"

    # Execução cancelada não é entregue ao agente
    response = await client.get("/api/v1/agents/me/jobs", headers=enrolled_agent["headers"])
    assert response.json() == []


async def test_invalid_date_range_rejected(client: AsyncClient, auth_headers, enrolled_agent):
    company_id, certificate_id = await _setup_company_and_cert(client, auth_headers)
    response = await client.post(
        "/api/v1/executions",
        json={
            "company_id": company_id,
            "certificate_id": certificate_id,
            "portal": "nfse_nacional",
            "filters": {"start_date": "2026-06-30", "end_date": "2026-06-01"},
        },
        headers=auth_headers,
    )
    assert response.status_code == 422
