import uuid
from datetime import date, datetime
from typing import Any

from pydantic import BaseModel, Field, model_validator

from app.models.enums import ExecutionStatus, LogLevel, Portal


class ExecutionFilters(BaseModel):
    start_date: date
    end_date: date
    extra: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def check_range(self) -> "ExecutionFilters":
        if self.end_date < self.start_date:
            raise ValueError("Data final não pode ser anterior à data inicial")
        return self


class ExecutionCreate(BaseModel):
    company_id: uuid.UUID
    certificate_id: uuid.UUID
    portal: Portal
    filters: ExecutionFilters


class ExecutionOut(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    certificate_id: uuid.UUID | None
    agent_id: uuid.UUID | None
    schedule_id: uuid.UUID | None
    portal: Portal
    status: ExecutionStatus
    filters: dict[str, Any]
    attempt: int
    max_attempts: int
    started_at: datetime | None
    finished_at: datetime | None
    files_count: int
    error_message: str | None
    cancel_requested: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ExecutionLogOut(BaseModel):
    id: uuid.UUID
    level: LogLevel
    message: str
    screenshot_path: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class DownloadOut(BaseModel):
    id: uuid.UUID
    execution_id: uuid.UUID
    file_name: str
    original_name: str | None
    local_path: str
    size_bytes: int
    sha256: str | None
    document_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ---- Payloads enviados pelo agente ----

class AgentJobOut(BaseModel):
    """Trabalho entregue ao agente para execução local."""

    execution_id: uuid.UUID
    portal: Portal
    company_name: str
    company_cnpj: str
    certificate_thumbprint: str
    filters: dict[str, Any]
    cancel_requested: bool


class AgentLogEntry(BaseModel):
    level: LogLevel = LogLevel.INFO
    message: str
    screenshot_base64: str | None = None


class AgentDownloadReport(BaseModel):
    file_name: str
    original_name: str | None = None
    local_path: str
    size_bytes: int = 0
    sha256: str | None = None
    document_id: str | None = None


class AgentJobUpdate(BaseModel):
    status: ExecutionStatus | None = None
    logs: list[AgentLogEntry] = Field(default_factory=list)
    downloads: list[AgentDownloadReport] = Field(default_factory=list)
    error_message: str | None = None
