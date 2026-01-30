# from typing import Annotated # Рекомендуется в современных версиях
# from fastapi import Depends, HTTPException, status
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from sqlalchemy.ext.asyncio import AsyncSession
#
# from app.auth import verify_token
# from app.database import get_db
# from app import crud
# from app.models import User # Импорт модели БД
#
# security = HTTPBearer(auto_error=True)
#
# async def get_current_user(
#     credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
#     db: Annotated[AsyncSession, Depends(get_db)]
# ) -> User:
#
#     token_data = await verify_token(credentials.credentials)
#
#     user = await crud.get_user_by_inn(db, inn=token_data.inn)
#
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_401_UNAUTHORIZED,
#             detail="Пользователь не найден"
#         )
#
#     if not user.is_active:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Аккаунт деактивирован"
#         )
#
#     return user
#
# class RoleChecker:
#     def __init__(self, allowed_roles: list[str]):
#         self.allowed_roles = allowed_roles
#
#     def __call__(self, user: Annotated[User, Depends(get_current_user)]):
#         if user.role not in self.allowed_roles:
#             raise HTTPException(
#                 status_code=status.HTTP_403_FORBIDDEN,
#                 detail=f"Доступ запрещен. Требуемые роли: {self.allowed_roles}"
#             )
#         return user