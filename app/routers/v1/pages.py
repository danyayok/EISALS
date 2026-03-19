from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud
from app.auth import verify_token
from app.database import get_db
from app.models import User
from app.templates import templates

router = APIRouter(tags=["HTML pages"])


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse(name="index.html", context={"request": request})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", context={"request": request})


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", context={"request": request})


async def render_protected_page(request: Request, template_name: str, current_user: User):
    return templates.TemplateResponse(template_name, context={"request": request, "current_user": current_user})


async def get_current_user_for_page(request: Request, db: AsyncSession) -> Optional[User]:
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        token_data = await verify_token(token)
    except Exception:
        return None
    user = await crud.get_user_by_inn(db, inn=token_data.inn)
    if not user or not user.is_active:
        return None
    return user


@router.get("/feed", response_class=HTMLResponse)
async def feed(request: Request, db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user_for_page(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return await render_protected_page(request, "feed.html", current_user)


@router.get("/profile/{id}", response_class=HTMLResponse)
async def profile(request: Request, id: int, db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user_for_page(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return await render_protected_page(request, "profile.html", current_user)


@router.get("/profile", response_class=HTMLResponse)
async def own_profile(request: Request, db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user_for_page(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return await render_protected_page(request, "profile.html", current_user)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user_for_page(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return await render_protected_page(request, "dashboard.html", current_user)


@router.get("/dashboard/tenders", response_class=HTMLResponse)
async def dashboard_tenders(request: Request, db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user_for_page(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return await render_protected_page(request, "tenders.html", current_user)


@router.get("/dashboard/company", response_class=HTMLResponse)
async def dashboard_company(request: Request, db: AsyncSession = Depends(get_db)):
    current_user = await get_current_user_for_page(request, db)
    if not current_user:
        return RedirectResponse(url="/login", status_code=302)
    return await render_protected_page(request, "company.html", current_user)
