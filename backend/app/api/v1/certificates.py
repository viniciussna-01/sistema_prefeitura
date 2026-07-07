from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.models import Certificate, User
from app.schemas.agent import CertificateOut

router = APIRouter(prefix="/certificates", tags=["certificates"])


@router.get("", response_model=list[CertificateOut])
async def list_certificates(
    only_active: bool = True,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    query = select(Certificate).where(Certificate.organization_id == user.organization_id)
    if only_active:
        query = query.where(Certificate.is_active.is_(True))
    result = await db.execute(query.order_by(Certificate.subject))
    return result.scalars().all()
