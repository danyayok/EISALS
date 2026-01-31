from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import HTMLResponse
from fastapi.requests import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas, auth
from app.templates import templates

# from app.database import get_db
# from app.dependencies import get_current_user

router = APIRouter(tags=["Auth Pages"])






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
#
#
# @router.get("/register", response_class=HTMLResponse)
# async def register_page(request: Request):
#     """Страница регистрации"""
#     return """
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <title>Регистрация</title>
#         <script src="https://cdn.tailwindcss.com"></script>
#     </head>
#     <body class="bg-gray-100 min-h-screen flex items
#     """