from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas, auth
from app.templates import templates

# from app.database import get_db
# from app.dependencies import get_current_user

router = APIRouter(tags=["HTML pages"])
@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", context={"request": request})

@router.get("/register", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("register.html", context={"request": request})

@router.get("/feed", response_class=HTMLResponse)
async def feed(request: Request):
    return templates.TemplateResponse("feed.html", context={"request": request})

@router.get("/profile/{id}", response_class=HTMLResponse)
async def profile(request: Request):
    return templates.TemplateResponse("profile.html", context={"request": request})

@router.get("/profile", response_class=HTMLResponse)
async def own_profile(request: Request):
    return templates.TemplateResponse("profile.html", context={"request": request})

# @router.get("/register", response_class=HTMLResponse)
# async def login_page(request: Request):
#     return templates.TemplateResponse("register.html", context={"request": request})