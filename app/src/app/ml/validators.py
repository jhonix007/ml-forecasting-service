from typing import List, Any
from app.domain.value_objects import ValidatedSeries, InvalidRow

class BasicNumericValidator:
    """Базовая валидация: float + запрет NaN/Inf."""

    def validate_series(self, raw_values: List[Any]) -> ValidatedSeries:
        values: List[float] = []
        invalid: List[InvalidRow] = []

        for i, v in enumerate(raw_values):
            try:
                fv = float(v)
                if fv != fv or fv in (float("inf"), float("-inf")):
                    raise ValueError("NaN/Inf not allowed")
                values.append(fv)
            except Exception as e:
                invalid.append(InvalidRow(index=i, raw_value=v, error=str(e)))

        return ValidatedSeries(values=values, invalid_rows=invalid)