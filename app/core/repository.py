from datetime import datetime
from typing import Any

from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Tender, User


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    return None


async def upsert_companies_bulk(db: AsyncSession, companies: list[dict[str, Any]]) -> None:
    values: list[dict[str, Any]] = []
    for company in companies:
        if not company.get("inn"):
            continue

        values.append(
            {
                "inn": company.get("inn"),
                "kpp": company.get("kpp"),
                "company_name": company.get("name"),
                "is_active": True,
            }
        )

    if not values:
        return

    stmt = insert(User).values(values).on_conflict_do_update(
        index_elements=["inn"],
        set_={
            "company_name": func.coalesce(insert(User).excluded.company_name, User.company_name),
            "kpp": func.coalesce(insert(User).excluded.kpp, User.kpp),
            "updated_at": func.now(),
        },
    )

    await db.execute(stmt)


async def upsert_tenders_bulk(db: AsyncSession, items: list[dict[str, Any]]) -> int:
    tender_values: list[dict[str, Any]] = []
    companies: list[dict[str, Any]] = []

    for item in items:
        if not item.get("id"):
            continue

        customer_inn = item.get("customer_inn")
        customer_name = item.get("customer")

        if customer_inn:
            companies.append({"inn": customer_inn, "name": customer_name, "kpp": None})

        price = item.get("price")
        final_price = item.get("final_price")
        reduction = None
        if price and final_price and price > 0:
            reduction = round((price - final_price) / price * 100, 2)

        tender_values.append(
            {
                "eis_id": item.get("id"),
                "registry_number": item.get("registry_number") or item.get("id"),
                "title": item.get("object"),
                "description": item.get("object"),
                "customer_name": customer_name,
                "customer_inn": customer_inn,
                "nmck": price,
                "final_price": final_price,
                "price_reduction": reduction,
                "publication_date": _as_datetime(item.get("publication_date")),
                "submission_deadline": _as_datetime(item.get("submission_deadline")),
                "okpd2_codes": [item.get("okpd2_code")] if item.get("okpd2_code") else None,
                "region": item.get("region"),
                "procedure_type": item.get("procedure_type"),
                "status": "active",
                "raw_data": item,
            }
        )

    if companies:
        await upsert_companies_bulk(db, companies)

    if not tender_values:
        return 0

    stmt = insert(Tender).values(tender_values).on_conflict_do_update(
        index_elements=["eis_id"],
        set_={
            "title": insert(Tender).excluded.title,
            "description": insert(Tender).excluded.description,
            "customer_name": insert(Tender).excluded.customer_name,
            "customer_inn": insert(Tender).excluded.customer_inn,
            "nmck": insert(Tender).excluded.nmck,
            "publication_date": insert(Tender).excluded.publication_date,
            "submission_deadline": insert(Tender).excluded.submission_deadline,
            "okpd2_codes": insert(Tender).excluded.okpd2_codes,
            "region": insert(Tender).excluded.region,
            "procedure_type": insert(Tender).excluded.procedure_type,
            "raw_data": insert(Tender).excluded.raw_data,
            "updated_at": func.now(),
        },
    )

    await db.execute(stmt)
    await db.commit()
    return len(tender_values)
