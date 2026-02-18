from enum import Enum

class Role(Enum):
    USER = "USER"
    ADMIN = "ADMIN"

class TransactionType(Enum):
    TOP_UP = "TOP_UP"
    CHARGE = "CHARGE"

class TaskStatus(Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"

class ModelKind(Enum):
    TIMESERIES_FORECASTING = "TIMESERIES_FORECASTING"