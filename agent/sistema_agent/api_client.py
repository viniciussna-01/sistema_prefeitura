"""Cliente HTTP do agente para o backend (HTTPS + token de agente)."""

import base64
from typing import Any

import httpx

from sistema_agent import __version__
from sistema_agent.config import AgentConfig


class ApiClient:
    def __init__(self, config: AgentConfig):
        self.config = config
        self._client = httpx.Client(base_url=f"{config.api_url}/api/v1", timeout=30)

    def _headers(self) -> dict[str, str]:
        return {"X-Agent-Token": self.config.agent_token}

    # ---- Matrícula ----

    def enroll(self, enrollment_token: str, name: str) -> dict[str, Any]:
        response = self._client.post(
            "/agents/enroll",
            json={
                "enrollment_token": enrollment_token,
                "name": name,
                "machine_id": self.config.machine_id,
                "version": __version__,
                "downloads_dir": self.config.downloads_dir,
            },
        )
        response.raise_for_status()
        return response.json()

    # ---- Ciclo de vida ----

    def heartbeat(self) -> None:
        self._client.post(
            "/agents/me/heartbeat",
            headers=self._headers(),
            json={"version": __version__, "downloads_dir": self.config.downloads_dir},
        ).raise_for_status()

    def report_certificates(self, reports: list[dict[str, Any]]) -> None:
        self._client.put(
            "/agents/me/certificates", headers=self._headers(), json=reports
        ).raise_for_status()

    def poll_jobs(self) -> list[dict[str, Any]]:
        response = self._client.get("/agents/me/jobs", headers=self._headers())
        response.raise_for_status()
        return response.json()

    def update_job(
        self,
        execution_id: str,
        *,
        status: str | None = None,
        logs: list[dict[str, Any]] | None = None,
        downloads: list[dict[str, Any]] | None = None,
        error_message: str | None = None,
    ) -> dict[str, Any]:
        response = self._client.patch(
            f"/agents/me/jobs/{execution_id}",
            headers=self._headers(),
            json={
                "status": status,
                "logs": logs or [],
                "downloads": downloads or [],
                "error_message": error_message,
            },
        )
        response.raise_for_status()
        return response.json()

    def log(self, execution_id: str, message: str, level: str = "info", screenshot: bytes | None = None) -> None:
        entry: dict[str, Any] = {"level": level, "message": message}
        if screenshot is not None:
            entry["screenshot_base64"] = base64.b64encode(screenshot).decode()
        self.update_job(execution_id, logs=[entry])

    def latest_version(self) -> dict[str, Any]:
        response = self._client.get("/agents/version")
        response.raise_for_status()
        return response.json()
