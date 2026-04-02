from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import crud
from app.services.auth import verify_token
from app.core.database import get_db
from app.models.models import User
from app.core.templates import templates
from fastapi.responses import PlainTextResponse

router = APIRouter(tags=["HTML pages"])



@router.get("/robots.txt", response_class=PlainTextResponse)
def robots_txt():
    lines = [
        "User-agent: *",
        "Crawl-delay: 2",       # Пауза 2 секунды (робот будет качать не более 30 стр/мин)
        "Allow: /",
        "Allow: /feed",
        "Allow: /static/",
        "Disallow: /profile",
        "Disallow: /api/",
        "Disallow: /login",
        "Disallow: /*?*",       # Критично: не даем роботу бесконечно перебирать фильтры
        "",
        "User-agent: Yandex",    # Яндекс очень внимателен к Crawl-delay
        "Crawl-delay: 3",       # Для Яндекса чуть медленнее (раз в 3 сек)
        "Clean-param: ref /",    # Убирает мусорные метки из URL для Яндекса
        "",
        "Sitemap: https://eisals.ru",
        "Host: https://eisals.ru"
    ]
    return "\n".join(lines)


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
