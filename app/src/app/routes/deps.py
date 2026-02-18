from __future__ import annotations

# Совместимость: роутеры продолжают импортировать зависимости отсюда,
# а реализация перенесена в app.auth.authenticate.
from app.auth.authenticate import (  # noqa: F401
    get_current_user,
    get_current_user_dep,
    get_current_user_id,
)

__all__ = [
    "get_current_user",
    "get_current_user_dep",
    "get_current_user_id",
]
