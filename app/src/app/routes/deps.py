from __future__ import annotations

from uuid import UUID

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.orm_models import UserORM
from app.infrastructure.db.session import get_session


def get_db() -> Session:
    # alias для совместимости со старыми роутами
    return next(get_session())


def get_current_user_dep(
    db: Session = Depends(get_session),
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> UserORM:
    """
    Минимальная auth-зависимость для MVP:
    - если передали X-User-Id => ищем пользователя по id
    - иначе берём demo@local
    """
    if x_user_id:
        user = db.scalar(select(UserORM).where(UserORM.id == x_user_id))
    else:
        user = db.scalar(select(UserORM).where(UserORM.email == "demo@local"))

    if not user:
        raise HTTPException(status_code=401, detail="User not found / unauthorized")

    return user


# чтобы predict/history могли импортировать `get_current_user`
def get_current_user(user: UserORM = Depends(get_current_user_dep)) -> UserORM:
    return user


def get_current_user_id(user: UserORM = Depends(get_current_user_dep)) -> UUID:
    return UUID(user.id)