import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin
from app.models.enums import Portal


class Company(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "companies"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    cnpj: Mapped[str] = mapped_column(String(18), index=True)
    municipal_registration: Mapped[str | None] = mapped_column(String(50), nullable=True)
    default_portal: Mapped[Portal] = mapped_column(Enum(Portal), default=Portal.NFSE_NACIONAL)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
