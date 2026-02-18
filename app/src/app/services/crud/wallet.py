from sqlalchemy import select
from sqlalchemy.orm import Session

from app.infrastructure.db.orm_models import WalletORM, TransactionORM


class InsufficientBalanceError(Exception):
    pass


def get_wallet(db: Session, user_id: str) -> WalletORM | None:
    return db.scalar(select(WalletORM).where(WalletORM.user_id == user_id))


def top_up_wallet(db: Session, user_id: str, amount: int, comment: str = "") -> int:
    wallet = get_wallet(db, user_id)
    if not wallet:
        wallet = WalletORM(user_id=user_id, balance=0)
        db.add(wallet)
        db.flush()

    wallet.balance += amount
    db.add(TransactionORM(user_id=user_id, tx_type="TOP_UP", amount=amount, comment=comment))
    db.commit()
    return wallet.balance


def charge_wallet(db: Session, user_id: str, amount: int, comment: str = "") -> int:
    wallet = get_wallet(db, user_id)
    if not wallet:
        raise InsufficientBalanceError("Wallet not found")

    if wallet.balance < amount:
        raise InsufficientBalanceError("Not enough credits")

    wallet.balance -= amount
    db.add(TransactionORM(user_id=user_id, tx_type="CHARGE", amount=amount, comment=comment))
    db.commit()
    return wallet.balance


# --- обратная совместимость (чтобы не падали импорты в роутерах)
def top_up(db: Session, user_id: str, amount: int, comment: str = "") -> int:
    return top_up_wallet(db, user_id, amount, comment)


def charge(db: Session, user_id: str, amount: int, comment: str = "") -> int:
    return charge_wallet(db, user_id, amount, comment)
