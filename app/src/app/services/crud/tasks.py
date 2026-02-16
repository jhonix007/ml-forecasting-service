from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.infrastructure.db.orm_models import MLTaskORM

def create_task(db: Session, task_id: str, user_id: str, model: str, features: dict) -> MLTaskORM:
    task = MLTaskORM(
        id=task_id,
        user_id=user_id,
        model=model,
        features=features,
        status="PENDING",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

def set_task_success(db: Session, task_id: str, prediction: float, worker_id: str) -> None:
    task = db.scalar(select(MLTaskORM).where(MLTaskORM.id == task_id))
    if not task:
        return
    task.status = "SUCCESS"
    task.prediction = float(prediction)
    task.worker_id = worker_id
    task.error = None
    task.updated_at = datetime.now(timezone.utc)
    db.commit()

def set_task_failed(db: Session, task_id: str, error: str, worker_id: str) -> None:
    task = db.scalar(select(MLTaskORM).where(MLTaskORM.id == task_id))
    if not task:
        return
    task.status = "FAILED"
    task.worker_id = worker_id
    task.error = error[:500]
    task.updated_at = datetime.now(timezone.utc)
    db.commit()

def get_task_for_user(db: Session, task_id: str, user_id: str) -> MLTaskORM | None:
    return db.scalar(select(MLTaskORM).where(MLTaskORM.id == task_id, MLTaskORM.user_id == user_id))