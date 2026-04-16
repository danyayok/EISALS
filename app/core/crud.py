from typing import Optional
from datetime import datetime, timezone

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import models, schemas
from app.services.auth import get_password_hash, verify_password
from app.services.parser import EISParser
from app.services.tender_analytics import evaluate_tender_for_user


async def get_user_by_inn(db: AsyncSession, inn: str, kpp: Optional[str] = None) -> Optional[models.User]:
    filters = [models.User.inn == inn]
    if kpp:
        filters.append(models.User.kpp == kpp)

    query = select(models.User).options(selectinload(models.User.profile)).where(and_(*filters))
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_user(db: AsyncSession, user_data: schemas.UserCreate) -> models.User:
    hashed_password = get_password_hash(user_data.password)

    db_user = models.User(
        inn=user_data.inn,
        kpp=user_data.kpp,
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
    except Exception as exc:
        await db.rollback()
        raise exc


async def authenticate_user(db: AsyncSession, inn: str, password: str, kpp: Optional[str] = None) -> Optional[models.User]:
    user = await get_user_by_inn(db, inn, kpp)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user


async def sync_company_profile_from_eis(db: AsyncSession, user: models.User, parser: EISParser | None = None) -> None:
    parser = parser or EISParser()
    company = await parser.get_company_info(user.inn)
    if not company:
        return

    if company.get("name"):
        user.company_name = company["name"]
    if company.get("kpp") and not user.kpp:
        user.kpp = company["kpp"]

    if user.profile is None:
        user.profile = models.CompanyProfile(user_id=user.id)

    user.profile.full_name = company.get("name") or user.profile.full_name
    user.profile.ogrn = company.get("ogrn") or user.profile.ogrn
    user.profile.legal_address = company.get("address") or user.profile.legal_address
    user.profile.updated_at = datetime.now(timezone.utc)

    await db.commit()


async def get_company_profile(db: AsyncSession, user_id: int) -> Optional[models.CompanyProfile]:
    result = await db.execute(select(models.CompanyProfile).where(models.CompanyProfile.user_id == user_id))
    return result.scalar_one_or_none()


async def update_company_profile(
        db: AsyncSession,
        user_id: int,
        profile_data: schemas.CompanyProfileBase,
) -> models.CompanyProfile:
    profile = await get_company_profile(db, user_id)

    if not profile:
        profile = models.CompanyProfile(user_id=user_id)
        db.add(profile)

    update_data = profile_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)

    profile.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(profile)
    return profile


async def get_tenders_with_filters(
        db: AsyncSession,
        filters: schemas.TenderFilters,
        skip: int = 0,
        limit: int = 50,
) -> list[models.Tender]:
    query = select(models.Tender)

    if filters.okpd2_codes:
        query = query.where(models.Tender.okpd2_codes.overlap(filters.okpd2_codes))

    if filters.regions:
        query = query.where(models.Tender.region.in_(filters.regions))

    if filters.min_price is not None:
        query = query.where(models.Tender.nmck >= filters.min_price)

    if filters.max_price is not None:
        query = query.where(models.Tender.nmck <= filters.max_price)

    result = await db.execute(query.order_by(models.Tender.publication_date.desc()).offset(skip).limit(limit))
    return list(result.scalars().all())


async def get_recommended_tenders_for_user(db: AsyncSession, user: models.User, limit: int = 30) -> list[dict]:
    tender_query = select(models.Tender).where(models.Tender.status == "active").order_by(models.Tender.publication_date.desc()).limit(limit)
    result = await db.execute(tender_query)
    tenders = result.scalars().all()

    recommendations: list[dict] = []
    for tender in tenders:
        score = evaluate_tender_for_user(user, tender)
        tender.win_probability = score.win_probability
        tender.risk_level = score.dumping_risk
        tender.market_price_adequacy = score.recommendation

        recommendations.append(
            {
                "eis_id": tender.eis_id,
                "title": tender.title,
                "customer_name": tender.customer_name,
                "nmck": tender.nmck,
                "region": tender.region,
                "okpd2_codes": tender.okpd2_codes,
                "publication_date": tender.publication_date,
                "submission_deadline": tender.submission_deadline,
                "match_percent": score.match_percent,
                "competition_level": score.competition_level,
                "dumping_risk": score.dumping_risk,
                "recommendation": score.recommendation,
                "win_probability": score.win_probability,
            }
        )

    await db.commit()
    recommendations.sort(key=lambda row: row["win_probability"], reverse=True)
    return recommendations
