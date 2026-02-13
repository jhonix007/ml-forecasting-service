from dataclasses import dataclass
from typing import Any, List
from uuid import UUID

@dataclass(frozen=True)
class Credits:
    """Баланс пользователя в условных кредитах."""
    value: int
    def __post_init__(self) -> None:
        if self.value < 0:
            raise ValueError("Credits.value must be >= 0")

@dataclass(frozen=True)
class CreditsCost:
    """Стоимость операции (списание)."""
    value: int
    def __post_init__(self) -> None:
        if self.value <= 0:
            raise ValueError("CreditsCost.value must be > 0")

@dataclass(frozen=True)
class InvalidRow:
    """Описание некорректного значения во входных данных."""
    index: int
    raw_value: Any
    error: str

@dataclass(frozen=True)
class ValidatedSeries:
    """Валидные значения + ошибки, которые вернём пользователю."""
    values: List[float]
    invalid_rows: List[InvalidRow]

@dataclass(frozen=True)
class ForecastRequest:
    """Запрос к движку прогнозирования."""
    model_id: UUID
    horizon: int
    values: List[float]

@dataclass(frozen=True)
class ForecastResult:
    """Результат прогноза."""
    forecast: List[float]
