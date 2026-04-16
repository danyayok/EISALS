import asyncio
import logging

from app.core.database import AsyncSessionLocal
from app.core.repository import upsert_tenders_bulk
from app.services.parser import EISParser

logger = logging.getLogger(__name__)


async def collect_tenders_once(pages: int = 4) -> int:
    parser = EISParser()
    items = await parser.parse_latest_tenders(pages=pages)
    if not items:
        return 0

    async with AsyncSessionLocal() as db:
        saved = await upsert_tenders_bulk(db, items)

    logger.info("Saved %s tenders from EIS", saved)
    return saved


async def hourly_parser():
    while True:
        try:
            logger.info("Starting scheduled EIS parsing")
            await collect_tenders_once(pages=4)
            logger.info("Scheduled EIS parsing finished")
        except Exception as exc:
            logger.exception("Hourly parser error: %s", exc)

        await asyncio.sleep(3600)
