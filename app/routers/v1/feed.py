from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas, auth
from app.templates import templates

# from app.database import get_db
# from app.dependencies import get_current_user

router = APIRouter(tags=["Feed Page"])

@router.get("/feed", response_class=HTMLResponse)
async def feed(request: Request):
    return templates.TemplateResponse("feed.html", context={"request": request})

# @router.get("/register", response_class=HTMLResponse)
# async def login_page(request: Request):
#     return templates.TemplateResponse("register.html", context={"request": request})