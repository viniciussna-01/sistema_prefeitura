from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import (
    Agent,
    Certificate,
    Company,
    Download,
    Execution,
    ExecutionStatus,
    Schedule,
    User,
)
from app.schemas.dashboard import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/stats", response_model=DashboardStats)
async def stats(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    org_id = user.organization_id
    now = datetime.now(timezone.utc)
    seven_days_ago = now - timedelta(days=7)
    thirty_days = now + timedelta(days=30)
    online_cutoff = now - timedelta(seconds=settings.agent_offline_after_seconds)

    async def scalar(query) -> int:
        return (await db.execute(query)).scalar() or 0

    total_companies = await scalar(
        select(func.count()).select_from(Company).where(Company.organization_id == org_id)
    )
    total_certificates = await scalar(
        select(func.count())
        .select_from(Certificate)
        .where(Certificate.organization_id == org_id, Certificate.is_active.is_(True))
    )
    total_agents = await scalar(
        select(func.count()).select_from(Agent).where(Agent.organization_id == org_id)
    )
    agents_online = await scalar(
        select(func.count())
        .select_from(Agent)
        .where(Agent.organization_id == org_id, Agent.last_seen_at >= online_cutoff)
    )
    executions_total = await scalar(
        select(func.count()).select_from(Execution).where(Execution.organization_id == org_id)
    )
    executions_running = await scalar(
        select(func.count())
        .select_from(Execution)
        .where(
            Execution.organization_id == org_id,
            Execution.status.in_([ExecutionStatus.PENDING, ExecutionStatus.DISPATCHED, ExecutionStatus.RUNNING]),
        )
    )
    executions_failed_7d = await scalar(
        select(func.count())
        .select_from(Execution)
        .where(
            Execution.organization_id == org_id,
            Execution.status == ExecutionStatus.FAILED,
            Execution.created_at >= seven_days_ago,
        )
    )
    downloads_total = await scalar(
        select(func.count()).select_from(Download).where(Download.organization_id == org_id)
    )
    files_downloaded_7d = await scalar(
        select(func.count())
        .select_from(Download)
        .where(Download.organization_id == org_id, Download.created_at >= seven_days_ago)
    )
    expiring_certificates = await scalar(
        select(func.count())
        .select_from(Certificate)
        .where(
            Certificate.organization_id == org_id,
            Certificate.is_active.is_(True),
            Certificate.not_after.is_not(None),
            Certificate.not_after <= thirty_days,
        )
    )

    last_execution_at = (
        await db.execute(
            select(func.max(Execution.created_at)).where(Execution.organization_id == org_id)
        )
    ).scalar()
    next_scheduled_at = (
        await db.execute(
            select(func.min(Schedule.next_run_at)).where(
                Schedule.organization_id == org_id, Schedule.enabled.is_(True)
            )
        )
    ).scalar()

    # Tempo médio: calculado em Python para funcionar em Postgres e SQLite
    finished = (
        await db.execute(
            select(Execution.started_at, Execution.finished_at)
            .where(
                Execution.organization_id == org_id,
                Execution.status == ExecutionStatus.SUCCESS,
                Execution.started_at.is_not(None),
                Execution.finished_at.is_not(None),
            )
            .order_by(Execution.finished_at.desc())
            .limit(100)
        )
    ).all()
    durations = [(f - s).total_seconds() for s, f in finished if s and f]
    avg_execution_seconds = sum(durations) / len(durations) if durations else None

    return DashboardStats(
        total_companies=total_companies,
        total_certificates=total_certificates,
        total_agents=total_agents,
        agents_online=agents_online,
        last_execution_at=last_execution_at,
        next_scheduled_at=next_scheduled_at,
        executions_total=executions_total,
        executions_running=executions_running,
        executions_failed_7d=executions_failed_7d,
        downloads_total=downloads_total,
        files_downloaded_7d=files_downloaded_7d,
        avg_execution_seconds=avg_execution_seconds,
        expiring_certificates=expiring_certificates,
    )
