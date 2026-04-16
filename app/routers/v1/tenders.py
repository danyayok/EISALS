from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import crud
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models import schemas
from app.models.models import User

router = APIRouter(prefix="/api/tenders", tags=["Tenders"])


@router.post("/search", response_model=list[schemas.TenderResponse])
async def search_tenders(
        filters: schemas.TenderFilters,
        skip: int = 0,
        limit: int = 50,
        db: AsyncSession = Depends(get_db),
):
    return await crud.get_tenders_with_filters(db, filters, skip=skip, limit=limit)


@router.get("/recommended")
async def get_recommended_tenders(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user),
):
    return await crud.get_recommended_tenders_for_user(db, current_user)
