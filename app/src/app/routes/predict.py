from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infrastructure.db.session import get_session
from app.infrastructure.rabbit.publisher import publish_task
from app.schemas.predictions import TaskCreateIn, TaskCreateOut
from app.services.crud.tasks import create_task, set_task_failed


router = APIRouter(prefix="/predict", tags=["predict"])


@router.post("", response_model=TaskCreateOut)
def create_prediction(payload: TaskCreateIn, db: Session = Depends(get_session)) -> TaskCreateOut:
    task_id = str(uuid4())

    msg = {
        "task_id": task_id,
        "model": payload.model,
        "features": {
            "series": payload.features.series,
            "horizon": payload.features.horizon,
        },
        "timestamp": (payload.timestamp or datetime.now(timezone.utc)).isoformat(),
    }

    # сохраняем статус задачи в БД
    create_task(db, task_id=task_id, model=payload.model)

    # публикуем в брокер сообщений
    try:
        publish_task(msg)
    except Exception as e:
        set_task_failed(db, task_id=task_id, error=str(e), worker_id="publisher")
        raise HTTPException(status_code=503, detail=f"RabbitMQ unavailable: {e}")

    return TaskCreateOut(task_id=UUID(task_id))
