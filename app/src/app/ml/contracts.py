from typing import Protocol, List, Any
from app.domain.value_objects import ValidatedSeries, ForecastRequest, ForecastResult

class IDataValidator(Protocol):
    def validate_series(self, raw_values: List[Any]) -> ValidatedSeries:
        ...

class IForecastingEngine(Protocol):
    def forecast(self, req: ForecastRequest) -> ForecastResult:
        ...