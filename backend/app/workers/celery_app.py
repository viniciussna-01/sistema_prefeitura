from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "sistema_prefeitura",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.workers.tasks"],
)

celery_app.conf.update(
    timezone="UTC",
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        # Dispara agendamentos vencidos
        "check-schedules": {
            "task": "app.workers.tasks.check_schedules",
            "schedule": 60.0,
        },
        # Expira execuções travadas e re-tenta falhas
        "watchdog": {
            "task": "app.workers.tasks.execution_watchdog",
            "schedule": 60.0,
        },
        # Limpa screenshots antigos (diariamente às 03:00 UTC)
        "cleanup-screenshots": {
            "task": "app.workers.tasks.cleanup_old_screenshots",
            "schedule": crontab(hour=3, minute=0),
        },
    },
)
