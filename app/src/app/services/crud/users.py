from sqlalchemy.orm import Session
from sqlalchemy import select
from app.infrastructure.db.orm_models import UserORM, WalletORM

def create_user(db: Session, email: str, password_hash: str, role: str = "USER") -> UserORM:
    user = UserORM(email=email, password_hash=password_hash, role=role)
    user.wallet = WalletORM(balance=0)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user

def get_user_by_email(db: Session, email: str) -> UserORM | None:
    return db.scalar(select(UserORM).where(UserORM.email == email))