import base64
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_agent, get_current_user, require_admin
from app.core.security import generate_agent_token
from app.models import (
    Agent,
    AgentStatus,
    Certificate,
    Company,
    Download,
    Execution,
    ExecutionLog,
    ExecutionStatus,
    User,
)
from app.schemas.agent import (
    AgentEnrollRequest,
    AgentEnrollResponse,
    AgentOut,
    CertificateReport,
    EnrollmentTokenResponse,
    HeartbeatRequest,
)
from app.schemas.execution import AgentJobOut, AgentJobUpdate
from app.services.audit import record_audit
from app.services.enrollment import ENROLLMENT_TTL_SECONDS, consume_enrollment_token, create_enrollment_token

router = APIRouter(prefix="/agents", tags=["agents"])


def _agent_status(agent: Agent) -> AgentStatus:
    if agent.last_seen_at is None:
        return AgentStatus.OFFLINE
    last = agent.last_seen_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)
    delta = (datetime.now(timezone.utc) - last).total_seconds()
    return AgentStatus.ONLINE if delta < settings.agent_offline_after_seconds else AgentStatus.OFFLINE


def _to_agent_out(agent: Agent) -> AgentOut:
    out = AgentOut.model_validate(agent)
    out.status = _agent_status(agent)
    return out


# ---- Endpoints usados pelo dashboard ----

@router.get("", response_model=list[AgentOut])
async def list_agents(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Agent).where(Agent.organization_id == user.organization_id).order_by(Agent.created_at)
    )
    return [_to_agent_out(a) for a in result.scalars().all()]


@router.post("/enrollment-token", response_model=EnrollmentTokenResponse)
async def new_enrollment_token(
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    token = await create_enrollment_token(str(admin.organization_id))
    await record_audit(
        db,
        action="agent.enrollment_token",
        organization_id=admin.organization_id,
        user_id=admin.id,
        request=request,
    )
    await db.commit()
    return EnrollmentTokenResponse(enrollment_token=token, expires_in_seconds=ENROLLMENT_TTL_SECONDS)


@router.get("/version")
async def agent_version():
    """Usado pelo auto-update do agente."""
    return {
        "latest_version": settings.agent_latest_version,
        "download_url": settings.agent_download_url,
    }


# ---- Endpoints usados pelo agente desktop ----

@router.post("/enroll", response_model=AgentEnrollResponse, status_code=status.HTTP_201_CREATED)
async def enroll(payload: AgentEnrollRequest, request: Request, db: AsyncSession = Depends(get_db)):
    org_id = await consume_enrollment_token(payload.enrollment_token)
    if org_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token de matrícula inválido ou expirado")

    token, token_hash = generate_agent_token()
    agent = Agent(
        organization_id=uuid.UUID(org_id),
        name=payload.name,
        machine_id=payload.machine_id,
        token_hash=token_hash,
        version=payload.version,
        downloads_dir=payload.downloads_dir,
        last_seen_at=datetime.now(timezone.utc),
    )
    db.add(agent)
    await db.flush()
    await record_audit(
        db,
        action="agent.enroll",
        organization_id=agent.organization_id,
        agent_id=agent.id,
        detail={"machine_id": payload.machine_id},
        request=request,
    )
    await db.commit()
    return AgentEnrollResponse(agent_id=agent.id, agent_token=token)


@router.post("/me/heartbeat")
async def heartbeat(
    payload: HeartbeatRequest,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    agent.last_seen_at = datetime.now(timezone.utc)
    if payload.version:
        agent.version = payload.version
    if payload.downloads_dir:
        agent.downloads_dir = payload.downloads_dir
    await db.commit()
    return {"ok": True}


@router.put("/me/certificates")
async def report_certificates(
    certs: list[CertificateReport],
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Sincroniza os METADADOS dos certificados visíveis na máquina do agente."""
    result = await db.execute(select(Certificate).where(Certificate.agent_id == agent.id))
    existing = {c.thumbprint: c for c in result.scalars().all()}
    reported = {c.thumbprint for c in certs}

    for report in certs:
        cert = existing.get(report.thumbprint)
        if cert is None:
            db.add(
                Certificate(
                    organization_id=agent.organization_id,
                    agent_id=agent.id,
                    **report.model_dump(),
                )
            )
        else:
            for field, value in report.model_dump().items():
                setattr(cert, field, value)
            cert.is_active = True

    # Certificados que sumiram da máquina ficam inativos (histórico preservado)
    for thumbprint, cert in existing.items():
        if thumbprint not in reported:
            cert.is_active = False

    await db.commit()
    return {"synced": len(certs)}


@router.get("/me/jobs", response_model=list[AgentJobOut])
async def poll_jobs(
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    """Entrega execuções pendentes deste agente e as marca como despachadas."""
    agent.last_seen_at = datetime.now(timezone.utc)

    result = await db.execute(
        select(Execution, Company, Certificate)
        .join(Company, Execution.company_id == Company.id)
        .join(Certificate, Execution.certificate_id == Certificate.id)
        .where(
            Execution.agent_id == agent.id,
            Execution.status == ExecutionStatus.PENDING,
        )
        .order_by(Execution.created_at)
        .limit(5)
    )
    jobs: list[AgentJobOut] = []
    for execution, company, certificate in result.all():
        execution.status = ExecutionStatus.DISPATCHED
        jobs.append(
            AgentJobOut(
                execution_id=execution.id,
                portal=execution.portal,
                company_name=company.name,
                company_cnpj=company.cnpj,
                certificate_thumbprint=certificate.thumbprint,
                filters=execution.filters,
                cancel_requested=execution.cancel_requested,
            )
        )
    await db.commit()
    return jobs


@router.patch("/me/jobs/{execution_id}")
async def update_job(
    execution_id: uuid.UUID,
    payload: AgentJobUpdate,
    agent: Agent = Depends(get_current_agent),
    db: AsyncSession = Depends(get_db),
):
    execution = await db.get(Execution, execution_id)
    if execution is None or execution.agent_id != agent.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Execução não encontrada")

    now = datetime.now(timezone.utc)

    for entry in payload.logs:
        screenshot_path = None
        if entry.screenshot_base64:
            screenshots_dir = Path(settings.data_dir) / "screenshots"
            screenshots_dir.mkdir(parents=True, exist_ok=True)
            screenshot_path = str(screenshots_dir / f"{execution_id}_{uuid.uuid4().hex[:8]}.png")
            Path(screenshot_path).write_bytes(base64.b64decode(entry.screenshot_base64))
        db.add(
            ExecutionLog(
                execution_id=execution.id,
                level=entry.level,
                message=entry.message,
                screenshot_path=screenshot_path,
            )
        )

    for item in payload.downloads:
        db.add(
            Download(
                execution_id=execution.id,
                organization_id=execution.organization_id,
                **item.model_dump(),
            )
        )
    if payload.downloads:
        execution.files_count += len(payload.downloads)

    if payload.status is not None:
        execution.status = payload.status
        if payload.status == ExecutionStatus.RUNNING and execution.started_at is None:
            execution.started_at = now
        if payload.status in (ExecutionStatus.SUCCESS, ExecutionStatus.FAILED, ExecutionStatus.CANCELLED):
            execution.finished_at = now
        if payload.error_message:
            execution.error_message = payload.error_message

    await db.commit()
    return {"ok": True, "cancel_requested": execution.cancel_requested}
