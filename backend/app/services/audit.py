import uuid
from typing import Any

from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditLog


async def record_audit(
    db: AsyncSession,
    *,
    action: str,
    organization_id: uuid.UUID | None = None,
    user_id: uuid.UUID | None = None,
    agent_id: uuid.UUID | None = None,
    entity: str | None = None,
    entity_id: str | None = None,
    detail: dict[str, Any] | None = None,
    request: Request | None = None,
) -> None:
    """Registra um evento de auditoria. Não faz commit — participa da transação do chamador."""
    ip = None
    if request is not None and request.client is not None:
        ip = request.client.host
    db.add(
        AuditLog(
            action=action,
            organization_id=organization_id,
            user_id=user_id,
            agent_id=agent_id,
            entity=entity,
            entity_id=entity_id,
            detail=detail or {},
            ip_address=ip,
        )
    )
