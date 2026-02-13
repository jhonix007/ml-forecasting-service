from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from app.infrastructure.db.orm_models import TransactionORM

def get_user_transactions(db: Session, user_id: str, limit: int = 50) -> list[TransactionORM]:
    q = select(TransactionORM).where(TransactionORM.user_id == user_id).order_by(desc(TransactionORM.created_at)).limit(limit)
    return list(db.scalars(q).all())