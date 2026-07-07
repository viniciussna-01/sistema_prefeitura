import uuid
from datetime import datetime
from typing import Any

from croniter import croniter
from pydantic import BaseModel, Field, field_validator

from app.models.enums import Portal


class ScheduleBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    company_id: uuid.UUID
    certificate_id: uuid.UUID
    portal: Portal
    cron_expression: str
    # Ex.: {"period_days": 7, "extra": {...}} — a janela de datas é calculada
    # no momento da execução (últimos N dias).
    filters: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v: str) -> str:
        if not croniter.is_valid(v):
            raise ValueError("Expressão cron inválida (use 5 campos: min hora dia mês dia-da-semana)")
        return v


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    name: str | None = None
    cron_expression: str | None = None
    filters: dict[str, Any] | None = None
    enabled: bool | None = None

    @field_validator("cron_expression")
    @classmethod
    def validate_cron(cls, v: str | None) -> str | None:
        if v is not None and not croniter.is_valid(v):
            raise ValueError("Expressão cron inválida")
        return v


class ScheduleOut(ScheduleBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    next_run_at: datetime | None
    last_run_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
