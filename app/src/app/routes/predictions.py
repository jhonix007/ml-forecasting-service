from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infrastructure.db.session import get_session
from app.routes.deps import get_current_user
from app.schemas.predictions import PredictionMetaOut
from app.services.crud.predictions import get_user_predictions, get_user_prediction_by_id

router = APIRouter(prefix="/predictions", tags=["predictions"])


@router.get("", response_model=list[PredictionMetaOut])
def list_predictions(
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
    limit: int = 50,
    offset: int = 0,
):
    return get_user_predictions(db, user_id=str(user.id), limit=limit, offset=offset)


@router.get("/{prediction_id}", response_model=PredictionMetaOut)
def get_prediction(
    prediction_id: UUID,
    db: Session = Depends(get_session),
    user=Depends(get_current_user),
):
    p = get_user_prediction_by_id(db, user_id=str(user.id), prediction_id=str(prediction_id))
    if not p:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return p