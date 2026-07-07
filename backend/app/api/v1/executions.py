import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_operator
from app.models import (
    Certificate,
    Company,
    Download,
    Execution,
    ExecutionLog,
    ExecutionStatus,
    User,
)
from app.schemas.execution import (
    DownloadOut,
    ExecutionCreate,
    ExecutionLogOut,
    ExecutionOut,
)
from app.services.audit import record_audit
from app.core.config import settings

router = APIRouter(prefix="/executions", tags=["executions"])


async def _get_execution(db: AsyncSession, org_id: uuid.UUID, execution_id: uuid.UUID) -> Execution:
    execution = await db.get(Execution, execution_id)
    if execution is None or execution.organization_id != org_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Execução não encontrada")
    return execution


@router.get("", response_model=list[ExecutionOut])
async def list_executions(
    status_filter: ExecutionStatus | None = None,
    company_id: uuid.UUID | None = None,
    limit: int = 50,
    offset: int = 0,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Execution).where(Execution.organization_id == user.organization_id)
    if status_filter is not None:
        query = query.where(Execution.status == status_filter)
    if company_id is not None:
        query = query.where(Execution.company_id == company_id)
    query = query.order_by(Execution.created_at.desc()).limit(min(limit, 200)).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.post("", response_model=ExecutionOut, status_code=status.HTTP_201_CREATED)
async def create_execution(
    payload: ExecutionCreate,
    request: Request,
    user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    company = await db.get(Company, payload.company_id)
    if company is None or company.organization_id != user.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Empresa não encontrada")

    certificate = await db.get(Certificate, payload.certificate_id)
    if certificate is None or certificate.organization_id != user.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Certificado não encontrado")
    if not certificate.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Certificado inativo neste agente")

    execution = Execution(
        organization_id=user.organization_id,
        company_id=company.id,
        certificate_id=certificate.id,
        agent_id=certificate.agent_id,
        triggered_by_user_id=user.id,
        portal=payload.portal,
        filters={
            "start_date": payload.filters.start_date.isoformat(),
            "end_date": payload.filters.end_date.isoformat(),
            "extra": payload.filters.extra,
        },
        max_attempts=settings.execution_max_attempts,
    )
    db.add(execution)
    await db.flush()
    await record_audit(
        db,
        action="execution.create",
        organization_id=user.organization_id,
        user_id=user.id,
        entity="execution",
        entity_id=str(execution.id),
        detail={
            "company": company.name,
            "portal": payload.portal.value,
            "certificate_thumbprint": certificate.thumbprint,
        },
        request=request,
    )
    await db.commit()
    return execution


@router.get("/{execution_id}", response_model=ExecutionOut)
async def get_execution(
    execution_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_execution(db, user.organization_id, execution_id)


@router.post("/{execution_id}/cancel", response_model=ExecutionOut)
async def cancel_execution(
    execution_id: uuid.UUID,
    request: Request,
    user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    execution = await _get_execution(db, user.organization_id, execution_id)
    if execution.status in (ExecutionStatus.SUCCESS, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Execução já finalizada")

    execution.cancel_requested = True
    # Pendentes são canceladas imediatamente; em andamento aguardam o agente confirmar.
    if execution.status == ExecutionStatus.PENDING:
        execution.status = ExecutionStatus.CANCELLED

    await record_audit(
        db,
        action="execution.cancel",
        organization_id=user.organization_id,
        user_id=user.id,
        entity="execution",
        entity_id=str(execution.id),
        request=request,
    )
    await db.commit()
    await db.refresh(execution)
    return execution


@router.get("/{execution_id}/logs", response_model=list[ExecutionLogOut])
async def get_execution_logs(
    execution_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_execution(db, user.organization_id, execution_id)
    result = await db.execute(
        select(ExecutionLog)
        .where(ExecutionLog.execution_id == execution_id)
        .order_by(ExecutionLog.created_at)
    )
    return result.scalars().all()


@router.get("/{execution_id}/downloads", response_model=list[DownloadOut])
async def get_execution_downloads(
    execution_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_execution(db, user.organization_id, execution_id)
    result = await db.execute(
        select(Download).where(Download.execution_id == execution_id).order_by(Download.created_at)
    )
    return result.scalars().all()
