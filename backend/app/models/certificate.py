import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
from app.models.enums import CertificateType


class Certificate(Base, UUIDMixin, TimestampMixin):
    """Somente METADADOS do certificado digital.

    A chave privada NUNCA sai da máquina do cliente: o agente desktop apenas
    reporta os certificados visíveis no repositório do Windows e os utiliza
    localmente via APIs do sistema operacional.
    """

    __tablename__ = "certificates"
    __table_args__ = (UniqueConstraint("agent_id", "thumbprint", name="uq_cert_agent_thumbprint"),)

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    agent_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("agents.id", ondelete="CASCADE"), index=True
    )
    thumbprint: Mapped[str] = mapped_column(String(64), index=True)
    subject: Mapped[str] = mapped_column(String(500))
    issuer: Mapped[str] = mapped_column(String(500))
    cnpj_cpf: Mapped[str | None] = mapped_column(String(18), nullable=True)
    certificate_type: Mapped[CertificateType] = mapped_column(
        Enum(CertificateType), default=CertificateType.A1
    )
    not_before: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    not_after: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
