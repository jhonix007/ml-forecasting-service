from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.infrastructure.db.session import get_session
from app.routes.deps import get_current_user
from app.schemas.history import TransactionOut, TaskHistoryOut
from app.services.crud.transactions import get_user_transactions
from app.services.crud.tasks import get_tasks_for_user

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


@router.get("/predictions", response_model=list[TaskHistoryOut])
def predictions(
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    tasks = get_tasks_for_user(db, user_id=str(user.id), limit=50)
    return [
        TaskHistoryOut(
            task_id=t.task_id,
            model=t.model,
            status=t.status,
            prediction=t.prediction,
            worker_id=t.worker_id,
            error=t.error,
            created_at=t.created_at,
        )
        for t in tasks
    ]
