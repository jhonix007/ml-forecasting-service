from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infrastructure.db.session import get_session
from app.infrastructure.db.orm_models import MLTaskORM
from app.schemas.predictions import TaskStatusOut

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("/{task_id}", response_model=TaskStatusOut)
def get_task(task_id: UUID, db: Session = Depends(get_session)) -> TaskStatusOut:
    task = db.get(MLTaskORM, str(task_id))
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return TaskStatusOut(
        task_id=UUID(task.task_id),
        status=task.status,
        prediction=task.prediction,
        worker_id=task.worker_id,
        error=task.error,
        created_at=task.created_at,
    )
