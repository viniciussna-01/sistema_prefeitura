import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
from app.models.enums import Portal


class Schedule(Base, UUIDMixin, TimestampMixin):
    """Agendamento recorrente de automação (expressão cron de 5 campos)."""

    __tablename__ = "schedules"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    certificate_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("certificates.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    portal: Mapped[Portal] = mapped_column(Enum(Portal))
    cron_expression: Mapped[str] = mapped_column(String(100))
    # Filtros dinâmicos; datas relativas em dias (ex.: últimos 7 dias)
    filters: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    next_run_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True, index=True
    )
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
