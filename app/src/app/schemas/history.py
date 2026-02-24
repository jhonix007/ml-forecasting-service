from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class TransactionOut(BaseModel):
    tx_type: str
    amount: int
    comment: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskHistoryOut(BaseModel):
    task_id: UUID
    model: str
    status: str
    worker_id: Optional[str] = None
    prediction: Optional[list[float] | dict] = None
    error: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
