from datetime import date, datetime, timedelta, timezone
from typing import Any

from croniter import croniter


def compute_next_run(cron_expression: str, base: datetime | None = None) -> datetime:
    base = base or datetime.now(timezone.utc)
    return croniter(cron_expression, base).get_next(datetime)


def resolve_schedule_filters(filters: dict[str, Any], today: date | None = None) -> dict[str, Any]:
    """Converte filtros relativos do agendamento em datas concretas.

    {"period_days": 7} → start_date = hoje-7, end_date = hoje.
    """
    today = today or datetime.now(timezone.utc).date()
    period_days = int(filters.get("period_days", 7))
    return {
        "start_date": (today - timedelta(days=period_days)).isoformat(),
        "end_date": today.isoformat(),
        "extra": filters.get("extra", {}),
    }
