from __future__ import annotations

import logging
import inspect
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infrastructure.db.session import get_session
from app.infrastructure.db.orm_models import PredictionORM, WalletORM
from app.routes.deps import get_current_user
from app.schemas.predict import PredictIn, PredictOut, InvalidRowSchema
from app.services.crud.wallet import charge, InsufficientBalanceError
from app.ml.validators import BasicNumericValidator
from app.ml.engines import BaselineForecastEngine

router = APIRouter(prefix="/predict", tags=["predict"])
logger = logging.getLogger(__name__)

COST_PER_REQUEST = 50  # учебная стоимость


def _refund(db: Session, user_id: str, amount: int) -> None:
    """Простой возврат средств, если после списания что-то упало."""
    wallet = db.query(WalletORM).filter(WalletORM.user_id == user_id).one_or_none()
    if wallet:
        wallet.balance += amount
        db.commit()

def _call_forecast(engine: BaselineForecastEngine, values: list[float], horizon: int) -> list[float]:
    """
    У твоего BaselineForecastEngine.forecast() horizon обязателен (см. лог),
    поэтому сначала всегда пробуем (values, horizon).
    """
    try:
        forecast = engine.forecast(values, horizon)  # основной путь
    except TypeError:
        # fallback на случай другой сигнатуры
        forecast = engine.forecast(values)

    forecast = list(forecast)
    if len(forecast) >= horizon:
        return forecast[:horizon]
    if len(forecast) == 0:
        return [0.0] * horizon
    last = float(forecast[-1])
    return forecast + [last] * (horizon - len(forecast))


@router.post("", response_model=PredictOut)
def predict(payload: PredictIn, db: Session = Depends(get_session), user=Depends(get_current_user)):
    # 1) валидация ряда
    validator = BasicNumericValidator()
    validated = validator.validate_series(payload.values)

    if len(validated.values) == 0:
        raise HTTPException(status_code=400, detail="No valid numeric values provided")

    # 2) списание
    try:
        charge(db, user_id=str(user.id), amount=COST_PER_REQUEST, comment="predict request")
    except InsufficientBalanceError:
        raise HTTPException(status_code=402, detail="Insufficient balance")

    task_id = uuid4()

    try:
        # 3) прогноз
        engine = BaselineForecastEngine()
        forecast = _call_forecast(engine, validated.values, payload.horizon)

        # 4) запись в БД (ТОЛЬКО те поля, которые реально есть в таблице!)
        pred = PredictionORM(
            id=str(task_id),
            user_id=str(user.id),
            model_id=str(payload.model_id),
            horizon=int(payload.horizon),
            valid_count=int(len(validated.values)),
            credits_spent=int(COST_PER_REQUEST),
            created_at=datetime.now(timezone.utc),
        )
        db.add(pred)
        db.commit()

        # 5) ответ клиенту
        return PredictOut(
            task_id=task_id,
            model_id=payload.model_id,
            horizon=payload.horizon,
            valid_count=len(validated.values),
            invalid_rows=[
                InvalidRowSchema(index=r.index, raw_value=r.raw_value, error=r.error)
                for r in validated.invalid_rows
            ],
            forecast=forecast,
            credits_spent=COST_PER_REQUEST,
        )

    except Exception as e:
        # если что-то упало после списания — вернём деньги
        logger.exception("Predict failed: %s", e)
        _refund(db, user_id=str(user.id), amount=COST_PER_REQUEST)
        raise HTTPException(status_code=500, detail="Prediction failed")