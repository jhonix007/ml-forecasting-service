from __future__ import annotations

from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from app.infrastructure.db.orm_models import PredictionORM


def create_prediction(
    db: Session,
    user_id: str,
    model_id: str,
    horizon: int,
    valid_count: int,
    credits_spent: int,
) -> PredictionORM:
    p = PredictionORM(
        user_id=user_id,
        model_id=model_id,
        horizon=horizon,
        valid_count=valid_count,
        credits_spent=credits_spent,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def get_user_predictions(db: Session, user_id: str, limit: int = 50, offset: int = 0) -> list[PredictionORM]:
    q = (
        select(PredictionORM)
        .where(PredictionORM.user_id == user_id)
        .order_by(desc(PredictionORM.created_at))
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(q).all())


def get_user_prediction_by_id(db: Session, user_id: str, prediction_id: str) -> PredictionORM | None:
    q = select(PredictionORM).where(
        PredictionORM.user_id == user_id,
        PredictionORM.id == prediction_id,
    )
    return db.scalar(q)