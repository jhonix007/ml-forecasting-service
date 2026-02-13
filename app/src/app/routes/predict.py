from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infrastructure.db.session import get_db
from app.routes.deps import get_current_user
from app.schemas.predict import PredictIn, PredictOut
from app.services.crud.wallet import charge, InsufficientBalanceError
from app.ml.validators import BasicNumericValidator
from app.ml.engines import BaselineForecastEngine

router = APIRouter(prefix="/predict", tags=["predict"])

COST_PER_REQUEST = 50  # для учебки


@router.post("", response_model=PredictOut)
def predict(payload: PredictIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    # 1) Валидация ряда
    validator = BasicNumericValidator()
    validated = validator.validate_series(payload.values)

    if len(validated.values) == 0:
        raise HTTPException(status_code=400, detail="No valid numeric values provided")

    # 2) Проверка баланса + списание
    try:
        charge(db, user_id=str(user.id), amount=COST_PER_REQUEST, comment="predict request")
    except InsufficientBalanceError:
        raise HTTPException(status_code=402, detail="Insufficient balance")

    # 3) Прогноз (пока baseline)
    engine = BaselineForecastEngine()
    forecast = engine.forecast(validated.values, payload.horizon)  # если у тебя другая сигнатура — поправь

    return PredictOut(
        forecast=forecast,
        valid_count=len(validated.values),
        invalid_rows=[{"index": r.index, "raw_value": r.raw_value, "error": r.error} for r in validated.invalid_rows],
        credits_spent=COST_PER_REQUEST,
    )