import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.core.security import hash_password
from app.models import User
from app.schemas.auth import UserCreate, UserOut, UserUpdate
from app.services.audit import record_audit

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=list[UserOut])
async def list_users(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(User).where(User.organization_id == user.organization_id).order_by(User.created_at)
    )
    return result.scalars().all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    if (await db.execute(select(User).where(User.email == payload.email))).scalar_one_or_none():
        raise HTTPException(status.HTTP_409_CONFLICT, "E-mail já cadastrado")
    new_user = User(
        organization_id=admin.organization_id,
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    db.add(new_user)
    await db.flush()
    await record_audit(
        db,
        action="user.create",
        organization_id=admin.organization_id,
        user_id=admin.id,
        entity="user",
        entity_id=str(new_user.id),
        request=request,
    )
    await db.commit()
    return new_user


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    payload: UserUpdate,
    request: Request,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    target = await db.get(User, user_id)
    if target is None or target.organization_id != admin.organization_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuário não encontrado")

    data = payload.model_dump(exclude_unset=True)
    if "password" in data:
        target.hashed_password = hash_password(data.pop("password"))
    for field, value in data.items():
        setattr(target, field, value)

    await record_audit(
        db,
        action="user.update",
        organization_id=admin.organization_id,
        user_id=admin.id,
        entity="user",
        entity_id=str(target.id),
        detail={"fields": list(data.keys())},
        request=request,
    )
    await db.commit()
    await db.refresh(target)
    return target
