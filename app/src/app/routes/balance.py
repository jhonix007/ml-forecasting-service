from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.infrastructure.db.session import get_session
from app.routes.deps import get_current_user_id
from app.schemas.balance import BalanceResponse, TopUpRequest
from app.services.crud.wallet import get_wallet, top_up_wallet

router = APIRouter(prefix="/balance", tags=["balance"])


@router.get("", response_model=BalanceResponse)
def get_balance(
    user_id: UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
) -> BalanceResponse:
    wallet = get_wallet(session, str(user_id))
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    return BalanceResponse(balance=wallet.balance)


@router.post("/top-up", response_model=BalanceResponse)
def top_up(
    payload: TopUpRequest,
    user_id: UUID = Depends(get_current_user_id),
    session: Session = Depends(get_session),
) -> BalanceResponse:
    new_balance = top_up_wallet(session, str(user_id), payload.amount, comment="api top up")
    return BalanceResponse(balance=new_balance)