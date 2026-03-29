import re
from datetime import timedelta

from fastapi import APIRouter, Depends, Form, HTTPException, Response, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.models import schemas
from app.core import crud
from app.services import auth
from app.core.config import settings
from app.core.database import get_db

router = APIRouter(prefix="/api", tags=["Auth"])


@router.post("/register")
async def register_user(
    inn: str = Form(...),
    kpp: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone: str = Form(...),
    agree_conf: bool = Form(False),
    db: AsyncSession = Depends(get_db),
):
    if not agree_conf:
        raise HTTPException(status_code=400, detail="Необходимо согласие с правилами")

    sanitized_phone = re.sub(r"\D", "", phone)
    user_payload = {
        "inn": inn,
        "kpp": kpp,
        "email": email,
        "password": password,
        "phone": sanitized_phone,
        "company_name": f"Компания ИНН {inn}",
    }

    try:
        user_create_data = schemas.UserCreate(**user_payload)
    except ValidationError:
        raise HTTPException(status_code=422, detail="Некорректные данные регистрации")

    existing_user = await crud.get_user_by_inn(db, inn=user_create_data.inn)
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким ИНН уже существует")

    new_user = await crud.create_user(db, user_data=user_create_data)
    if user_create_data.phone:
        new_user.phone_number = user_create_data.phone
        await db.commit()

    access_token = auth.create_access_token(
        data={"sub": new_user.inn},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    response = JSONResponse(
        {
            "status": "success",
            "user_id": new_user.id,
            "access_token": access_token,
            "token_type": "bearer",
        }
    )
    return response


@router.post("/login", response_model=schemas.Token)
async def login(
    inn: str = Form(...),
    password: str = Form(...),
    db: AsyncSession = Depends(get_db),
):
    try:
        login_data = schemas.UserLogin(inn=inn, password=password)
    except ValidationError:
        raise HTTPException(status_code=422, detail="Некорректный формат ИНН или пароля")

    user = await crud.authenticate_user(db, inn=login_data.inn, password=login_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Неверный ИНН или пароль")

    access_token = auth.create_access_token(data={"sub": user.inn})
    response = JSONResponse({"access_token": access_token, "token_type": "bearer"})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=settings.COOKIE_SECURE,
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return response


@router.post("/logout", status_code=204)
async def logout() -> Response:
    response = Response(status_code=204)
    response.delete_cookie("access_token", path="/")
    return response
