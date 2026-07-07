from datetime import date, datetime, timezone

from httpx import AsyncClient

from app.services.schedules import compute_next_run, resolve_schedule_filters


def test_compute_next_run_daily():
    base = datetime(2026, 7, 7, 10, 0, tzinfo=timezone.utc)
    next_run = compute_next_run("0 8 * * *", base)
    assert next_run == datetime(2026, 7, 8, 8, 0, tzinfo=timezone.utc)


def test_compute_next_run_monthly_first_day():
    base = datetime(2026, 7, 7, 10, 0, tzinfo=timezone.utc)
    next_run = compute_next_run("0 6 1 * *", base)
    assert next_run == datetime(2026, 8, 1, 6, 0, tzinfo=timezone.utc)


def test_resolve_schedule_filters_period():
    filters = resolve_schedule_filters({"period_days": 7}, today=date(2026, 7, 7))
    assert filters["start_date"] == "2026-06-30"
    assert filters["end_date"] == "2026-07-07"


async def test_schedule_crud_and_cron_validation(client: AsyncClient, auth_headers, enrolled_agent):
    response = await client.post(
        "/api/v1/companies",
        json={"name": "Empresa A", "cnpj": "12.345.678/0001-99"},
        headers=auth_headers,
    )
    company_id = response.json()["id"]
    response = await client.get("/api/v1/certificates", headers=auth_headers)
    certificate_id = response.json()[0]["id"]

    payload = {
        "name": "Diário às 08:00",
        "company_id": company_id,
        "certificate_id": certificate_id,
        "portal": "nfse_nacional",
        "cron_expression": "0 8 * * *",
        "filters": {"period_days": 1},
    }
    response = await client.post("/api/v1/schedules", json=payload, headers=auth_headers)
    assert response.status_code == 201, response.text
    schedule = response.json()
    assert schedule["next_run_at"] is not None

    # Cron inválido é rejeitado
    response = await client.post(
        "/api/v1/schedules",
        json={**payload, "cron_expression": "isso não é cron"},
        headers=auth_headers,
    )
    assert response.status_code == 422

    response = await client.patch(
        f"/api/v1/schedules/{schedule['id']}", json={"enabled": False}, headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["enabled"] is False

    response = await client.delete(f"/api/v1/schedules/{schedule['id']}", headers=auth_headers)
    assert response.status_code == 204
