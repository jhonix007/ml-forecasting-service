from __future__ import annotations

from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import decode_token
from app.infrastructure.db.orm_models import UserORM
from app.infrastructure.db.session import get_session


def get_current_user_dep(
    db: Session = Depends(get_session),
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> UserORM:
    """
    Authorization: Bearer <jwt>
    В токене ожидаем payload {"sub": "<user_id>", ...}
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.split(" ", 1)[1].strip()
    try:
        payload = decode_token(token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = db.scalar(select(UserORM).where(UserORM.id == user_id))
    if not user:
        raise HTTPException(status_code=401, detail="User not found / unauthorized")

    return user


def get_current_user(user: UserORM = Depends(get_current_user_dep)) -> UserORM:
    return user


def get_current_user_id(user: UserORM = Depends(get_current_user_dep)) -> UUID:
    return UUID(user.id)