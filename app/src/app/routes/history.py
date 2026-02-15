from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.db.session import get_session
from app.routes.deps import get_current_user
from app.schemas.history import TransactionOut
from app.services.crud.transactions import get_user_transactions

router = APIRouter(prefix="/history", tags=["history"])


@router.get("/transactions", response_model=list[TransactionOut])
def transactions(
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    txs = get_user_transactions(db, user_id=str(user.id), limit=50)
    return [
        TransactionOut(
            tx_type=t.tx_type,
            amount=t.amount,
            comment=t.comment,
            created_at=t.created_at,
        )
        for t in txs
    ]