from app.domain.value_objects import ForecastRequest, ForecastResult

class BaselineForecastEngine:
    """Простой baseline: повторяем последнее значение horizon раз."""

    def forecast(self, req: ForecastRequest) -> ForecastResult:
        last = req.values[-1]
        return ForecastResult(forecast=[last] * req.horizon)