from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class PredictIn(BaseModel):
    model_id: UUID
    horizon: int = Field(gt=0, le=1000)
    values: list[Any] = Field(min_length=1)


class InvalidRowSchema(BaseModel):
    index: int
    raw_value: Any
    error: str


class PredictOut(BaseModel):
    task_id: UUID
    model_id: UUID
    horizon: int
    valid_count: int
    invalid_rows: list[InvalidRowSchema]
    forecast: list[float]
    credits_spent: int


PredictRequest = PredictIn
PredictResponse = PredictOut