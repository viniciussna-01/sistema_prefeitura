import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import Portal

_CNPJ_ALLOWED = set("0123456789./-")


class CompanyBase(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    cnpj: str = Field(min_length=11, max_length=18)
    municipal_registration: str | None = None
    default_portal: Portal = Portal.NFSE_NACIONAL
    is_active: bool = True

    @field_validator("cnpj")
    @classmethod
    def validate_cnpj(cls, v: str) -> str:
        if not set(v) <= _CNPJ_ALLOWED:
            raise ValueError("CNPJ contém caracteres inválidos")
        digits = "".join(c for c in v if c.isdigit())
        if len(digits) not in (11, 14):
            raise ValueError("CNPJ/CPF deve conter 11 ou 14 dígitos")
        return v


class CompanyCreate(CompanyBase):
    pass


class CompanyUpdate(BaseModel):
    name: str | None = None
    cnpj: str | None = None
    municipal_registration: str | None = None
    default_portal: Portal | None = None
    is_active: bool | None = None


class CompanyOut(CompanyBase):
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
