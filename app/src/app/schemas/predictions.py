from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, Field


TaskStatus = Literal["PENDING", "SUCCESS", "FAILED"]


class PredictTaskIn(BaseModel):
    model: str = Field(..., examples=["demo_model"])
    features: dict[str, Any] = Field(..., examples=[{"x1": 1.2, "x2": 5.7}])


class PredictTaskOut(BaseModel):
    task_id: UUID


class TaskStatusOut(BaseModel):
    task_id: UUID
    status: TaskStatus
    prediction: Optional[float] = None
    worker_id: Optional[str] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
