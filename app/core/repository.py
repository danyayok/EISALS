import re
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.sql import func
from app.models import Tender, User


def normalize_price(value):
    if not value:
        return None
    value = re.sub(r"[^\d,\.]", "", value)
    value = value.replace(",", ".")
    try:
        return float(value)
    except Exception:
        return None


async def upsert_companies_bulk(db, companies: list):
    values = []
    for c in companies:
        if not c.get("inn"):
            continue

        values.append({
            "inn": c.get("inn"),
            "kpp": c.get("kpp"),
            "company_name": c.get("name"),
            "is_active": True
        })

    if not values:
        return

    stmt = insert(User).values(values).on_conflict_do_update(
        index_elements=["inn"],
        set_={
            "company_name": func.coalesce(insert(User).excluded.company_name, User.company_name),
            "kpp": func.coalesce(insert(User).excluded.kpp, User.kpp),
            "updated_at": func.now()
        }
    )

    await db.execute(stmt)


async def upsert_tenders_bulk(db, items: list):
    tender_values = []
    companies = []

    for item in items:
        if not item.get("id"):
            continue

        customer_inn = item.get("customer_inn")
        customer_name = item.get("customer")

        if customer_inn:
            companies.append({
                "inn": customer_inn,
                "name": customer_name,
                "kpp": None
            })

        tender_values.append({
            "eis_id": item.get("id"),
            "title": item.get("object"),
            "customer_name": customer_name,
            "customer_inn": customer_inn,
            "nmck": normalize_price(item.get("price")),
            "publication_date": item.get("date"),
            "raw_data": item
        })

    if companies:
        await upsert_companies_bulk(db, companies)

    if not tender_values:
        return

    stmt = insert(Tender).values(tender_values).on_conflict_do_update(
        index_elements=["eis_id"],
        set_={
            "title": insert(Tender).excluded.title,
            "customer_name": insert(Tender).excluded.customer_name,
            "customer_inn": insert(Tender).excluded.customer_inn,
            "nmck": insert(Tender).excluded.nmck,
            "updated_at": func.now()
        }
    )

    await db.execute(stmt)
    await db.commit()