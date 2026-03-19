from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.requests import Request
from fastapi.responses import HTMLResponse

from app.dependencies import get_current_user
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


@router.get("/feed", response_class=HTMLResponse)
async def feed(request: Request, current_user: Annotated[User, Depends(get_current_user)]):
    return await render_protected_page(request, "feed.html", current_user)


@router.get("/profile/{id}", response_class=HTMLResponse)
async def profile(request: Request, id: int, current_user: Annotated[User, Depends(get_current_user)]):
    return await render_protected_page(request, "profile.html", current_user)


@router.get("/profile", response_class=HTMLResponse)
async def own_profile(request: Request, current_user: Annotated[User, Depends(get_current_user)]):
    return await render_protected_page(request, "profile.html", current_user)


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, current_user: Annotated[User, Depends(get_current_user)]):
    return await render_protected_page(request, "dashboard.html", current_user)


@router.get("/dashboard/tenders", response_class=HTMLResponse)
async def dashboard_tenders(request: Request, current_user: Annotated[User, Depends(get_current_user)]):
    return await render_protected_page(request, "tenders.html", current_user)


@router.get("/dashboard/company", response_class=HTMLResponse)
async def dashboard_company(request: Request, current_user: Annotated[User, Depends(get_current_user)]):
    return await render_protected_page(request, "company.html", current_user)
