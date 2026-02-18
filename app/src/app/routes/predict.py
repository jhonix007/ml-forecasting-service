from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infrastructure.db.session import get_session
from app.routes.deps import get_current_user_id
from app.infrastructure.rabbit.publisher import publish_task
from app.schemas.predictions import TaskCreateIn, TaskCreateOut
from app.services.crud.tasks import create_task, set_task_failed
from app.services.crud.wallet import charge_wallet, InsufficientBalanceError


router = APIRouter(prefix="/predict", tags=["predict"])


@router.post("", response_model=TaskCreateOut)
def create_prediction(
    payload: TaskCreateIn,
    db: Session = Depends(get_session),
    user_id=Depends(get_current_user_id),
) -> TaskCreateOut:
    max_horizon = 50
    horizon = min(payload.features.horizon, max_horizon)
    task_id = str(uuid4())

    # списание за запрос (простая учебная модель)
    try:
        charge_wallet(db, str(user_id), amount=1, comment="predict request")
    except InsufficientBalanceError as e:
        raise HTTPException(status_code=402, detail=str(e))

    msg = {
        "task_id": task_id,
        "model": payload.model,
        "features": {
            "series": payload.features.series,
            "horizon": horizon,
        },
        "timestamp": (payload.timestamp or datetime.now(timezone.utc)).isoformat(),
    }

    # сохраняем статус задачи в БД
    create_task(db, task_id=task_id, model=payload.model, user_id=str(user_id))

    # публикуем в брокер сообщений
    try:
        publish_task(msg)
    except Exception as e:
        set_task_failed(db, task_id=task_id, error=str(e), worker_id="publisher")
        raise HTTPException(status_code=503, detail=f"RabbitMQ unavailable: {e}")

    return TaskCreateOut(task_id=UUID(task_id))
