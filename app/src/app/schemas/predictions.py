from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class TaskFeatures(BaseModel):
    series: list[float] = Field(min_length=1)
    horizon: int = Field(gt=0, le=1000)


class TaskCreateIn(BaseModel):
    model: str = Field(min_length=1, max_length=100, examples=["hf-timeseries"])
    features: TaskFeatures
    timestamp: Optional[datetime] = None


class TaskCreateOut(BaseModel):
    task_id: UUID


class TaskStatusOut(BaseModel):
    task_id: UUID
    status: str
    worker_id: Optional[str] = None
    prediction: Optional[list[float]] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None
