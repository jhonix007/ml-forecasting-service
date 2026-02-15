from app.domain.value_objects import ForecastRequest, ForecastResult

class BaselineForecastEngine:
    def forecast(self, values: list[float], horizon: int) -> list[float]:
        last = float(values[-1])
        return [last] * horizon