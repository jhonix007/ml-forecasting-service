from __future__ import annotations

from sqlalchemy.orm import Session
from sqlalchemy import select

from app.auth.hash_password import hash_password
from app.infrastructure.db.orm_models import UserORM, WalletORM


def create_user(db: Session, email: str, password: str, role: str = "USER") -> UserORM:
    # хэшируем пароль при сохранении (замечание №5)
    user = UserORM(email=email, password_hash=hash_password(password), role=role)
    user.wallet = WalletORM(balance=0)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_email(db: Session, email: str) -> UserORM | None:
    return db.scalar(select(UserORM).where(UserORM.email == email))


def get_user_by_id(db: Session, user_id: str) -> UserORM | None:
    return db.scalar(select(UserORM).where(UserORM.id == user_id))
