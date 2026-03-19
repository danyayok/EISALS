import os
import shutil

from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from app.templates import templates
from fastapi import APIRouter, Depends, Form, File, UploadFile, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas
from app.database import get_db
# from app.dependencies import get_current_user

router = APIRouter(prefix="/api", tags=["Auth"])

from datetime import timedelta
from app.config import settings
from app import auth  # Твой файл с функцией create_access_token


@router.post("/register")
async def register_user(
        inn: str = Form(...),
        email: str = Form(...),
        password: str = Form(...),
        phone: str = Form(...),  # Принимаем телефон из формы
        agree_conf: bool = Form(False),
        avatar: UploadFile = File(None),  # Принимаем файл
        db: AsyncSession = Depends(get_db)
):
    if not agree_conf:
        raise HTTPException(status_code=400, detail="Необходимо согласие с правилами")

    existing_user = await crud.get_user_by_inn(db, inn=inn)
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким ИНН уже существует")

    user_create_data = schemas.UserCreate(
        inn=inn,
        email=email,
        password=password,
        company_name=f"Компания ИНН {inn}"
    )

    new_user = await crud.create_user(db, user_data=user_create_data)

    clean_phone = "".join(filter(str.isdigit, phone))
    if clean_phone:
        try:
            new_user.phone_number = str(clean_phone) if clean_phone.isdigit() else None
        except Exception:
            pass

    # if avatar and avatar.filename:
    #     upload_dir = "app/static/users/avas"
    #     os.makedirs(upload_dir, exist_ok=True)
    #
    #     file_ext = avatar.filename.split(".")[-1]
    #     file_path = f"{upload_dir}/{new_user.id}_avatar.{file_ext}"
    #
    #     with open(file_path, "wb") as buffer:
    #         shutil.copyfileobj(avatar.file, buffer)

        # new_user.avatar_url = file_path
    await db.commit()

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": new_user.inn},
        expires_delta=access_token_expires
    )

    return {
        "status": "success",
        "user_id": new_user.id,
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/login", response_model=schemas.Token)
async def login(
        inn: str = Form(...),
        password: str = Form(...),
        db: AsyncSession = Depends(get_db)
):
    user = await crud.authenticate_user(db, inn=inn, password=password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный ИНН или пароль"
        )
    access_token = auth.create_access_token(data={"sub": user.inn})
    response = {"access_token": access_token, "token_type": "bearer"}
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # True на проде (https)
        samesite="lax"
    )
    return response

#
#
# # @router.post("/login", response_model=schemas.Token)
# # async def login_for_access_token(
# #         form_data: schemas.UserLogin,
# #         db: AsyncSession = Depends(get_db)
# # ):
# #     """Вход в систему, получение JWT токена"""
# #     user = await crud.authenticate_user(
# #         db, form_data.inn, form_data.password
# #     )
# #
# #     if not user:
# #         raise HTTPException(
# #             status_code=status.HTTP_401_UNAUTHORIZED,
# #             detail="Неправильный ИНН или пароль",
# #             headers={"WWW-Authenticate": "Bearer"},
# #         )
# #
# #     # Создаем токен
# #     access_token_expires = timedelta(
# #         minutes=auth.settings.ACCESS_TOKEN_EXPIRE_MINUTES
# #     )
# #     access_token = auth.create_access_token(
# #         data={"sub": user.inn},
# #         expires_delta=access_token_expires
# #     )
# #
# #     return {"access_token": access_token, "token_type": "bearer"}
