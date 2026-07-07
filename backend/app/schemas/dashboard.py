from datetime import datetime

from pydantic import BaseModel


class DashboardStats(BaseModel):
    total_companies: int
    total_certificates: int
    total_agents: int
    agents_online: int
    last_execution_at: datetime | None
    next_scheduled_at: datetime | None
    executions_total: int
    executions_running: int
    executions_failed_7d: int
    downloads_total: int
    files_downloaded_7d: int
    avg_execution_seconds: float | None
    expiring_certificates: int


class AuditLogOut(BaseModel):
    id: str
    action: str
    entity: str | None
    entity_id: str | None
    detail: dict
    ip_address: str | None
    created_at: datetime

    model_config = {"from_attributes": True}
