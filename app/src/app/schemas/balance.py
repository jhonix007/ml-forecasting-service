from pydantic import BaseModel, Field


class BalanceResponse(BaseModel):
    balance: int


class TopUpRequest(BaseModel):
    amount: int = Field(gt=0)