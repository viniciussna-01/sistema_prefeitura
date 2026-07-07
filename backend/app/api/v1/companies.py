import uuid

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user, require_operator
from app.models import Company, User
from app.schemas.company import CompanyCreate, CompanyOut, CompanyUpdate
from app.services.audit import record_audit

router = APIRouter(prefix="/companies", tags=["companies"])


async def _get_company(db: AsyncSession, org_id: uuid.UUID, company_id: uuid.UUID) -> Company:
    company = await db.get(Company, company_id)
    if company is None or company.organization_id != org_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Empresa não encontrada")
    return company


@router.get("", response_model=list[CompanyOut])
async def list_companies(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Company)
        .where(Company.organization_id == user.organization_id)
        .order_by(Company.name)
    )
    return result.scalars().all()


@router.post("", response_model=CompanyOut, status_code=status.HTTP_201_CREATED)
async def create_company(
    payload: CompanyCreate,
    request: Request,
    user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    company = Company(organization_id=user.organization_id, **payload.model_dump())
    db.add(company)
    await db.flush()
    await record_audit(
        db,
        action="company.create",
        organization_id=user.organization_id,
        user_id=user.id,
        entity="company",
        entity_id=str(company.id),
        detail={"name": company.name, "cnpj": company.cnpj},
        request=request,
    )
    await db.commit()
    return company


@router.get("/{company_id}", response_model=CompanyOut)
async def get_company(
    company_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_company(db, user.organization_id, company_id)


@router.patch("/{company_id}", response_model=CompanyOut)
async def update_company(
    company_id: uuid.UUID,
    payload: CompanyUpdate,
    request: Request,
    user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    company = await _get_company(db, user.organization_id, company_id)
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(company, field, value)
    await record_audit(
        db,
        action="company.update",
        organization_id=user.organization_id,
        user_id=user.id,
        entity="company",
        entity_id=str(company.id),
        detail={"fields": list(data.keys())},
        request=request,
    )
    await db.commit()
    await db.refresh(company)
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: uuid.UUID,
    request: Request,
    user: User = Depends(require_operator),
    db: AsyncSession = Depends(get_db),
):
    company = await _get_company(db, user.organization_id, company_id)
    await record_audit(
        db,
        action="company.delete",
        organization_id=user.organization_id,
        user_id=user.id,
        entity="company",
        entity_id=str(company.id),
        detail={"name": company.name},
        request=request,
    )
    await db.delete(company)
    await db.commit()
