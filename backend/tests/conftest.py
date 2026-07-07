import os

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret-key-com-tamanho-suficiente-para-hs256")
os.environ.setdefault("ENVIRONMENT", "test")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.database import Base, get_db
from app.main import app


@pytest_asyncio.fixture
async def db_engine():
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def client(db_engine):
    factory = async_sessionmaker(db_engine, expire_on_commit=False)

    async def override_get_db():
        async with factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Registra uma organização e devolve headers autenticados de admin."""
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "organization_name": "Escritorio Teste",
            "full_name": "Admin Teste",
            "email": "admin@teste.com",
            "password": "senha-super-segura",
        },
    )
    assert response.status_code == 201, response.text
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def enrolled_agent(client: AsyncClient, auth_headers: dict[str, str]) -> dict:
    """Matricula um agente desktop e devolve token + certificado reportado."""
    response = await client.post("/api/v1/agents/enrollment-token", headers=auth_headers)
    assert response.status_code == 200, response.text
    enrollment_token = response.json()["enrollment_token"]

    response = await client.post(
        "/api/v1/agents/enroll",
        json={
            "enrollment_token": enrollment_token,
            "name": "PC-CONTABILIDADE",
            "machine_id": "machine-abc-123",
            "version": "1.0.0",
            "downloads_dir": "C:\\Downloads\\NFSe",
        },
    )
    assert response.status_code == 201, response.text
    data = response.json()
    agent_headers = {"X-Agent-Token": data["agent_token"]}

    response = await client.put(
        "/api/v1/agents/me/certificates",
        headers=agent_headers,
        json=[
            {
                "thumbprint": "ABCDEF1234567890",
                "subject": "CN=EMPRESA TESTE LTDA:12345678000199",
                "issuer": "CN=AC Certisign",
                "cnpj_cpf": "12345678000199",
                "certificate_type": "A1",
                "not_before": "2026-01-01T00:00:00Z",
                "not_after": "2027-01-01T00:00:00Z",
            }
        ],
    )
    assert response.status_code == 200, response.text
    return {"agent_id": data["agent_id"], "headers": agent_headers}
