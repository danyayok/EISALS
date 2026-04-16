from fastapi import Cookie, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import crud
from app.core.database import get_db
from app.models.models import User
from app.services.auth import verify_token

security = HTTPBearer(auto_error=False)


async def get_token_from_request(
        credentials: HTTPAuthorizationCredentials | None = Depends(security),
        access_token: str | None = Cookie(default=None),
) -> str:
    if credentials and credentials.credentials:
        return credentials.credentials

    if access_token:
        return access_token

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Требуется авторизация",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def get_current_user(
        token: str = Depends(get_token_from_request),
        db: AsyncSession = Depends(get_db),
) -> User:
    token_data = await verify_token(token)
    user = await crud.get_user_by_inn(db, inn=token_data.inn)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Пользователь не найден")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Аккаунт деактивирован")

    return user


class RoleChecker:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: User = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Доступ запрещен. Требуемые роли: {self.allowed_roles}",
            )
        return user
