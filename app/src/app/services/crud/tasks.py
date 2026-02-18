from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select, desc

from app.infrastructure.db.orm_models import MLTaskORM

def create_task(db: Session, task_id: str, model: str, user_id: str | None = None) -> MLTaskORM:
    task = MLTaskORM(
        task_id=task_id,
        user_id=user_id,
        model=model,
        status="PENDING",
        created_at=datetime.now(timezone.utc),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def set_task_success(db: Session, task_id: str, prediction, worker_id: str) -> None:
    task = db.scalar(select(MLTaskORM).where(MLTaskORM.task_id == task_id))
    if not task:
        return
    task.status = "SUCCESS"
    task.prediction = prediction
    task.worker_id = worker_id
    task.error = None
    db.commit()

def set_task_failed(db: Session, task_id: str, error: str, worker_id: str) -> None:
    task = db.scalar(select(MLTaskORM).where(MLTaskORM.task_id == task_id))
    if not task:
        return
    task.status = "FAILED"
    task.worker_id = worker_id
    task.error = error[:500]
    db.commit()

def get_task(db: Session, task_id: str) -> MLTaskORM | None:
    return db.scalar(select(MLTaskORM).where(MLTaskORM.task_id == task_id))

def get_tasks_for_user(db: Session, user_id: str, limit: int = 50) -> list[MLTaskORM]:
    q = (
        select(MLTaskORM)
        .where(MLTaskORM.user_id == user_id)
        .order_by(desc(MLTaskORM.created_at))
        .limit(limit)
    )
    return list(db.scalars(q).all())
