import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_operator
from app.models import Certificate, Company, Schedule, User
from app.schemas.schedule import ScheduleCreate, ScheduleOut, ScheduleUpdate
from app.services.audit import record_audit
from app.services.schedules import compute_next_run

router = APIRouter(prefix="/schedules", tags=["schedules"])


@router.get("", response_model=list[ScheduleOut])
async def list_schedules(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Schedule).where(Schedule.organization_id == user.organization_id).order_by(Schedule.name)
    )
    return result.scalars().all()


@router.post("", response_model=ScheduleOut, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    payload: ScheduleCreate,
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

    schedule = Schedule(
        organization_id=user.organization_id,
        **payload.model_dump(),
        next_run_at=compute_next_run(payload.cron_expression),
    )
    db.add(schedule)
    await db.flush()
    await record_audit(
        db,
        action="schedule.create",
        organization_id=user.organization_id,
        user_id=user.id,
        entity="schedule",
        entity_id=str(schedule.id),
        detail={"name": schedule.name, "cron": schedule.cron_expression},
        request=request,
    )
    await db.commit()
    return schedule


@router.patch("/{schedule_id}", response_model=ScheduleOut)
async def update_schedule(
    schedule_id: uuid.UUID,
    payload: ScheduleUpdate,
    request: Request,
    user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    schedule = await db.get(Schedule, schedule_id)
    if schedule is None or schedule.organization_id != user.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agendamento não encontrado")

    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(schedule, field, value)
    if "cron_expression" in data or data.get("enabled"):
        schedule.next_run_at = compute_next_run(schedule.cron_expression)

    await record_audit(
        db,
        action="schedule.update",
        organization_id=user.organization_id,
        user_id=user.id,
        entity="schedule",
        entity_id=str(schedule.id),
        detail={"fields": list(data.keys())},
        request=request,
    )
    await db.commit()
    await db.refresh(schedule)
    return schedule


@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: uuid.UUID,
    request: Request,
    user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    schedule = await db.get(Schedule, schedule_id)
    if schedule is None or schedule.organization_id != user.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Agendamento não encontrado")
    await record_audit(
        db,
        action="schedule.delete",
        organization_id=user.organization_id,
        user_id=user.id,
        entity="schedule",
        entity_id=str(schedule.id),
        detail={"name": schedule.name},
        request=request,
    )
    await db.delete(schedule)
    await db.commit()
