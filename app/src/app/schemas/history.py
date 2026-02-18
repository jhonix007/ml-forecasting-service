from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from uuid import UUID
from datetime import datetime
from datetime import datetime

from datetime import datetime

class TransactionOut(BaseModel):
    tx_type: str
    amount: int
    comment: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class TransactionItem(BaseModel):
    type: str
    amount: int
    comment: str
    created_at: datetime
    related_task_id: Optional[UUID] = None


class TransactionsHistoryResponse(BaseModel):
    items: List[TransactionItem]


class PredictionItem(BaseModel):
    task_id: UUID
    model_id: UUID
    horizon: int
    valid_count: int
    credits_spent: int
    created_at: datetime


class PredictionsHistoryResponse(BaseModel):
    items: List[PredictionItem]