import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Download, User
from app.schemas.execution import DownloadOut

router = APIRouter(prefix="/downloads", tags=["downloads"])


@router.get("", response_model=list[DownloadOut])
async def list_downloads(
    limit: int = 100,
    offset: int = 0,
    execution_id: uuid.UUID | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Download).where(Download.organization_id == user.organization_id)
    if execution_id is not None:
        query = query.where(Download.execution_id == execution_id)
    query = query.order_by(Download.created_at.desc()).limit(min(limit, 500)).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()
