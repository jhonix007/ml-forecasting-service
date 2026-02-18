from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field
from uuid import UUID

class PredictAsyncIn(BaseModel):
    model: str = Field(min_length=1, max_length=100)
    features: dict[str, float]

class PredictAsyncOut(BaseModel):
    task_id: UUID

class TaskStatusOut(BaseModel):
    task_id: UUID
    status: str
    model: str
    prediction: float | None = None
    worker_id: str | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime

