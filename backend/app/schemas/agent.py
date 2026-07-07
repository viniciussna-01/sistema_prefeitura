import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.enums import AgentStatus, CertificateType


class AgentEnrollRequest(BaseModel):
    """Enviado pelo agente desktop no primeiro registro, usando um
    token de matrícula gerado pelo administrador no dashboard."""

    enrollment_token: str
    name: str = Field(max_length=255)
    machine_id: str = Field(max_length=255)
    version: str = Field(max_length=20)
    downloads_dir: str | None = None


class AgentEnrollResponse(BaseModel):
    agent_id: uuid.UUID
    agent_token: str


class AgentOut(BaseModel):
    id: uuid.UUID
    name: str
    machine_id: str
    version: str
    last_seen_at: datetime | None
    downloads_dir: str | None
    status: AgentStatus = AgentStatus.OFFLINE

    model_config = {"from_attributes": True}


class HeartbeatRequest(BaseModel):
    version: str | None = None
    downloads_dir: str | None = None


class CertificateReport(BaseModel):
    """Metadados de um certificado visível no repositório do Windows.
    A chave privada nunca é transmitida."""

    thumbprint: str = Field(max_length=64)
    subject: str = Field(max_length=500)
    issuer: str = Field(max_length=500)
    cnpj_cpf: str | None = None
    certificate_type: CertificateType = CertificateType.A1
    not_before: datetime | None = None
    not_after: datetime | None = None


class CertificateOut(BaseModel):
    id: uuid.UUID
    agent_id: uuid.UUID
    thumbprint: str
    subject: str
    issuer: str
    cnpj_cpf: str | None
    certificate_type: CertificateType
    not_before: datetime | None
    not_after: datetime | None
    is_active: bool

    model_config = {"from_attributes": True}


class EnrollmentTokenResponse(BaseModel):
    enrollment_token: str
    expires_in_seconds: int
