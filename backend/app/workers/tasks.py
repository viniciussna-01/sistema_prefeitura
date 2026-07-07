"""Tarefas de fundo (Celery).

As tarefas são síncronas do ponto de vista do Celery, mas reutilizam os
modelos assíncronos criando um event loop e um engine descartável por
execução — simples e seguro entre processos/loops.
"""

import asyncio
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.models import Execution, ExecutionLog, ExecutionStatus, LogLevel, Schedule
from app.services.schedules import compute_next_run, resolve_schedule_filters
from app.workers.celery_app import celery_app


def _run(coro) -> int:
    return asyncio.run(coro)


async def _with_session(fn) -> int:
    engine = create_async_engine(settings.database_url)
    try:
        factory = async_sessionmaker(engine, expire_on_commit=False)
        async with factory() as session:
            result = await fn(session)
            await session.commit()
            return result
    finally:
        await engine.dispose()


@celery_app.task
def check_schedules() -> int:
    """Cria execuções para agendamentos vencidos e calcula o próximo disparo."""

    async def inner(session) -> int:
        now = datetime.now(timezone.utc)
        result = await session.execute(
            select(Schedule).where(Schedule.enabled.is_(True), Schedule.next_run_at <= now)
        )
        created = 0
        for schedule in result.scalars().all():
            from app.models import Certificate

            certificate = await session.get(Certificate, schedule.certificate_id)
            agent_id = certificate.agent_id if certificate else None
            session.add(
                Execution(
                    organization_id=schedule.organization_id,
                    company_id=schedule.company_id,
                    certificate_id=schedule.certificate_id,
                    agent_id=agent_id,
                    schedule_id=schedule.id,
                    portal=schedule.portal,
                    filters=resolve_schedule_filters(schedule.filters),
                    max_attempts=settings.execution_max_attempts,
                )
            )
            schedule.last_run_at = now
            schedule.next_run_at = compute_next_run(schedule.cron_expression, now)
            created += 1
        return created

    return _run(_with_session(inner))


@celery_app.task
def execution_watchdog() -> int:
    """Expira execuções travadas e re-enfileira falhas com tentativas restantes."""

    async def inner(session) -> int:
        now = datetime.now(timezone.utc)
        timeout_cutoff = now - timedelta(minutes=settings.execution_timeout_minutes)
        touched = 0

        # 1) Timeout: execuções em andamento há tempo demais
        result = await session.execute(
            select(Execution).where(
                Execution.status.in_([ExecutionStatus.DISPATCHED, ExecutionStatus.RUNNING]),
                Execution.updated_at <= timeout_cutoff,
            )
        )
        for execution in result.scalars().all():
            execution.status = ExecutionStatus.FAILED
            execution.finished_at = now
            execution.error_message = "Tempo limite de execução excedido (watchdog)"
            session.add(
                ExecutionLog(
                    execution_id=execution.id,
                    level=LogLevel.ERROR,
                    message="Execução expirada pelo watchdog do servidor",
                )
            )
            touched += 1

        # 2) Retry: falhas com tentativas restantes voltam para a fila
        result = await session.execute(
            select(Execution).where(
                Execution.status == ExecutionStatus.FAILED,
                Execution.attempt < Execution.max_attempts,
                Execution.cancel_requested.is_(False),
            )
        )
        for execution in result.scalars().all():
            execution.status = ExecutionStatus.PENDING
            execution.attempt += 1
            execution.started_at = None
            execution.finished_at = None
            session.add(
                ExecutionLog(
                    execution_id=execution.id,
                    level=LogLevel.WARNING,
                    message=f"Nova tentativa automática ({execution.attempt}/{execution.max_attempts})",
                )
            )
            touched += 1

        return touched

    return _run(_with_session(inner))


@celery_app.task
def cleanup_old_screenshots(max_age_days: int = 30) -> int:
    """Remove capturas de tela de falhas com mais de N dias."""
    screenshots_dir = Path(settings.data_dir) / "screenshots"
    if not screenshots_dir.exists():
        return 0
    cutoff = time.time() - max_age_days * 86400
    removed = 0
    for file in screenshots_dir.glob("*.png"):
        if file.stat().st_mtime < cutoff:
            file.unlink(missing_ok=True)
            removed += 1
    return removed
