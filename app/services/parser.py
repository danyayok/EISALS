import asyncio
import httpx
import re
from bs4 import BeautifulSoup
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, ForeignKey,
    JSON, Index, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.dialects.postgresql import insert


# вот тут я вообще не понимающпщпщпщ
# я не читал этот код, а просто навайбкодил в отличии от остальной части проекта что сам писал
# потом как накидаю парсер для еис буду смотреть этот класс




# =========================
# TIME (МОСКВА)
# =========================
MOSCOW_TZ = ZoneInfo("Europe/Moscow")

def now_moscow():
    return datetime.now(MOSCOW_TZ)


# =========================
# DB
# =========================
DATABASE_URL = "postgresql://user:password@localhost:5432/eis_db"

engine = create_engine(DATABASE_URL, pool_size=10, max_overflow=20)
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


# =========================
# RAW DATA
# =========================
class RawData(Base):
    __tablename__ = "raw_data"

    id = Column(Integer, primary_key=True)
    source = Column(String)
    type = Column(String)
    external_id = Column(String, index=True)

    content = Column(JSON)
    version = Column(Integer, default=1)

    created_at = Column(DateTime(timezone=True), default=now_moscow)

    __table_args__ = (
        Index("idx_raw_external", "external_id"),
    )


# =========================
# COMPANY
# =========================
class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True)
    inn = Column(String, index=True)
    kpp = Column(String)
    name = Column(String)

    created_at = Column(DateTime(timezone=True), default=now_moscow)
    updated_at = Column(DateTime(timezone=True), default=now_moscow)

    eis_ids = relationship("EISCompanyId", back_populates="company")

    __table_args__ = (
        UniqueConstraint("inn", "kpp", name="uniq_company"),
    )


# =========================
# EIS ID
# =========================
class EISCompanyId(Base):
    __tablename__ = "company_eis_ids"

    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id"))
    eis_id = Column(String)
    type = Column(String)

    company = relationship("Company", back_populates="eis_ids")

    __table_args__ = (
        UniqueConstraint("eis_id", name="uniq_eis_id"),
        Index("idx_eis_lookup", "eis_id"),
    )


# =========================
# TENDERS
# =========================
class Tender(Base):
    __tablename__ = "tenders"

    id = Column(Integer, primary_key=True)
    eis_id = Column(String)

    title = Column(String)
    price = Column(Integer)

    published_at = Column(DateTime(timezone=True))

    customer_id = Column(Integer, ForeignKey("companies.id"))

    created_at = Column(DateTime(timezone=True), default=now_moscow)
    updated_at = Column(DateTime(timezone=True), default=now_moscow)

    __table_args__ = (
        UniqueConstraint("eis_id", name="uniq_tender"),
        Index("idx_tender_eis", "eis_id"),
    )


# =========================
# CONTRACTS
# =========================
class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True)
    eis_id = Column(String)

    price = Column(Integer)
    signed_at = Column(DateTime(timezone=True))

    supplier_id = Column(Integer, ForeignKey("companies.id"))
    customer_id = Column(Integer, ForeignKey("companies.id"))

    created_at = Column(DateTime(timezone=True), default=now_moscow)
    updated_at = Column(DateTime(timezone=True), default=now_moscow)

    __table_args__ = (
        UniqueConstraint("eis_id", name="uniq_contract"),
        Index("idx_contract_eis", "eis_id"),
    )


# =========================
# SERVICE
# =========================
class DataService:

    def __init__(self):
        self.session = SessionLocal()

    def close(self):
        self.session.close()

    def commit(self):
        self.session.commit()

    # RAW
    def save_raw(self, source, type_, external_id, content):
        latest = self.session.query(RawData).filter_by(
            external_id=external_id
        ).order_by(RawData.version.desc()).first()

        version = 1 if not latest else latest.version + 1

        raw = RawData(
            source=source,
            type=type_,
            external_id=external_id,
            content=content,
            version=version
        )
        self.session.add(raw)

    # COMPANY
    def upsert_company(self, inn, name=None, kpp=None):
        stmt = insert(Company).values(
            inn=inn,
            name=name,
            kpp=kpp,
            updated_at=now_moscow()
        ).on_conflict_do_update(
            constraint="uniq_company",
            set_={
                "name": name,
                "updated_at": now_moscow()
            }
        ).returning(Company.id)

        result = self.session.execute(stmt)
        return result.scalar()

    # TENDER
    def upsert_tender(self, eis_id, title, price, customer_inn):
        customer_id = self.upsert_company(customer_inn)

        stmt = insert(Tender).values(
            eis_id=eis_id,
            title=title,
            price=self._normalize_price(price),
            customer_id=customer_id,
            updated_at=now_moscow()
        ).on_conflict_do_update(
            constraint="uniq_tender",
            set_={
                "title": title,
                "price": self._normalize_price(price),
                "updated_at": now_moscow()
            }
        )

        self.session.execute(stmt)

    def _normalize_price(self, value):
        if not value:
            return None
        value = re.sub(r"[^\d,]", "", value)
        value = value.replace(",", ".")
        return int(float(value))


# =========================
# PARSER
# =========================
class AsyncParserZakazi:

    def __init__(self):
        self.semaphore = asyncio.Semaphore(5)
        self.db = DataService()

        self.headers = {
            "User-Agent": "Mozilla/5.0"
        }

    async def fetch(self, client, url, retries=3):
        for attempt in range(retries):
            try:
                async with self.semaphore:
                    r = await client.get(url, timeout=15)

                if r.status_code == 200:
                    return r.text

            except Exception:
                await asyncio.sleep(2 ** attempt)

        return None

    def safe_text(self, el):
        return el.get_text(strip=True) if el else None

    def find_by_label(self, soup, label):
        el = soup.find(string=lambda x: x and label in x)
        if el:
            return self.safe_text(el.find_next())
        return None

    async def parse_page(self, client, page):
        url = f"https://zakupki.gov.ru/epz/order/extendedsearch/results.html?pageNumber={page}"

        html = await self.fetch(client, url)
        if not html:
            return []

        # сохраняем raw поиска
        self.db.save_raw("eis", "search_page", f"page_{page}", {"html": html})

        soup = BeautifulSoup(html, "html.parser")
        return soup.find_all("div", class_="search-registry-entry-block")

    def parse_card(self, block):
        try:
            id_el = block.find("a")
            if not id_el:
                return None

            eis_id = self.safe_text(id_el)

            title = self.safe_text(block.find("div", class_="registry-entry__body-block"))
            price = self.safe_text(block.find("div", class_="price-block__value"))

            return {
                "eis_id": eis_id,
                "title": title,
                "price": price,
                "url": "https://zakupki.gov.ru" + id_el["href"]
            }

        except Exception:
            return None

    async def parse_detail(self, client, data):
        html = await self.fetch(client, data["url"])
        if not html:
            return data

        self.db.save_raw("eis", "tender", data["eis_id"], {"html": html})

        soup = BeautifulSoup(html, "html.parser")

        data["inn"] = self.find_by_label(soup, "ИНН")

        return data

    async def process_page(self, client, page):
        blocks = await self.parse_page(client, page)

        tasks = []
        for b in blocks:
            parsed = self.parse_card(b)
            if parsed:
                tasks.append(self.parse_detail(client, parsed))

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for r in results:
            if isinstance(r, dict) and r.get("inn"):
                self.db.upsert_tender(
                    eis_id=r["eis_id"],
                    title=r["title"],
                    price=r["price"],
                    customer_inn=r["inn"]
                )

        self.db.commit()

    async def run(self, pages=2):
        async with httpx.AsyncClient(headers=self.headers) as client:
            tasks = [self.process_page(client, p) for p in range(pages)]
            await asyncio.gather(*tasks)

        self.db.close()


# =========================
# INIT
# =========================
def init_db():
    Base.metadata.create_all(engine)


# =========================
# RUN
# =========================
async def main():
    init_db()
    parser = AsyncParserZakazi()
    await parser.run(pages=2)


if __name__ == "__main__":
    asyncio.run(main())