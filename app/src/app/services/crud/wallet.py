from sqlalchemy.orm import Session
from sqlalchemy import select
from app.infrastructure.db.orm_models import WalletORM, TransactionORM

class InsufficientBalanceError(Exception):
    pass

def top_up(db: Session, user_id: str, amount: int, comment: str = "") -> int:
    wallet = db.scalar(select(WalletORM).where(WalletORM.user_id == user_id))
    wallet.balance += amount
    db.add(TransactionORM(user_id=user_id, tx_type="TOP_UP", amount=amount, comment=comment))
    db.commit()
    return wallet.balance

def charge(db: Session, user_id: str, amount: int, comment: str = "") -> int:
    wallet = db.scalar(select(WalletORM).where(WalletORM.user_id == user_id))
    if wallet.balance < amount:
        raise InsufficientBalanceError("Not enough credits")
    wallet.balance -= amount
    db.add(TransactionORM(user_id=user_id, tx_type="CHARGE", amount=amount, comment=comment))
    db.commit()
    return wallet.balance