from celery import Celery

import os
from app.core.crud import sync_company_profile_from_eis, get_user_by_inn
from app.models import models
from app.services.parser import EISParser
celery_instance = Celery(
    "tasks",
    broker=os.getenv("REDIS_URL", "redis://redis:6379/0"),
    backend=os.getenv("REDIS_URL", "redis://redis:6379/0")
)

import asyncio
from app.core.database import AsyncSessionLocal

@celery_instance.task(name="sync_with_eis_task")
def sync_with_eis_task(user_id: str) -> None:
    print(f"Starting parsing for user {user_id}")
    asyncio.run(execute_sync(user_id))

async def execute_sync(user_id: str) -> None:
    async with AsyncSessionLocal() as db:
        user = await get_user_by_inn(db, user_id=int(user_id))
        if not user:
            return
        parser = EISParser()
        await sync_company_profile_from_eis(db, user, parser)