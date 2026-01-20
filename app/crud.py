from typing import Optional, List, Any
from decimal import Decimal
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from app import models, schemas
from app.auth import get_password_hash, verify_password

async def get_user_by_inn(db: AsyncSession, inn: str) -> Optional[models.User]:
    result = await db.execute(
        select(models.User)
        .options(selectinload(models.User.profile))
        .where(models.User.inn == inn)
    )
    return result.scalar_one_or_none()

async def create_user(db: AsyncSession, user_data: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user_data.password)

    db_user = models.User(
        inn=user_data.inn,
        email=user_data.email,
        company_name=user_data.company_name,
        hashed_password=hashed_password,
        role="supplier",
        is_active=True,
    )

    try:
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user
    except Exception as e:
        await db.rollback()
        raise e

async def authenticate_user(db: AsyncSession, inn: str, password: str) -> Optional[models.User]:
    user = await get_user_by_inn(db, inn)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

async def get_company_profile(db: AsyncSession, user_id: int) -> Optional[models.CompanyProfile]:
    result = await db.execute(
        select(models.CompanyProfile).where(models.CompanyProfile.user_id == user_id)
    )
    return result.scalar_one_or_none()

async def update_company_profile(db: AsyncSession, user_id: int, profile_data: schemas.CompanyProfileBase) -> models.CompanyProfile:
    profile = await get_company_profile(db, user_id)

    if not profile:
        profile = models.CompanyProfile(user_id=user_id)
        db.add(profile)

    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    profile.update_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(profile)
    return profile

async def get_tenders_with_filters(
        db: AsyncSession,
        filters: schemas.TenderFilters,
        skip: int = 0,
        limit: int = 50,
) -> List[models.Tender]:
    query = select(models.Tender)

    if filters.okpd2_codes:
        query = query.where(models.Tender.okpd2_codes.overlap(filters.okpd2_codes))

    if filters.regions:
        query = query.where(models.Tender.region.in_(filters.regions))

    if filters.min_price is not None:
        query = query.where(models.Tender.nmck >= filters.min_price)

    if filters.max_price is not None:
        query = query.where(models.Tender.nmck <= filters.max_price)

    result = await db.execute(
        query.order_by(models.Tender.publication_date.desc()).offset(skip).limit(limit)
    )
    return list(result.scalars().all())
