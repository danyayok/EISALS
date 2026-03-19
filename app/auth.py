from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

import jwt
from bcrypt import checkpw, gensalt, hashpw
from fastapi import HTTPException, status
from pydantic import ValidationError

from app.config import settings
from app.schemas import TokenData


def get_password_hash(password: str) -> str:
    return hashpw(password.encode("utf-8"), gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

    to_encode = data.copy()
    to_encode.update(
        {
            "exp": expire,
            "iat": now,
            "nbf": now,
            "jti": str(uuid4()),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "type": "access",
        }
    )

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


async def verify_token(token: str) -> TokenData:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Не удалось подтвердить учетные данные",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            issuer=settings.JWT_ISSUER,
        )
        if payload.get("type") != "access":
            raise credentials_exception

        inn: str | None = payload.get("sub")
        if inn is None:
            raise credentials_exception

        return TokenData(inn=inn)
    except (jwt.PyJWTError, ValidationError):
        raise credentials_exception
