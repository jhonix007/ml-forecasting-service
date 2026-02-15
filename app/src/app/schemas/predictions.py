from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PredictionMetaOut(BaseModel):
    id: UUID
    user_id: UUID
    model_id: UUID
    horizon: int = Field(gt=0, le=1000)
    valid_count: int
    credits_spent: int
    created_at: datetime

    class Config:
        from_attributes = True